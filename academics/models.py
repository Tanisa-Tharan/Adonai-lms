from datetime import timezone
import uuid
from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

User = settings.AUTH_USER_MODEL

class AcademicYear(models.Model):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(max_length=100)

    start_date = models.DateField()
    end_date = models.DateField()

    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "academic_years"

    def __str__(self):
        return self.name

class Enrollment(models.Model):

    TRACK_CHOICES = (
        ("DIPLOMA", "Diploma"),
        ("CERTIFICATE", "Certificate"),
        ("INDIVIDUAL", "Individual"),
    )

    STATUS_CHOICES = (
        ("ACTIVE", "Active"),
        ("COMPLETED", "Completed"),
        ("DROPPED", "Dropped"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    student = models.ForeignKey(User, on_delete=models.CASCADE)
    
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        null=True,
        blank=True)

    track = models.CharField(max_length=20, choices=TRACK_CHOICES)    

    track = models.CharField(max_length=20, choices=TRACK_CHOICES)

    start_date = models.DateField()
    expected_completion_date = models.DateField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "enrollments"

class Quarter(models.Model):

    TYPE_CHOICES = (
        ("MODULE", "Module"),
        ("QUIZ", "Quiz"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        null=True,
        blank=True)

    name = models.CharField(max_length=100)

    quarter_number = models.IntegerField()

    start_date = models.DateField()
    end_date = models.DateField()

    type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    class Meta:
        db_table = "quarters"

def clean(self):

    if self.start_date.year != self.end_date.year:
        raise ValidationError("Start and End date must be in same year")

    if self.start_date.year != timezone.now().year:
        raise ValidationError("Academic year must start in current year")