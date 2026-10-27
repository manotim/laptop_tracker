import os
from django.core.management.base import BaseCommand
from tracking.models import Student

class Command(BaseCommand):
    help = 'Creates a superuser from environment variables'

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        admission_number = os.environ.get('DJANGO_SUPERUSER_ADMISSION_NUMBER', username)

        if not (username and email and password):
            self.stdout.write(self.style.WARNING('Skipping superuser creation: missing env vars'))
            return

        if Student.objects.filter(username=username).exists():
            self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" already exists'))
            return

        Student.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            admission_number=admission_number
        )
        self.stdout.write(self.style.SUCCESS(f'Superuser "{username}" created successfully'))