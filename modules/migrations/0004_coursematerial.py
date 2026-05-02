import uuid

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("modules", "0003_attendancerecord"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CourseMaterial",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("file_url", models.CharField(max_length=1024)),
                ("material_type", models.CharField(choices=[("PDF", "PDF"), ("VIDEO", "Video"), ("LINK", "Link"), ("PPT", "PPT")], max_length=10)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("module", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="course_materials", to="modules.module")),
                ("uploaded_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="uploaded_course_materials", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "course_materials",
                "ordering": ["-created_at"],
            },
        ),
    ]

