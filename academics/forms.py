from django import forms

from academics.models import AcademicYear, Quarter


class CreateQuarterForm(forms.Form):
    academic_year = forms.ModelChoiceField(
        queryset=AcademicYear.objects.all(),
        required=True,
    )
    name = forms.CharField(max_length=100)
    quarter_number = forms.IntegerField(min_value=1, max_value=12)
    type = forms.ChoiceField(choices=Quarter.TYPE_CHOICES)
    start_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    end_date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))

    def clean(self):
        cleaned_data = super().clean()
        academic_year = cleaned_data.get("academic_year")
        quarter_number = cleaned_data.get("quarter_number")

        if not academic_year or not quarter_number:
            return cleaned_data

        existing_quarters = Quarter.objects.filter(academic_year=academic_year)

        if existing_quarters.count() >= academic_year.max_quarters:
            self.add_error("academic_year", f"Maximum {academic_year.max_quarters} quarters allowed for this academic year.")

        if existing_quarters.filter(quarter_number=quarter_number).exists():
            self.add_error("quarter_number", "This quarter number already exists for the selected academic year.")

        return cleaned_data
