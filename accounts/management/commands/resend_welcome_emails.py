from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import User


class Command(BaseCommand):
    help = "Resend welcome email to a user and reset their password to the default format"

    def add_arguments(self, parser):
        parser.add_argument("--email", required=True, help="Email address of the user")

    def handle(self, *args, **options):
        email = options["email"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise CommandError(f'No user found with email "{email}"')

        generated_password = f"{user.first_name}@abs@2026"
        user.set_password(generated_password)
        user.save()

        try:
            send_mail(
                subject="Your LMS Account Created",
                message=f"""
Hello {user.first_name},

Your LMS account has been created.

Login Details:
Email: {user.email}
Password: {generated_password}

Please login and change your password.

Regards,
LMS Team
""",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS(
                f"Welcome email sent to {user.email} and password reset to default."
            ))
        except Exception as e:
            raise CommandError(f"Failed to send email: {e}")
