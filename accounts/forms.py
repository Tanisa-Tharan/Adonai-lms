from django import forms
from accounts.models import User, UserProfile
from academics.models import Enrollment, AcademicYear


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
    address = forms.CharField(required=False)
    dob = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date"})
    )

    # ENROLLMENT (only for student)
    track = forms.ChoiceField(
        choices=Enrollment.TRACK_CHOICES,
        required=False
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
