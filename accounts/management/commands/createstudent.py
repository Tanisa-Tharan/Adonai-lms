from django.core.management.base import BaseCommand
from django.core.management import CommandError
from accounts.models import User


class Command(BaseCommand):
    help = 'Create a student user'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Student email address')
        parser.add_argument('--password', type=str, help='Student password')
        parser.add_argument('--first-name', type=str, help='Student first name')
        parser.add_argument('--last-name', type=str, help='Student last name')

    def handle(self, *args, **options):
        email = options.get('email')
        password = options.get('password')
        first_name = options.get('first_name')
        last_name = options.get('last_name')

        # Interactive mode if arguments not provided
        if not email:
            email = input('Email address: ')
        
        if not first_name:
            first_name = input('First name: ')
        
        if not last_name:
            last_name = input('Last name: ')
        
        if not password:
            from getpass import getpass
            password = getpass('Password: ')
            password_confirm = getpass('Password (again): ')
            
            if password != password_confirm:
                raise CommandError('Passwords do not match')

        if not email:
            raise CommandError('Email is required')

        if User.objects.filter(email=email).exists():
            raise CommandError(f'User with email {email} already exists')

        try:
            user = User.objects.create_student(
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            self.stdout.write(self.style.SUCCESS(f'Successfully created student: {user.email}'))
        except Exception as e:
            raise CommandError(f'Error creating student: {str(e)}')

# Made with Bob
