from django.core.management.base import BaseCommand, CommandError

from accounts.models import User


class Command(BaseCommand):
    help = "Create a supervisor user (role=SUPERVISOR)."

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True)
        parser.add_argument("--first-name", required=True)
        parser.add_argument("--last-name", required=True)
        parser.add_argument("--password", required=True)

    def handle(self, *args, **options):
        email = options["email"].strip().lower()
        first_name = options["first_name"].strip()
        last_name = options["last_name"].strip()
        password = options["password"]

        if User.objects.filter(email=email).exists():
            raise CommandError("User with this email already exists.")

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role="SUPERVISOR",
            is_active=True,
            is_staff=True,
        )

        self.stdout.write(self.style.SUCCESS(f"Created supervisor: {user.email}"))

