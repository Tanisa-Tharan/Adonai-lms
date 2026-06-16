from django.core.management.base import BaseCommand
from django.db.models import Q

from accounts.models import User


class Command(BaseCommand):
    help = "Update passwords for existing users (excluding ADMIN and SUPERVISOR) to format: Firstname@abs@2026"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Update password for a specific user by email',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        specific_email = options.get('email')

        # Build query to exclude ADMIN and SUPERVISOR roles
        query = Q(role__in=['FACULTY', 'STUDENT'])
        
        if specific_email:
            query &= Q(email=specific_email.strip().lower())
            users = User.objects.filter(query)
            if not users.exists():
                self.stdout.write(self.style.ERROR(f"No user found with email: {specific_email}"))
                return
        else:
            users = User.objects.filter(query)

        if not users.exists():
            self.stdout.write(self.style.WARNING("No users found to update."))
            return

        self.stdout.write(self.style.WARNING(f"Found {users.count()} user(s) to update."))
        self.stdout.write("")

        updated_count = 0
        for user in users:
            new_password = f"{user.first_name}@abs@2026"
            
            if dry_run:
                self.stdout.write(
                    f"[DRY RUN] Would update: {user.email} ({user.first_name} {user.last_name}) - "
                    f"Role: {user.role} - New password: {new_password}"
                )
            else:
                user.set_password(new_password)
                user.save(update_fields=['password'])
                updated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Updated: {user.email} ({user.first_name} {user.last_name}) - "
                        f"Role: {user.role} - New password: {new_password}"
                    )
                )

        self.stdout.write("")
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f"DRY RUN completed. {users.count()} user(s) would be updated. "
                    "Run without --dry-run to apply changes."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully updated passwords for {updated_count} user(s)."
                )
            )

# Made with Bob
