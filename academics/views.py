from django.shortcuts import get_object_or_404, redirect
from academics.models import AcademicYear
from accounts.decorators import admin_required
from django.contrib.auth.decorators import login_required

@login_required
@admin_required
def delete_academic_year(request, year_id):

    year = get_object_or_404(AcademicYear, id=year_id)

    if request.method == "POST":
        year.delete()

    return redirect("home")
