"""
Make sure the staff login from the Render environment variables works.

Uses DJANGO_SUPERUSER_USERNAME / _EMAIL / _PASSWORD.
- If the user doesn't exist, it is created.
- If it already exists (for example from a database pushed to GitHub),
  its password is reset to DJANGO_SUPERUSER_PASSWORD.
"""
import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Create or update the staff login from environment variables."

    def handle(self, *args, **options):
        username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "").strip()
        password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "")
        email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "")
        if not username or not password:
            self.stdout.write("No DJANGO_SUPERUSER_USERNAME/PASSWORD set, skipping.")
            return

        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        if email:
            user.email = email
        user.set_password(password)
        user.save()
        self.stdout.write(f"Staff login '{username}' {'created' if created else 'updated'}.")
