import os
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Creates or updates an admin user'

    def handle(self, *args, **options):
        admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
        admin_password = os.getenv('ADMIN_PASSWORD')
        if not admin_password:
            self.stdout.write(self.style.WARNING("ADMIN_PASSWORD not set; skipping admin creation."))
            return
        
        # Look up by email (the login field) so the command is safe to re-run
        user = User.objects.filter(email=admin_email).first()
        if user:
            self.stdout.write(self.style.WARNING("Admin user already exists. Updating..."))
        else:
            self.stdout.write(self.style.SUCCESS("Creating new admin user..."))
            username = 'admin' if not User.objects.filter(username='admin').exists() else 'admin_user'
            user = User(username=username, email=admin_email)

        user.set_password(admin_password)
        user.first_name = 'Admin'
        user.last_name = 'User'

        # Set admin properties
        user.role = 'admin'
        user.is_staff = True
        user.is_superuser = True
        user.save()
        
        self.stdout.write(self.style.SUCCESS(f"\nAdmin user ready:"))
        self.stdout.write(f"  Email: {user.email}")
        self.stdout.write(f"  Username: {user.username}")
        self.stdout.write(f"  Role: {getattr(user, 'role', 'N/A')}")
        self.stdout.write(f"  is_staff: {user.is_staff}")
        self.stdout.write(f"  is_superuser: {user.is_superuser}")
        
        # List all users
        self.stdout.write("\nAll users in database:")
        for u in User.objects.all():
            self.stdout.write(f"- {u.username} ({u.email}): role={getattr(u, 'role', 'N/A')}, is_staff={u.is_staff}")