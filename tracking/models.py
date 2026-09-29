from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Student(AbstractUser):
    """
    Custom user model. `username` and `admission_number` will hold the
    same value; we keep both because Django's auth needs `username`.
    """
    admission_number = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique admission number, e.g. ADM-2024-001",
    )
    full_name = models.CharField(max_length=120, blank=True)

    REQUIRED_FIELDS = ['admission_number', 'email']

    def __str__(self):
        return self.full_name or self.admission_number


class Laptop(models.Model):
    """A student's personal laptop, stored under office care."""
    owner = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name='laptops',
        help_text="The student who owns this laptop",
    )
    name = models.CharField(max_length=100, help_text="e.g. HP Pavilion 15")
    model_number = models.CharField(
        max_length=50, help_text="e.g. HP-PAV-15-001"
    )
    serial_number = models.CharField(
        max_length=50, unique=True, blank=True, null=True
    )
    slot_label = models.CharField(
        max_length=20, blank=True,
        help_text="Leave blank to auto-fill with owner's admission number.",
    )

    class Meta:
        ordering = ['slot_label', 'name']

    # ---- helpers ----

    @property
    def active_checkout(self):
        return self.checkouts.filter(returned_at__isnull=True).first()

    @property
    def is_available(self):
        return self.active_checkout is None

    def save(self, *args, **kwargs):
        if not self.slot_label and self.owner_id:
            self.slot_label = self.owner.admission_number
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.model_number}) — {self.owner.admission_number}"


class Checkout(models.Model):
    """One borrow event: student takes their own laptop out of storage."""
    laptop = models.ForeignKey(
        Laptop, on_delete=models.CASCADE, related_name='checkouts'
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name='checkouts'
    )
    checked_out_at = models.DateTimeField(default=timezone.now)
    expected_return_at = models.DateTimeField()
    returned_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-checked_out_at']

    # ---- status helpers used everywhere ----

    @property
    def is_active(self):
        return self.returned_at is None

    @property
    def is_overdue(self):
        return self.is_active and timezone.now() > self.expected_return_at

    @property
    def minutes_overdue(self):
        if not self.is_overdue:
            return 0
        delta = timezone.now() - self.expected_return_at
        return int(delta.total_seconds() // 60)

    @property
    def hours_out(self):
        end = self.returned_at or timezone.now()
        return round((end - self.checked_out_at).total_seconds() / 3600, 1)

    def __str__(self):
        if self.returned_at:
            state = "returned"
        elif self.is_overdue:
            state = "OVERDUE"
        else:
            state = "OUT"
        return f"{self.laptop.name} → {self.student.admission_number} ({state})"