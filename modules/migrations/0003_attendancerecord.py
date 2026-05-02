import uuid

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("modules", "0002_studentmodule"),
    ]

    operations = [
        migrations.CreateModel(
            name="AttendanceRecord",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("date", models.DateField()),
                ("status", models.CharField(choices=[("PRESENT", "Present"), ("ABSENT", "Absent"), ("LATE", "Late")], max_length=10)),
                ("module_session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_records", to="modules.modulesession")),
                ("student_module", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="attendance_records", to="modules.studentmodule")),
            ],
            options={
                "db_table": "attendance_records",
            },
        ),
        migrations.AddConstraint(
            model_name="attendancerecord",
            constraint=models.UniqueConstraint(fields=("module_session", "student_module"), name="uniq_attendance_session_student"),
        ),
    ]

