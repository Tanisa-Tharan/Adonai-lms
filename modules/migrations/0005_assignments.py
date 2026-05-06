import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("modules", "0004_coursematerial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Assignment",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("due_date", models.DateTimeField()),
                ("max_score", models.IntegerField()),
                ("created_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="created_assignments", to=settings.AUTH_USER_MODEL)),
                ("module", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignments", to="modules.module")),
                ("module_run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assignments", to="modules.modulerun")),
            ],
            options={
                "db_table": "assignments",
                "ordering": ["-due_date", "-id"],
            },
        ),
        migrations.CreateModel(
            name="AssignmentFile",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("file_url", models.CharField(max_length=1024)),
                ("file_name", models.CharField(max_length=255)),
                ("file_type", models.CharField(blank=True, max_length=100)),
                ("file_size", models.IntegerField(default=0)),
                ("uploaded_at", models.DateTimeField(auto_now_add=True)),
                ("assignment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="files", to="modules.assignment")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="uploaded_assignment_files", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "assignment_files",
                "ordering": ["-uploaded_at"],
            },
        ),
    ]

