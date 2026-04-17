from django import forms

from accounts.models import User
from academics.models import Quarter

from .models import ModuleRun


class FacultyChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name or obj.email


class QuarterChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        academic_year = obj.academic_year.name if obj.academic_year else "No Academic Year"
        return f"{academic_year} - Quarter {obj.quarter_number}: {obj.name}"


class CreateModuleForm(forms.Form):
    title = forms.CharField(max_length=255)
    description = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4}),
    )
    order_number = forms.IntegerField(min_value=1)
    session_count = forms.IntegerField(min_value=1, initial=3)
    is_active = forms.BooleanField(required=False, initial=True)

    quarter = QuarterChoiceField(
        queryset=Quarter.objects.none(),
        required=True,
    )
    faculty = FacultyChoiceField(
        queryset=User.objects.none(),
        required=True,
    )
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    max_students = forms.IntegerField(min_value=1)
    status = forms.ChoiceField(choices=ModuleRun.STATUS_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["quarter"].queryset = Quarter.objects.select_related("academic_year").order_by(
            "academic_year__start_date", "quarter_number"
        )
        self.fields["faculty"].queryset = User.objects.filter(role="FACULTY").order_by("first_name", "last_name")

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and end_date < start_date:
            self.add_error("end_date", "End date must be on or after the start date.")

        return cleaned_data
