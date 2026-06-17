from django import forms
from accounts.models import User, UserProfile
from academics.models import Enrollment, AcademicYear, Quarter


class CreateUserForm(forms.Form):

    # USER
    email = forms.EmailField()
    first_name = forms.CharField()
    last_name = forms.CharField()

    role = forms.ChoiceField(
        choices=User.ROLE_CHOICES,
        widget=forms.Select(attrs={"id":"role_field"})
    )

    # PROFILE
    phone = forms.CharField(required=False)
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"rows": 4})
    )
    dob = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"})
    )
    gender = forms.ChoiceField(
        choices=UserProfile.GENDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={"class": "form-select"})
    )

    # ENROLLMENT (only for student)
    track = forms.ChoiceField(
        choices=Enrollment.TRACK_CHOICES,
        required=False,
        widget=forms.RadioSelect
    )

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type":"date"})
    )
    
    expected_completion_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type":"date"})
    )
    
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        required=False
    )
    
    quarters = forms.ModelMultipleChoiceField(
        queryset=Quarter.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text="Select all quarters the student will be enrolled in"
    )

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")

        if role == "STUDENT":
            required_student_fields = {
                "track": "Track is required for students.",
                "expected_completion_date": "Expected completion date is required for students.",
                "academic_year": "Academic year is required for students.",
            }

            for field_name, error_message in required_student_fields.items():
                if not cleaned_data.get(field_name):
                    self.add_error(field_name, error_message)

        return cleaned_data
