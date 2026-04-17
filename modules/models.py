import uuid

from django.conf import settings
from django.db import models

from academics.models import Quarter


class Module(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
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
        return self.title


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

