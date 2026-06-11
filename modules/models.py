import uuid
import os

from django.conf import settings
from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver

from academics.models import Enrollment
from academics.models import Quarter


def course_material_upload_path(instance, filename):
    """Generate upload path: course_materials/{module_title}/{filename}"""
    module_title = instance.module.title.replace('/', '-').replace('\\', '-')
    return f'course_materials/{module_title}/{filename}'


def assignment_file_upload_path(instance, filename):
    """Generate upload path: assignment_files/{module_title}/{assignment_title}/{filename}"""
    module_title = instance.assignment.module.title.replace('/', '-').replace('\\', '-')
    assignment_title = instance.assignment.title.replace('/', '-').replace('\\', '-')
    return f'assignment_files/{module_title}/{assignment_title}/{filename}'


def assignment_submission_upload_path(instance, filename):
    """Generate upload path: assignment_submissions/{module_title}/{assignment_title}/{student_serial}/{filename}"""
    module_title = instance.assignment.module.title.replace('/', '-').replace('\\', '-')
    assignment_title = instance.assignment.title.replace('/', '-').replace('\\', '-')
    student_serial = instance.student_module.enrollment.student.serial_number
    return f'assignment_submissions/{module_title}/{assignment_title}/{student_serial}/{filename}'


class Module(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    moduleId = models.CharField(max_length=100, default="MODULE-ID-PENDING")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order_number = models.IntegerField()
    session_count = models.IntegerField(default=3)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "modules"
        ordering = ["order_number", "title"]

    def __str__(self):
        return f"{self.moduleId} - {self.title}"


class ModuleRun(models.Model):
    STATUS_CHOICES = (
        ("SCHEDULED", "Scheduled"),
        ("RUNNING", "Running"),
        ("COMPLETED", "Completed"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="runs")
    quarter = models.ForeignKey(Quarter, on_delete=models.CASCADE, related_name="module_runs")
    faculty = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="module_runs",
    )
    start_date = models.DateField()
    end_date = models.DateField()
    max_students = models.IntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "module_runs"
        ordering = ["-created_at"]


class ModuleSession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module_run = models.ForeignKey(ModuleRun, on_delete=models.CASCADE, related_name="sessions")
    session_number = models.IntegerField()
    session_date = models.DateField()

    class Meta:
        db_table = "module_sessions"
        ordering = ["session_number"]


class StudentModule(models.Model):
    STATUS_CHOICES = (
        ("NOT_STARTED", "Not Started"),
        ("IN_PROGRESS", "In Progress"),
        ("COMPLETED", "Completed"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    enrollment = models.ForeignKey(
        Enrollment,
        on_delete=models.CASCADE,
        related_name="student_modules",
    )
    module_run = models.ForeignKey(
        ModuleRun,
        on_delete=models.CASCADE,
        related_name="student_modules",
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="NOT_STARTED")
    attendance_percentage = models.FloatField(null=True, blank=True)
    final_grade = models.FloatField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "student_modules"
        constraints = [
            models.UniqueConstraint(fields=["enrollment", "module_run"], name="uniq_student_module_enrollment_run"),
        ]


class AttendanceRecord(models.Model):
    STATUS_CHOICES = (
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
        ("LATE", "Late"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module_session = models.ForeignKey(
        ModuleSession,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    student_module = models.ForeignKey(
        StudentModule,
        on_delete=models.CASCADE,
        related_name="attendance_records",
    )
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        db_table = "attendance_records"
        constraints = [
            models.UniqueConstraint(fields=["module_session", "student_module"], name="uniq_attendance_session_student"),
        ]


class CourseMaterial(models.Model):
    MATERIAL_TYPE_CHOICES = (
        ("PDF", "PDF"),
        ("VIDEO", "Video"),
        ("LINK", "Link"),
        ("PPT", "PPT"),
    )
    
    RESOURCE_TYPE_CHOICES = (
        ("REQUIRED", "Required"),
        ("RECOMMENDED", "Recommended"),
        ("RESOURCES", "Resources"),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="course_materials")
    title = models.CharField(max_length=255)
    file_url = models.FileField(upload_to=course_material_upload_path)
    material_type = models.CharField(max_length=10, choices=MATERIAL_TYPE_CHOICES)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES, default="REQUIRED")
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_course_materials",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "course_materials"
        ordering = ["-created_at"]
    
    def delete(self, *args, **kwargs):
        # Delete the file from storage when the model instance is deleted
        if self.file_url:
            self.file_url.delete(save=False)
        super().delete(*args, **kwargs)


class Assignment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="assignments")
    module_run = models.ForeignKey(ModuleRun, on_delete=models.CASCADE, related_name="assignments")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    due_date = models.DateTimeField()
    max_score = models.IntegerField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_assignments",
    )

    class Meta:
        db_table = "assignments"
        ordering = ["-due_date", "-id"]


class AssignmentFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="files")
    file_url = models.FileField(upload_to=assignment_file_upload_path)
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=100, blank=True)
    file_size = models.IntegerField(default=0)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="uploaded_assignment_files",
    )

    class Meta:
        db_table = "assignment_files"
        ordering = ["-uploaded_at"]
    
    def delete(self, *args, **kwargs):
        # Delete the file from storage when the model instance is deleted
        if self.file_url:
            self.file_url.delete(save=False)
        super().delete(*args, **kwargs)


class AssignmentSubmission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name="submissions")
    student_module = models.ForeignKey(
        StudentModule,
        on_delete=models.CASCADE,
        related_name="assignment_submissions",
    )
    file_url = models.FileField(upload_to=assignment_submission_upload_path)
    submitted_at = models.DateTimeField(auto_now_add=True)
    score = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_assignment_submissions",
    )

    class Meta:
        db_table = "assignment_submissions"
        constraints = [
            models.UniqueConstraint(fields=["assignment", "student_module"], name="uniq_assignment_submission"),
        ]
    
    def delete(self, *args, **kwargs):
        # Delete the file from storage when the model instance is deleted
        if self.file_url:
            self.file_url.delete(save=False)
        super().delete(*args, **kwargs)


# Signal handlers to delete files when models are deleted via cascade
@receiver(post_delete, sender=CourseMaterial)
def delete_course_material_file(sender, instance, **kwargs):
    """Delete file from storage when CourseMaterial is deleted"""
    if instance.file_url:
        instance.file_url.delete(save=False)


@receiver(post_delete, sender=AssignmentFile)
def delete_assignment_file(sender, instance, **kwargs):
    """Delete file from storage when AssignmentFile is deleted"""
    if instance.file_url:
        instance.file_url.delete(save=False)


@receiver(post_delete, sender=AssignmentSubmission)
def delete_assignment_submission_file(sender, instance, **kwargs):
    """Delete file from storage when AssignmentSubmission is deleted"""
    if instance.file_url:
        instance.file_url.delete(save=False)
