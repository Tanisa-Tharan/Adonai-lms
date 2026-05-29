import uuid
from django.db import models
from django.db import IntegrityError, transaction
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("SUPERVISOR", "Supervisor"),
        ("FACULTY", "Faculty"),
        ("STUDENT", "Student"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    email = models.EmailField(unique=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    serial_number = models.CharField(max_length=7, unique=True, null=True, blank=True, db_index=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name", "role"]

    objects = UserManager()

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.email

    def _generate_student_serial_number(self):
        prefix = str(timezone.now().year)[::-1]
        last_student = (
            User.objects.select_for_update()
            .filter(role="STUDENT", serial_number__startswith=prefix)
            .order_by("-serial_number")
            .first()
        )
        next_seq = 1
        if last_student and last_student.serial_number and len(last_student.serial_number) >= 7:
            try:
                next_seq = int(last_student.serial_number[-3:]) + 1
            except ValueError:
                next_seq = 1
        return f"{prefix}{next_seq:03d}"

    def save(self, *args, **kwargs):
        # Students get an auto-generated serial number like 6202001 (reverse(year) + 3-digit counter).
        if self.role == "STUDENT" and not self.serial_number:
            for _ in range(5):
                try:
                    with transaction.atomic():
                        self.serial_number = self._generate_student_serial_number()
                        return super().save(*args, **kwargs)
                except IntegrityError:
                    # Retry on rare race conditions.
                    self.serial_number = None
            raise
        return super().save(*args, **kwargs)


class UserProfile(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.OneToOneField(User, on_delete=models.CASCADE)

    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)

    dob = models.DateField(null=True, blank=True)

    profile_image = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "user_profiles"
