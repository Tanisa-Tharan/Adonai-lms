import secrets
from datetime import timedelta

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.db.models import Prefetch
from django.urls import reverse
from .decorators import admin_required
from django.contrib import messages


from .forms import CreateUserForm
from .models import User, UserProfile
from academics.forms import CreateAcademicYearForm, CreateQuarterForm
from academics.models import AcademicYear, Enrollment
from academics.models import Quarter
from modules.forms import CreateModuleForm
from modules.models import Module, ModuleRun, ModuleSession

ROLE_TABS = {
    "faculty": "FACULTY",
    "students": "STUDENT",
}


def _build_user_form(user=None, role=None):
    if not user:
        initial = {"role": role} if role else None
        return CreateUserForm(initial=initial)

    profile, _ = UserProfile.objects.get_or_create(user=user)
    enrollment = Enrollment.objects.filter(student=user).first()
    initial = {
        "email": user.email,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "role": user.role,
        "phone": profile.phone,
        "address": profile.address,
        "dob": profile.dob,
    }

    if enrollment:
        initial.update({
            "track": enrollment.track,
            "start_date": enrollment.start_date,
            "expected_completion_date": enrollment.expected_completion_date,
            "academic_year": enrollment.academic_year,
        })

    return CreateUserForm(initial=initial)


def _save_user_from_form(form, user=None):
    is_new_user = user is None

    if is_new_user:
        user = User(
            email=form.cleaned_data["email"],
            first_name=form.cleaned_data["first_name"],
            last_name=form.cleaned_data["last_name"],
            role=form.cleaned_data["role"],
            is_active=True,
        )
        generated_password = secrets.token_urlsafe(8)
        user.set_password(generated_password)
    else:
        generated_password = None
        user.email = form.cleaned_data["email"]
        user.first_name = form.cleaned_data["first_name"]
        user.last_name = form.cleaned_data["last_name"]
        user.role = form.cleaned_data["role"]

    user.save()

    profile, _ = UserProfile.objects.get_or_create(user=user)
    profile.phone = form.cleaned_data.get("phone") or ""
    profile.address = form.cleaned_data.get("address") or ""
    profile.dob = form.cleaned_data.get("dob")
    profile.save()

    if user.role == "STUDENT":
        Enrollment.objects.update_or_create(
            student=user,
            defaults={
                "academic_year": form.cleaned_data.get("academic_year"),
                "track": form.cleaned_data.get("track"),
                "start_date": form.cleaned_data.get("start_date"),
                "expected_completion_date": form.cleaned_data.get("expected_completion_date"),
            },
        )
    else:
        Enrollment.objects.filter(student=user).delete()

    return user, generated_password


def _generate_session_dates(start_date, end_date, session_count):
    if session_count == 1:
        return [start_date]

    span_days = (end_date - start_date).days
    return [
        start_date + timedelta(days=round((span_days * index) / (session_count - 1)))
        for index in range(session_count)
    ]


def _save_module_from_form(form):
    with transaction.atomic():
        module = Module.objects.create(
            title=form.cleaned_data["title"],
            description=form.cleaned_data["description"],
            order_number=form.cleaned_data["order_number"],
            session_count=form.cleaned_data["session_count"],
            is_active=form.cleaned_data["is_active"],
        )

        module_run = ModuleRun.objects.create(
            module=module,
            quarter=form.cleaned_data["quarter"],
            faculty=form.cleaned_data["faculty"],
            start_date=form.cleaned_data["start_date"],
            end_date=form.cleaned_data["end_date"],
            max_students=form.cleaned_data["max_students"],
            status=form.cleaned_data["status"],
        )

        ModuleSession.objects.bulk_create([
            ModuleSession(
                module_run=module_run,
                session_number=index,
                session_date=session_date,
            )
            for index, session_date in enumerate(
                _generate_session_dates(
                    form.cleaned_data["start_date"],
                    form.cleaned_data["end_date"],
                    form.cleaned_data["session_count"],
                ),
                start=1,
            )
        ])

    return module


def _build_module_form(module=None):
    if not module:
        return CreateModuleForm()

    latest_run = module.runs.select_related("quarter", "faculty").order_by("-created_at").first()
    initial = {
        "title": module.title,
        "description": module.description,
        "order_number": module.order_number,
        "session_count": module.session_count,
        "is_active": module.is_active,
    }

    if latest_run:
        initial.update({
            "quarter": latest_run.quarter,
            "faculty": latest_run.faculty,
            "start_date": latest_run.start_date,
            "end_date": latest_run.end_date,
            "max_students": latest_run.max_students,
            "status": latest_run.status,
        })

    return CreateModuleForm(initial=initial)


def _update_module_from_form(form, module):
    with transaction.atomic():
        module.title = form.cleaned_data["title"]
        module.description = form.cleaned_data["description"]
        module.order_number = form.cleaned_data["order_number"]
        module.session_count = form.cleaned_data["session_count"]
        module.is_active = form.cleaned_data["is_active"]
        module.save()

        module_run = module.runs.order_by("-created_at").first()
        if module_run:
            module_run.quarter = form.cleaned_data["quarter"]
            module_run.faculty = form.cleaned_data["faculty"]
            module_run.start_date = form.cleaned_data["start_date"]
            module_run.end_date = form.cleaned_data["end_date"]
            module_run.max_students = form.cleaned_data["max_students"]
            module_run.status = form.cleaned_data["status"]
            module_run.save()
            module_run.sessions.all().delete()
        else:
            module_run = ModuleRun.objects.create(
                module=module,
                quarter=form.cleaned_data["quarter"],
                faculty=form.cleaned_data["faculty"],
                start_date=form.cleaned_data["start_date"],
                end_date=form.cleaned_data["end_date"],
                max_students=form.cleaned_data["max_students"],
                status=form.cleaned_data["status"],
            )

        ModuleSession.objects.bulk_create([
            ModuleSession(
                module_run=module_run,
                session_number=index,
                session_date=session_date,
            )
            for index, session_date in enumerate(
                _generate_session_dates(
                    form.cleaned_data["start_date"],
                    form.cleaned_data["end_date"],
                    form.cleaned_data["session_count"],
                ),
                start=1,
            )
        ])

    return module


def _admin_home_context(
    user_form=None,
    active_tab="dashboard",
    user_panel_mode="table",
    editing_user=None,
):
    users = User.objects.all().order_by("-created_at")
    academic_years = AcademicYear.objects.all().prefetch_related(
        Prefetch("quarter_set", queryset=Quarter.objects.all().order_by("quarter_number"))
    ).order_by("-start_date")
    modules = Module.objects.prefetch_related(
        Prefetch(
            "runs",
            queryset=ModuleRun.objects.select_related("quarter", "quarter__academic_year", "faculty").prefetch_related("sessions"),
        )
    ).order_by("order_number", "title")

    student_users = users.filter(role="STUDENT")
    active_modules = modules.filter(is_active=True)

    return {
        "users": users,
        "faculty_users": users.filter(role="FACULTY"),
        "student_users": student_users,
        "academic_years": academic_years,
        "user_form": user_form or CreateUserForm(),
        "active_tab": active_tab,
        "user_panel_mode": user_panel_mode,
        "editing_user": editing_user,
        "academic_year_form": CreateAcademicYearForm(),
        "quarter_form": CreateQuarterForm(),
        "academic_panel_mode": "table",
        "modules": modules,
        "module_form": CreateModuleForm(),
        "module_panel_mode": "table",
        "editing_module": None,
        "module_stats": {
            "total_courses": modules.count(),
            "active_courses": active_modules.count(),
            "total_students": student_users.count(),
        },
    }


def _build_home_context(
    *,
    user_form=None,
    academic_year_form=None,
    quarter_form=None,
    module_form=None,
    active_tab="dashboard",
    user_panel_mode="table",
    academic_panel_mode="table",
    module_panel_mode="table",
    editing_user=None,
    editing_module=None,
):
    context = _admin_home_context(
        user_form=user_form,
        active_tab=active_tab,
        user_panel_mode=user_panel_mode,
        editing_user=editing_user,
    )
    context["academic_year_form"] = academic_year_form or CreateAcademicYearForm()
    context["quarter_form"] = quarter_form or CreateQuarterForm()
    context["academic_panel_mode"] = academic_panel_mode
    context["module_form"] = module_form or CreateModuleForm()
    context["module_panel_mode"] = module_panel_mode
    context["editing_module"] = editing_module
    return context

def login_view(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

        if user:
            login(request, user)

            # Redirect after login
            if user.role == "ADMIN":
                return redirect("home")

    return render(request, "accounts/login.html")


@login_required
@admin_required
def home(request):
    active_tab = request.GET.get("tab", "dashboard")
    selected_role = ROLE_TABS.get(active_tab, request.GET.get("role"))
    user_panel_mode = request.GET.get("mode", "table") if active_tab in ROLE_TABS else "table"
    academic_panel_mode = request.GET.get("mode", "table") if active_tab == "academic-session" else "table"
    module_panel_mode = request.GET.get("mode", "table") if active_tab == "modules" else "table"
    editing_user = None
    editing_module = None
    academic_year_form = CreateAcademicYearForm()
    quarter_form = CreateQuarterForm(initial={
        "academic_year": request.GET.get("year_id"),
    } if request.GET.get("year_id") else None)
    module_form = CreateModuleForm()

    if active_tab in ROLE_TABS and user_panel_mode == "edit":
        editing_user = get_object_or_404(User, id=request.GET.get("user_id"), role__in=["STUDENT", "FACULTY"])
        active_tab = "faculty" if editing_user.role == "FACULTY" else "students"
        user_form = _build_user_form(editing_user)
    else:
        user_form = _build_user_form(role=selected_role)

    if active_tab == "modules" and module_panel_mode == "edit":
        editing_module = get_object_or_404(Module.objects.prefetch_related("runs__sessions"), id=request.GET.get("module_id"))
        module_form = _build_module_form(editing_module)

    if request.method == "POST" and active_tab in ROLE_TABS:
        user_panel_mode = request.GET.get("mode", "create")
        user_id = request.GET.get("user_id")
        editing_user = None

        if user_panel_mode == "edit" and user_id:
            editing_user = get_object_or_404(User, id=user_id, role__in=["STUDENT", "FACULTY"])

        form_data = request.POST.copy()
        if user_panel_mode == "create":
            form_data["role"] = ROLE_TABS[active_tab]

        user_form = CreateUserForm(form_data)
        if user_form.is_valid():
            saved_user, generated_password = _save_user_from_form(user_form, editing_user)

            if generated_password:
                messages.success(request, f"User created. Password: {generated_password}")
            else:
                messages.success(request, f"User updated for {saved_user.first_name} {saved_user.last_name}.")

            next_tab = "faculty" if saved_user.role == "FACULTY" else "students"
            return redirect(f"{reverse('home')}?tab={next_tab}")

    if request.method == "POST" and active_tab == "academic-session":
        academic_panel_mode = request.GET.get("mode", "create-academic-year")

        if academic_panel_mode == "create-academic-year":
            academic_year_form = CreateAcademicYearForm(request.POST)

            if academic_year_form.is_valid():
                AcademicYear.objects.create(
                    name=academic_year_form.cleaned_data["name"],
                    start_date=academic_year_form.cleaned_data["start_date"],
                    end_date=academic_year_form.cleaned_data["end_date"],
                    max_quarters=academic_year_form.cleaned_data["max_quarters"],
                    is_active=True,
                )
                messages.success(request, "Academic year created successfully.")
                return redirect(f"{reverse('home')}?tab=academic-session")

        elif academic_panel_mode == "create-quarter":
            quarter_form = CreateQuarterForm(request.POST)

            if quarter_form.is_valid():
                Quarter.objects.create(
                    academic_year=quarter_form.cleaned_data["academic_year"],
                    name=quarter_form.cleaned_data["name"],
                    quarter_number=quarter_form.cleaned_data["quarter_number"],
                    start_date=quarter_form.cleaned_data["start_date"],
                    end_date=quarter_form.cleaned_data["end_date"],
                    type=quarter_form.cleaned_data["type"],
                )
                messages.success(request, "Quarter created successfully.")
                return redirect(f"{reverse('home')}?tab=academic-session")

    if request.method == "POST" and active_tab == "modules":
        module_panel_mode = request.GET.get("mode", "create")
        module_id = request.GET.get("module_id")
        editing_module = None

        if module_panel_mode == "edit" and module_id:
            editing_module = get_object_or_404(Module.objects.prefetch_related("runs__sessions"), id=module_id)

        module_form = CreateModuleForm(request.POST)

        if module_form.is_valid():
            if module_panel_mode == "edit" and editing_module:
                module = _update_module_from_form(module_form, editing_module)
                messages.success(request, f"Module {module.title} updated successfully.")
            else:
                module = _save_module_from_form(module_form)
                messages.success(request, f"Module {module.title} created successfully.")
            return redirect(f"{reverse('home')}?tab=modules")

    return render(request, "accounts/home.html", _build_home_context(
        user_form=user_form,
        academic_year_form=academic_year_form,
        quarter_form=quarter_form,
        module_form=module_form,
        active_tab=active_tab,
        user_panel_mode=user_panel_mode,
        academic_panel_mode=academic_panel_mode,
        module_panel_mode=module_panel_mode,
        editing_user=editing_user,
        editing_module=editing_module,
    ))

def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
@admin_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST" and user.role != "ADMIN":
        user.delete()
    
    if user == request.user:
        return redirect("home")

    return redirect("home")
