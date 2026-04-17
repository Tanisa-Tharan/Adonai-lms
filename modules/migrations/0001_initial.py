import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("academics", "0003_academicyear_max_quarters"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Module",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                ("order_number", models.IntegerField()),
                ("session_count", models.IntegerField(default=3)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "db_table": "modules",
                "ordering": ["order_number", "title"],
            },
        ),
        migrations.CreateModel(
            name="ModuleRun",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("start_date", models.DateField()),
                ("end_date", models.DateField()),
                ("max_students", models.IntegerField()),
                ("status", models.CharField(choices=[("SCHEDULED", "Scheduled"), ("RUNNING", "Running"), ("COMPLETED", "Completed")], max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("faculty", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="module_runs", to=settings.AUTH_USER_MODEL)),
                ("module", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="runs", to="modules.module")),
                ("quarter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="module_runs", to="academics.quarter")),
            ],
            options={
                "db_table": "module_runs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="ModuleSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("session_number", models.IntegerField()),
                ("session_date", models.DateField()),
                ("module_run", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sessions", to="modules.modulerun")),
            ],
            options={
                "db_table": "module_sessions",
                "ordering": ["session_number"],
            },
        ),
    ]
