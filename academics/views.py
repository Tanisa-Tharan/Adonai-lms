from django.shortcuts import get_object_or_404, redirect, render
from academics.models import AcademicYear
from accounts.decorators import admin_required
from django.contrib.auth.decorators import login_required

# Create your views here.
@admin_required
def create_academic_year(request):

    if request.method == "POST":

        name = request.POST.get("name")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        AcademicYear.objects.create(
            name=name,
            start_date=start_date,
            end_date=end_date,
            is_active=True
        )

        return redirect("dashboard")

    return render(request, "academics/create_academic_year.html")

@login_required
@admin_required
def delete_academic_year(request, year_id):

    year = get_object_or_404(AcademicYear, id=year_id)

    if request.method == "POST":
        year.delete()

    return redirect("dashboard")