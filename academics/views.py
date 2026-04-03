from pyexpat.errors import messages

from django.shortcuts import get_object_or_404, redirect, render
from academics.models import AcademicYear, Quarter
from accounts.decorators import admin_required
from django.contrib.auth.decorators import login_required

# Create your views here.
@admin_required
def create_academic_year(request):

    if request.method == "POST":

        name = request.POST.get("name")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        max_quarters = int(request.POST.get("max_quarters"))

        AcademicYear.objects.create(
            name=name,
            start_date=start_date,
            end_date=end_date,
            max_quarters=max_quarters,
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

@login_required
@admin_required
def create_quarter(request):

    academic_years = AcademicYear.objects.all()
    selected_year_id = request.GET.get("year_id")

    context = {
        "academic_years": academic_years,
        "selected_year_id": selected_year_id
    }

    if request.method == "POST":

        academic_year_id = request.POST.get("academic_year")
        name = request.POST.get("name")
        quarter_number = int(request.POST.get("quarter_number"))
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")

        academic_year = get_object_or_404(AcademicYear, id=academic_year_id)

        # Check against maximum quarters
        existing_count = Quarter.objects.filter(academic_year=academic_year).count()
        if existing_count >= academic_year.max_quarters:
            messages.error(
                request,
                f"Maximum {academic_year.max_quarters} quarters allowed for this academic year.")

            return redirect("create_quarter")

        q_type = request.POST.get("type")

        if q_type not in ["MODULE", "QUIZ"]:
            messages.error(request, "Invalid quarter type selected.")
            return redirect("create_quarter")

        # Prevent duplicate quarter_number
        if Quarter.objects.filter(academic_year=academic_year, quarter_number=quarter_number).exists():
            messages.error(request, "This quarter number already exists for the selected academic year.")
            return redirect("create_quarter")

        Quarter.objects.create(
            academic_year=academic_year,
            name=name,
            quarter_number=quarter_number,
            start_date=start_date,
            end_date=end_date,
            type=q_type
        )

        messages.success(request, f"Quarter created successfully as {q_type}")

        return redirect("create_quarter")

    return render(request, "academics/create_quarter.html", context)