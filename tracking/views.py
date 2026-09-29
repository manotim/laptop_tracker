from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from .forms import CheckoutForm, StudentLoginForm
from .models import Checkout, Laptop


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