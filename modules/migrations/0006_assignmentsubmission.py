import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("modules", "0005_assignments"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AssignmentSubmission",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("file_url", models.CharField(max_length=1024)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("score", models.FloatField(blank=True, null=True)),
                ("feedback", models.TextField(blank=True)),
                ("assignment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="submissions", to="modules.assignment")),
                ("graded_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="graded_assignment_submissions", to=settings.AUTH_USER_MODEL)),
                ("student_module", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignment_submissions", to="modules.studentmodule")),
            ],
            options={
                "db_table": "assignment_submissions",
            },
        ),
        migrations.AddConstraint(
            model_name="assignmentsubmission",
            constraint=models.UniqueConstraint(fields=("assignment", "student_module"), name="uniq_assignment_submission"),
        ),
    ]

