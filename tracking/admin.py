from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Checkout, Laptop, Student


@admin.register(Student)
class StudentAdmin(UserAdmin):
    list_display = ('admission_number', 'full_name', 'email',
                    'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')
    search_fields = ('admission_number', 'full_name', 'email', 'username')
    ordering = ('admission_number',)

    # Extend Django's built-in user fieldsets with our custom fields
    fieldsets = UserAdmin.fieldsets + (
        ('Office info', {'fields': ('admission_number', 'full_name')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Office info', {'fields': ('admission_number', 'full_name', 'email')}),
    )


@admin.register(Laptop)
class LaptopAdmin(admin.ModelAdmin):
    list_display = ('name', 'model_number', 'owner', 'slot_label', 'status')
    list_filter = ('owner',)
    search_fields = ('name', 'model_number', 'serial_number',
                     'owner__admission_number', 'owner__full_name')
    autocomplete_fields = ('owner',)

    @admin.display(description="Status")
    def status(self, obj):
        a = obj.active_checkout
        if a is None:
            return "In storage"
        return "Overdue" if a.is_overdue else "Checked out"


@admin.register(Checkout)
class CheckoutAdmin(admin.ModelAdmin):
    list_display = ('laptop', 'student', 'checked_out_at',
                    'expected_return_at', 'returned_at', 'overdue_flag')
    list_filter = ('returned_at',)
    search_fields = ('laptop__name', 'laptop__model_number',
                     'student__admission_number', 'student__full_name')
    readonly_fields = ('checked_out_at', 'returned_at')

    @admin.display(boolean=True, description="Overdue?")
    def overdue_flag(self, obj):
        return obj.is_overdue