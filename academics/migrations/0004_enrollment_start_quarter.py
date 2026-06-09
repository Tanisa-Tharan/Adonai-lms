# Generated migration

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0003_academicyear_max_quarters'),
    ]

    operations = [
        migrations.AddField(
            model_name='enrollment',
            name='start_quarter',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='enrollments', to='academics.quarter'),
        ),
    ]
