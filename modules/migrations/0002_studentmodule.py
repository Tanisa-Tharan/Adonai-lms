import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("academics", "0003_academicyear_max_quarters"),
        ("modules", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="StudentModule",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("status", models.CharField(choices=[("NOT_STARTED", "Not Started"), ("IN_PROGRESS", "In Progress"), ("COMPLETED", "Completed")], default="NOT_STARTED", max_length=20)),
                ("attendance_percentage", models.FloatField(blank=True, null=True)),
                ("final_grade", models.FloatField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("enrollment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="student_modules", to="academics.enrollment")),
                ("module_run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="student_modules", to="modules.modulerun")),
            ],
            options={
                "db_table": "student_modules",
            },
        ),
        migrations.AddConstraint(
            model_name="studentmodule",
            constraint=models.UniqueConstraint(fields=("enrollment", "module_run"), name="uniq_student_module_enrollment_run"),
        ),
    ]

