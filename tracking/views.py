from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import CheckoutForm, LaptopForm, StudentCreateForm, StudentLoginForm
from .models import Checkout, Laptop, Student


# ------------------------------------------------------------------ auth

class StudentLoginView(LoginView):
    form_class = StudentLoginForm
    template_name = 'tracking/login.html'
    redirect_authenticated_user = True


def logout_view(request):
    logout(request)
    return redirect('login')


# ------------------------------------------------------------------ student

@login_required
def dashboard(request):
    """Student home page — their laptops and current state."""
    laptops = Laptop.objects.filter(owner=request.user)

    cards = []
    for laptop in laptops:
        active = laptop.active_checkout
        cards.append({
            'laptop': laptop,
            'active': active,
            'is_available': active is None,
            'is_overdue': active.is_overdue if active else False,
        })

    has_overdue = any(c['is_overdue'] for c in cards)

    history = (
        Checkout.objects
        .filter(student=request.user, returned_at__isnull=False)
        .select_related('laptop')[:15]
    )

    return render(request, 'tracking/dashboard.html', {
        'cards': cards,
        'has_overdue': has_overdue,
        'history': history,
    })


@login_required
def checkout_laptop(request, laptop_id):
    """Check out one of MY laptops for a chosen session length."""
    # Ownership is enforced right here:
    laptop = get_object_or_404(Laptop, id=laptop_id, owner=request.user)

    # One active checkout per student — as requested.
    if Checkout.objects.filter(student=request.user, returned_at__isnull=True).exists():
        messages.error(
            request,
            "You already have a laptop checked out. Return it first."
        )
        return redirect('dashboard')

    if not laptop.is_available:
        messages.error(request, f"{laptop.name} is not currently available.")
        return redirect('dashboard')

    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            hours = int(form.cleaned_data['duration_hours'])
            now = timezone.now()
            expected = now + timedelta(hours=hours)

            Checkout.objects.create(
                laptop=laptop,
                student=request.user,
                checked_out_at=now,
                expected_return_at=expected,
                notes=form.cleaned_data.get('notes', ''),
            )
            messages.success(
                request,
                f"{laptop.name} checked out. Please return by "
                f"{expected.strftime('%H:%M')}."
            )
            return redirect('dashboard')
    else:
        form = CheckoutForm()

    return render(request, 'tracking/checkout.html', {
        'form': form,
        'laptop': laptop,
    })


@login_required
def return_laptop(request, checkout_id):
    """Return my own checked-out laptop."""
    checkout = get_object_or_404(
        Checkout,
        id=checkout_id,
        student=request.user,
        returned_at__isnull=True,
    )

    if request.method == 'POST':
        checkout.returned_at = timezone.now()
        checkout.save(update_fields=['returned_at'])
        messages.success(request, f"{checkout.laptop.name} returned. Thank you!")
        return redirect('dashboard')

    return render(request, 'tracking/return_confirm.html', {'checkout': checkout})


# ------------------------------------------------------------------ staff

@login_required
def staff_dashboard(request):
    """Staff-only overview: everything, plus overdue alerts."""
    if not request.user.is_staff:
        messages.error(request, "You don't have access to that page.")
        return redirect('dashboard')

    now = timezone.now()

    overdue = (
        Checkout.objects
        .filter(returned_at__isnull=True, expected_return_at__lt=now)
        .select_related('laptop', 'student')
        .order_by('expected_return_at')
    )

    active = (
        Checkout.objects
        .filter(returned_at__isnull=True, expected_return_at__gte=now)
        .select_related('laptop', 'student')
        .order_by('expected_return_at')
    )

    laptop_rows = []
    for laptop in Laptop.objects.select_related('owner'):
        a = laptop.active_checkout
        laptop_rows.append({
            'laptop': laptop,
            'is_available': a is None,
            'is_overdue': a.is_overdue if a else False,
        })

    return render(request, 'tracking/staff_dashboard.html', {
        'overdue': overdue,
        'active': active,
        'laptop_rows': laptop_rows,
    })


# ---------------------------------------------------------------- staff: decorator

staff_required = user_passes_test(
    lambda u: u.is_authenticated and u.is_staff,
    login_url='login',
)


# ---------------------------------------------------------------- staff: laptops

@staff_required
def staff_laptops_list(request):
    q = request.GET.get('q', '').strip()
    qs = Laptop.objects.select_related('owner').order_by('slot_label', 'name')
    if q:
        qs = qs.filter(
            Q(name__icontains=q)
            | Q(model_number__icontains=q)
            | Q(slot_label__icontains=q)
            | Q(owner__admission_number__icontains=q)
            | Q(owner__full_name__icontains=q)
        )

    rows = []
    for laptop in qs:
        active = laptop.active_checkout
        rows.append({
            'laptop': laptop,
            'active': active,
            'is_available': active is None,
            'is_overdue': active.is_overdue if active else False,
        })

    return render(request, 'tracking/staff_laptops.html', {
        'rows': rows,
        'query': q,
        'duration_choices': settings.SESSION_DURATION_CHOICES[:6],
    })


@staff_required
def staff_laptop_form(request, laptop_id=None):
    laptop = get_object_or_404(Laptop, id=laptop_id) if laptop_id else None
    if request.method == 'POST':
        form = LaptopForm(request.POST, instance=laptop)
        if form.is_valid():
            obj = form.save()
            messages.success(request, f"Laptop {obj.name} saved.")
            return redirect('staff_laptop_detail', laptop_id=obj.id)
    else:
        form = LaptopForm(instance=laptop)

    return render(request, 'tracking/staff_laptop_form.html', {
        'form': form,
        'laptop': laptop,
    })


@staff_required
def staff_laptop_detail(request, laptop_id):
    laptop = get_object_or_404(Laptop.objects.select_related('owner'), id=laptop_id)
    active = laptop.active_checkout
    history = laptop.checkouts.select_related('student').order_by('-checked_out_at')[:20]

    if request.method == 'POST' and not active:
        hours = int(request.POST.get('duration_hours', 3))
        now = timezone.now()
        Checkout.objects.create(
            laptop=laptop,
            student=laptop.owner,
            checked_out_at=now,
            expected_return_at=now + timedelta(hours=hours),
        )
        messages.success(request, f"{laptop.name} checked out for {hours}h.")
        return redirect('staff_laptop_detail', laptop_id=laptop.id)

    return render(request, 'tracking/staff_laptop_detail.html', {
        'laptop': laptop,
        'active': active,
        'history': history,
        'duration_choices': settings.SESSION_DURATION_CHOICES,
    })


@staff_required
@require_POST
def staff_laptop_checkout(request, laptop_id):
    laptop = get_object_or_404(Laptop, id=laptop_id)
    back = request.META.get('HTTP_REFERER') or '/staff/laptops/'
    if not laptop.is_available:
        messages.error(request, f"{laptop.name} is already checked out.")
        return redirect(back)
    hours = int(request.POST.get('duration_hours', 3))
    now = timezone.now()
    Checkout.objects.create(
        laptop=laptop,
        student=laptop.owner,
        checked_out_at=now,
        expected_return_at=now + timedelta(hours=hours),
    )
    messages.success(
        request,
        f"{laptop.name} checked out to {laptop.owner.admission_number} for {hours}h."
    )
    return redirect(back)


@staff_required
@require_POST
def staff_laptop_return(request, laptop_id):
    laptop = get_object_or_404(Laptop, id=laptop_id)
    back = request.META.get('HTTP_REFERER') or '/staff/laptops/'
    active = laptop.active_checkout
    if not active:
        messages.error(request, f"{laptop.name} is not checked out.")
        return redirect(back)
    active.returned_at = timezone.now()
    active.save(update_fields=['returned_at'])
    messages.success(request, f"{laptop.name} returned.")
    return redirect(back)


# ---------------------------------------------------------------- staff: students

@staff_required
def staff_students_list(request):
    q = request.GET.get('q', '').strip()
    qs = Student.objects.all().order_by('admission_number')
    if q:
        qs = qs.filter(
            Q(admission_number__icontains=q)
            | Q(full_name__icontains=q)
            | Q(email__icontains=q)
        )

    rows = []
    for s in qs:
        rows.append({
            'student': s,
            'laptop_count': s.laptops.count(),
            'out_count': s.checkouts.filter(returned_at__isnull=True).count(),
        })

    return render(request, 'tracking/staff_students.html', {
        'rows': rows,
        'query': q,
    })


@staff_required
def staff_student_form(request, student_id=None):
    student = get_object_or_404(Student, id=student_id) if student_id else None

    if student:
        # Simple edit — no password change here. Use admin for password resets.
        if request.method == 'POST':
            student.admission_number = request.POST.get('admission_number', student.admission_number)
            student.full_name = request.POST.get('full_name', student.full_name)
            student.email = request.POST.get('email', student.email)
            student.save()
            messages.success(request, f"Student {student.admission_number} updated.")
            return redirect('staff_students')
        return render(request, 'tracking/staff_student_form.html', {'student': student})

    if request.method == 'POST':
        form = StudentCreateForm(request.POST)
        if form.is_valid():
            s = form.save()
            messages.success(request, f"Student {s.admission_number} created.")
            return redirect('staff_students')
    else:
        form = StudentCreateForm()

    return render(request, 'tracking/staff_student_form.html', {'form': form, 'student': None})