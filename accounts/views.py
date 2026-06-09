import secrets
from datetime import date as date_type
from datetime import timedelta

from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db import transaction
from django.db.models import Prefetch, Q, Count
from django.urls import reverse
from .decorators import (
    admin_or_faculty_required,
    admin_or_supervisor_required,
    admin_required,
    faculty_required,
    student_required,
)
from django.contrib import messages
from django.core.files.storage import default_storage
from django.utils import timezone


from .forms import CreateUserForm
from .models import User, UserProfile
from academics.forms import CreateAcademicYearForm, CreateQuarterForm
from academics.models import AcademicYear, Enrollment
from academics.models import Quarter
from modules.forms import CreateModuleForm
from modules.models import (
    Assignment,
    AssignmentFile,
    AssignmentSubmission,
    AttendanceRecord,
    CourseMaterial,
    Module,
    ModuleRun,
    ModuleSession,
    StudentModule,
)
from django.core.mail import send_mail
from django.conf import settings

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
            "start_quarter": enrollment.start_quarter,
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

        # SEND EMAIL
        send_mail(
            subject="Your LMS Account Created",
            message=f"""
        Hello {user.first_name},

        Your LMS account has been created.

        Login Details:
        Email: {user.email}
        Password: {generated_password}

        Please login and change your password.

        Regards,
        LMS Team
        """,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

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
                "start_quarter": form.cleaned_data.get("start_quarter"),
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
    
    # Get module runs with assignment counts for assignments panel
    module_runs = ModuleRun.objects.select_related(
        "module", "quarter", "quarter__academic_year", "faculty"
    ).prefetch_related(
        "assignments"
    ).annotate(
        assignment_count=Count("assignments")
    ).order_by("-created_at")

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
        "module_runs": module_runs,
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
            if user.role == "SUPERVISOR":
                return redirect("home")
            if user.role == "FACULTY":
                return redirect("faculty_home")
            if user.role == "STUDENT":
                return redirect("student_home")

    return render(request, "accounts/login.html")


@login_required
@faculty_required
def faculty_home(request):
    active_tab = request.GET.get("tab", "dashboard")

    faculty_runs = (
        ModuleRun.objects.filter(faculty=request.user)
        .select_related("module", "quarter", "quarter__academic_year")
        .prefetch_related("sessions")
        .order_by("-created_at")
    )
    modules = Module.objects.filter(runs__in=faculty_runs).distinct().order_by("order_number", "title")
    student_modules = (
        StudentModule.objects.filter(module_run__in=faculty_runs)
        .select_related("enrollment", "enrollment__student", "module_run", "module_run__module")
        .order_by("enrollment__student__first_name", "enrollment__student__last_name")
    )

    submissions = AssignmentSubmission.objects.filter(
        assignment__module_run__in=faculty_runs,
        student_module__in=student_modules,
    ).select_related("graded_by", "assignment")
    has_submission = set()
    graded_by_faculty = set()
    next_ungraded_assignment_by_student_module = {}
    grade_percent_sum = {}
    grade_percent_count = {}
    for submission in submissions:
        key = str(submission.student_module_id)
        has_submission.add(key)
        if submission.graded_by_id == request.user.id or submission.score is not None:
            graded_by_faculty.add(key)
        if submission.score is None and submission.graded_by_id is None and key not in next_ungraded_assignment_by_student_module:
            next_ungraded_assignment_by_student_module[key] = str(submission.assignment_id)
        if submission.score is not None and submission.assignment and submission.assignment.max_score:
            max_score = float(submission.assignment.max_score)
            if max_score > 0:
                grade_percent_sum[key] = grade_percent_sum.get(key, 0.0) + (float(submission.score) / max_score) * 100.0
                grade_percent_count[key] = grade_percent_count.get(key, 0) + 1

    grade_percentage_by_student_module = {
        sm_id: (grade_percent_sum[sm_id] / grade_percent_count[sm_id])
        for sm_id in grade_percent_sum
        if grade_percent_count.get(sm_id)
    }

    return render(
        request,
        "accounts/faculty/home.html",
        {
            "active_tab": active_tab,
            "faculty_runs": faculty_runs,
            "modules": modules,
            "student_modules": student_modules,
            "faculty_student_has_submission": has_submission,
            "faculty_student_graded": graded_by_faculty,
            "faculty_next_ungraded_assignment": next_ungraded_assignment_by_student_module,
            "faculty_grade_percentage": grade_percentage_by_student_module,
        },
    )


@login_required
@faculty_required
def faculty_students_panel(request):
    active_tab = "students"
    faculty_runs = (
        ModuleRun.objects.filter(faculty=request.user)
        .select_related("module", "quarter", "quarter__academic_year")
        .order_by("-created_at")
    )
    student_modules = (
        StudentModule.objects.filter(module_run__in=faculty_runs)
        .select_related("enrollment", "enrollment__student", "module_run", "module_run__module")
        .order_by("enrollment__student__first_name", "enrollment__student__last_name")
    )

    submissions = AssignmentSubmission.objects.filter(
        assignment__module_run__in=faculty_runs,
        student_module__in=student_modules,
    ).select_related("graded_by", "assignment")
    has_submission = set()
    graded_by_faculty = set()
    next_ungraded_assignment_by_student_module = {}
    grade_percent_sum = {}
    grade_percent_count = {}
    for submission in submissions:
        key = str(submission.student_module_id)
        has_submission.add(key)
        if submission.graded_by_id == request.user.id or submission.score is not None:
            graded_by_faculty.add(key)
        if submission.score is None and submission.graded_by_id is None and key not in next_ungraded_assignment_by_student_module:
            next_ungraded_assignment_by_student_module[key] = str(submission.assignment_id)
        if submission.score is not None and submission.assignment and submission.assignment.max_score:
            max_score = float(submission.assignment.max_score)
            if max_score > 0:
                grade_percent_sum[key] = grade_percent_sum.get(key, 0.0) + (float(submission.score) / max_score) * 100.0
                grade_percent_count[key] = grade_percent_count.get(key, 0) + 1

    grade_percentage_by_student_module = {
        sm_id: (grade_percent_sum[sm_id] / grade_percent_count[sm_id])
        for sm_id in grade_percent_sum
        if grade_percent_count.get(sm_id)
    }

    return render(
        request,
        "accounts/faculty/panels/_students.html",
        {
            "active_tab": active_tab,
            "student_modules": student_modules,
            "faculty_student_has_submission": has_submission,
            "faculty_student_graded": graded_by_faculty,
            "faculty_next_ungraded_assignment": next_ungraded_assignment_by_student_module,
            "faculty_grade_percentage": grade_percentage_by_student_module,
        },
    )


@login_required
@student_required
def student_home(request):
    active_tab = request.GET.get("tab", "dashboard")
    student_modules = (
        StudentModule.objects.filter(enrollment__student=request.user)
        .select_related("enrollment", "module_run", "module_run__module", "module_run__quarter", "module_run__quarter__academic_year")
        .order_by("module_run__module__order_number", "module_run__module__title")
    )
    module_runs = [sm.module_run for sm in student_modules]

    submissions = AssignmentSubmission.objects.filter(student_module__in=student_modules).select_related("assignment")
    submission_by_assignment = {str(s.assignment_id): s for s in submissions}

    due_assignments = (
        Assignment.objects.filter(module_run__in=module_runs)
        .prefetch_related("files")
        .order_by("due_date")
    )

    return render(
        request,
        "accounts/student/home.html",
        {
            "active_tab": active_tab,
            "student_modules": student_modules,
            "due_assignments": due_assignments,
            "submission_by_assignment": submission_by_assignment,
        },
    )


@login_required
@student_required
def student_module_assignments_panel(request, module_run_id):
    student_module = get_object_or_404(
        StudentModule.objects.select_related("module_run", "module_run__module"),
        module_run_id=module_run_id,
        enrollment__student=request.user,
    )
    assignments = (
        Assignment.objects.filter(module_run_id=module_run_id)
        .prefetch_related("files")
        .order_by("-due_date", "-id")
    )
    submissions = AssignmentSubmission.objects.filter(student_module=student_module, assignment__in=assignments)
    submission_by_assignment = {str(s.assignment_id): s for s in submissions}
    now = timezone.now()
    return render(
        request,
        "accounts/student/panels/modules/_assignments.html",
        {
            "student_module": student_module,
            "assignments": assignments,
            "submission_by_assignment": submission_by_assignment,
            "now": now,
        },
    )


@login_required
@student_required
def student_submit_assignment(request, assignment_id, module_run_id):
    if request.method != "POST":
        return redirect("student_home")

    student_module = get_object_or_404(
        StudentModule,
        module_run_id=module_run_id,
        enrollment__student=request.user,
    )
    assignment = get_object_or_404(Assignment, id=assignment_id, module_run_id=module_run_id)
    if timezone.now() > assignment.due_date:
        return student_module_assignments_panel(request, module_run_id=module_run_id)

    upload = request.FILES.get("file")
    if not upload:
        return student_module_assignments_panel(request, module_run_id=module_run_id)

    # Directly assign the file object to FileField
    AssignmentSubmission.objects.update_or_create(
        assignment=assignment,
        student_module=student_module,
        defaults={
            "file_url": upload,
        },
    )

    return student_module_assignments_panel(request, module_run_id=module_run_id)


@login_required
@student_required
def student_delete_submission(request, assignment_id, module_run_id):
    if request.method != "POST":
        return redirect("student_home")

    student_module = get_object_or_404(
        StudentModule,
        module_run_id=module_run_id,
        enrollment__student=request.user,
    )
    assignment = get_object_or_404(Assignment, id=assignment_id, module_run_id=module_run_id)
    if timezone.now() > assignment.due_date:
        return student_module_assignments_panel(request, module_run_id=module_run_id)

    AssignmentSubmission.objects.filter(assignment=assignment, student_module=student_module).delete()
    return student_module_assignments_panel(request, module_run_id=module_run_id)


@login_required
@student_required
def student_module_materials_panel(request, module_id):
    # Ensure student is enrolled in at least one run for this module.
    if not StudentModule.objects.filter(enrollment__student=request.user, module_run__module_id=module_id).exists():
        return redirect("student_home")

    materials = CourseMaterial.objects.filter(module_id=module_id).select_related("module", "uploaded_by").order_by("-created_at")
    module = get_object_or_404(Module, id=module_id)
    return render(
        request,
        "accounts/student/panels/modules/_materials.html",
        {
            "module": module,
            "materials": materials,
        },
    )


@login_required
@admin_or_supervisor_required
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

    if request.user.role == "SUPERVISOR" and active_tab in ROLE_TABS and user_panel_mode == "create":
        return redirect(f"{reverse('home')}?tab={active_tab}")

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
        if request.user.role == "SUPERVISOR":
            messages.error(request, "Supervisors cannot create users.")
            return redirect(f"{reverse('home')}?tab={active_tab}")
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
            else:
                module = _save_module_from_form(module_form)
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


@login_required
@admin_required
def reset_user_password(request, user_id):
    if request.method != "POST":
        return redirect("home")

    user = get_object_or_404(User, id=user_id)
    if user.role == "ADMIN":
        return render(request, "accounts/home/panels/dashboard/_password_cell.html", {"password": ""})

    new_password = secrets.token_urlsafe(8)
    user.set_password(new_password)
    user.save(update_fields=["password"])

    return render(request, "accounts/home/panels/dashboard/_password_cell.html", {"password": new_password})


@login_required
@admin_required
def module_students_panel(request, module_run_id):
    module_run = get_object_or_404(
        ModuleRun.objects.select_related("module", "quarter", "quarter__academic_year", "faculty"),
        id=module_run_id,
    )
    assigned = (
        StudentModule.objects.filter(module_run=module_run)
        .select_related("enrollment", "enrollment__student")
        .order_by("enrollment__student__first_name", "enrollment__student__last_name")
    )
    available_enrollments = (
        Enrollment.objects.select_related("student")
        .filter(status="ACTIVE")
        .exclude(student_modules__module_run=module_run)
        .order_by("student__first_name", "student__last_name")
    )

    return render(
        request,
        "accounts/home/panels/modules/_module_students.html",
        {
            "module_run": module_run,
            "assigned_students": assigned,
            "available_enrollments": available_enrollments,
        },
    )


@login_required
@admin_required
def add_student_to_module_run(request, module_run_id):
    if request.method != "POST":
        return redirect("home")

    module_run = get_object_or_404(ModuleRun, id=module_run_id)
    enrollment_id = request.POST.get("enrollment_id")
    if enrollment_id:
        enrollment = get_object_or_404(Enrollment, id=enrollment_id)
        StudentModule.objects.get_or_create(enrollment=enrollment, module_run=module_run)

    return module_students_panel(request, module_run_id=module_run_id)


@login_required
@admin_required
def remove_student_from_module_run(request, module_run_id, enrollment_id):
    if request.method != "POST":
        return redirect("home")

    StudentModule.objects.filter(module_run_id=module_run_id, enrollment_id=enrollment_id).delete()
    return module_students_panel(request, module_run_id=module_run_id)


def _dates_between(start_date: date_type, end_date: date_type):
    current = start_date
    while current <= end_date:
        yield current
        current += timedelta(days=1)


def _ensure_daily_sessions(module_run):
    existing = set(module_run.sessions.values_list("session_date", flat=True))
    to_create = []
    for session_date in _dates_between(module_run.start_date, module_run.end_date):
        if session_date in existing:
            continue
        to_create.append(
            ModuleSession(
                module_run=module_run,
                session_number=0,  # not used for attendance; keep stable ordering via session_date
                session_date=session_date,
            )
        )
    if to_create:
        ModuleSession.objects.bulk_create(to_create)


@login_required
@admin_required
def module_attendance_panel(request, module_run_id):
    module_run = get_object_or_404(
        ModuleRun.objects.select_related("module", "quarter", "quarter__academic_year", "faculty").prefetch_related("sessions"),
        id=module_run_id,
    )

    # Attendance is per-day between start/end; ensure ModuleSession exists for each day.
    _ensure_daily_sessions(module_run)

    sessions = module_run.sessions.all().order_by("session_date")
    assigned = (
        StudentModule.objects.filter(module_run=module_run)
        .select_related("enrollment", "enrollment__student")
        .order_by("enrollment__student__first_name", "enrollment__student__last_name")
    )
    attendance = AttendanceRecord.objects.filter(
        module_session__module_run=module_run,
        student_module__in=assigned,
    )
    attendance_by_student = {}
    for record in attendance:
        attendance_by_student.setdefault(str(record.student_module_id), {})[str(record.module_session_id)] = record.status

    return render(
        request,
        "accounts/home/panels/modules/_module_attendance.html",
        {
            "module_run": module_run,
            "sessions": sessions,
            "assigned_students": assigned,
            "attendance_by_student": attendance_by_student,
            "attendance_statuses": ["PRESENT", "ABSENT", "LATE"],
        },
    )


@login_required
@admin_required
def save_module_attendance(request, module_run_id):
    if request.method != "POST":
        return redirect("home")

    module_run = get_object_or_404(ModuleRun.objects.prefetch_related("sessions"), id=module_run_id)
    _ensure_daily_sessions(module_run)
    session_ids = {str(session_id) for session_id in module_run.sessions.values_list("id", flat=True)}

    for key, value in request.POST.items():
        if not key.startswith("att__"):
            continue
        # Format: att__<student_module_id>__<module_session_id>
        parts = key.split("__")
        if len(parts) != 3:
            continue
        student_module_id = parts[1]
        module_session_id = parts[2]
        if str(module_session_id) not in session_ids:
            continue
        if value not in {"PRESENT", "ABSENT", "LATE"}:
            continue

        student_module = StudentModule.objects.filter(id=student_module_id, module_run_id=module_run_id).first()
        if not student_module:
            continue
        module_session = ModuleSession.objects.filter(id=module_session_id, module_run_id=module_run_id).first()
        if not module_session:
            continue

        AttendanceRecord.objects.update_or_create(
            module_session=module_session,
            student_module=student_module,
            defaults={"date": module_session.session_date, "status": value},
        )

    # Update attendance_percentage on student_modules for this run.
    total_sessions = module_run.sessions.count()
    student_modules = StudentModule.objects.filter(module_run_id=module_run_id)
    attended_counts = {
        str(row["student_module_id"]): row["attended"]
        for row in AttendanceRecord.objects.filter(
            module_session__module_run_id=module_run_id,
            student_module__in=student_modules,
        )
        .values("student_module_id")
        .annotate(attended=Count("id", filter=Q(status__in=["PRESENT", "LATE"])))
    }
    for student_module in student_modules:
        if total_sessions <= 0:
            student_module.attendance_percentage = None
        else:
            attended = attended_counts.get(str(student_module.id), 0)
            student_module.attendance_percentage = (attended / total_sessions) * 100.0
        student_module.save(update_fields=["attendance_percentage"])

    return module_attendance_panel(request, module_run_id=module_run_id)


@login_required
@admin_or_faculty_required
def course_materials_panel(request):
    module_id = request.GET.get("module_id")
    modules = Module.objects.all().order_by("order_number", "title")
    if request.user.role == "FACULTY":
        modules = modules.filter(runs__faculty=request.user).distinct()
    materials = CourseMaterial.objects.select_related("module", "uploaded_by")
    if module_id:
        if request.user.role == "FACULTY" and not modules.filter(id=module_id).exists():
            module_id = ""
        else:
            materials = materials.filter(module_id=module_id)

    return render(
        request,
        "accounts/home/panels/modules/_course_materials.html",
        {
            "modules": modules,
            "materials": materials.order_by("-created_at"),
            "selected_module_id": module_id or "",
        },
    )


@login_required
@admin_or_faculty_required
def add_course_material(request):
    if request.method != "POST":
        return redirect("home")

    module_id = request.POST.get("module_id")
    title = (request.POST.get("title") or "").strip()
    material_type = request.POST.get("material_type")
    link_url = (request.POST.get("link_url") or "").strip()
    upload = request.FILES.get("file")

    if not module_id or not title or material_type not in {"PDF", "VIDEO", "LINK", "PPT"}:
        return course_materials_panel(request)

    module = get_object_or_404(Module, id=module_id)
    if request.user.role == "FACULTY" and not ModuleRun.objects.filter(module=module, faculty=request.user).exists():
        return course_materials_panel(request)

    if material_type == "LINK":
        if not link_url:
            return course_materials_panel(request)
        # For LINK type, we still store the URL as a string in file_url
        # Note: This will need special handling since file_url is now a FileField
        # For now, create with empty file and store link separately if needed
        CourseMaterial.objects.create(
            module=module,
            title=title,
            file_url='',  # Empty for links - may need model adjustment
            material_type=material_type,
            uploaded_by=request.user,
        )
    else:
        if not upload:
            return course_materials_panel(request)
        # Directly assign the file object to FileField
        CourseMaterial.objects.create(
            module=module,
            title=title,
            file_url=upload,
            material_type=material_type,
            uploaded_by=request.user,
        )

    # Preserve module filter after submit.
    request.GET = request.GET.copy()
    request.GET["module_id"] = module_id
    return course_materials_panel(request)


@login_required
@admin_or_faculty_required
def delete_course_material(request, material_id):
    if request.method != "POST":
        return redirect("home")

    material = get_object_or_404(CourseMaterial, id=material_id)
    if request.user.role == "FACULTY" and not ModuleRun.objects.filter(module_id=material.module_id, faculty=request.user).exists():
        return course_materials_panel(request)
    module_id = str(material.module_id)
    material.delete()

    request.GET = request.GET.copy()
    request.GET["module_id"] = module_id
    return course_materials_panel(request)


@login_required
@admin_or_faculty_required
def module_assignments_panel(request, module_run_id):
    module_run = get_object_or_404(ModuleRun.objects.select_related("module"), id=module_run_id)
    if request.user.role == "FACULTY" and module_run.faculty_id != request.user.id:
        return redirect("faculty_home")
    assignments = (
        Assignment.objects.filter(module_run=module_run)
        .select_related("created_by", "module", "module_run")
        .prefetch_related("files")
        .order_by("-due_date", "-id")
    )
    max_score_by_assignment = {str(a.id): a.max_score for a in assignments}
    student_modules = (
        StudentModule.objects.filter(module_run=module_run)
        .select_related("enrollment", "enrollment__student")
        .order_by("enrollment__student__first_name", "enrollment__student__last_name")
    )
    submissions = AssignmentSubmission.objects.filter(assignment__in=assignments, student_module__in=student_modules)
    submissions_by_assignment = {}
    percentage_by_assignment = {}
    for submission in submissions:
        assignment_key = str(submission.assignment_id)
        student_key = str(submission.student_module_id)
        submissions_by_assignment.setdefault(assignment_key, {})[student_key] = submission
        if submission.score is not None:
            max_score = max_score_by_assignment.get(assignment_key) or 0
            if max_score > 0:
                percentage_by_assignment.setdefault(assignment_key, {})[student_key] = (float(submission.score) / float(max_score)) * 100.0
    editing_assignment = None
    assignment_id = request.GET.get("assignment_id")
    if assignment_id:
        editing_assignment = get_object_or_404(Assignment, id=assignment_id, module_run=module_run)
    
    # Fetch course materials for the module
    course_materials = CourseMaterial.objects.filter(
        module=module_run.module
    ).select_related("uploaded_by").order_by("-created_at")
    
    return render(
        request,
        "accounts/home/panels/modules/_assignments.html",
        {
            "module_run": module_run,
            "assignments": assignments,
            "editing_assignment": editing_assignment,
            "student_modules": student_modules,
            "submissions_by_assignment": submissions_by_assignment,
            "percentage_by_assignment": percentage_by_assignment,
            "course_materials": course_materials,
        },
    )


@login_required
@admin_or_faculty_required
def add_module_assignment(request, module_run_id):
    if request.method != "POST":
        return redirect("home")

    module_run = get_object_or_404(ModuleRun.objects.select_related("module"), id=module_run_id)
    if request.user.role == "FACULTY" and module_run.faculty_id != request.user.id:
        return redirect("faculty_home")
    title = (request.POST.get("title") or "").strip()
    description = (request.POST.get("description") or "").strip()
    due_date = request.POST.get("due_date")
    max_score = request.POST.get("max_score")

    if not title or not due_date or not max_score:
        return module_assignments_panel(request, module_run_id=module_run_id)

    try:
        max_score_int = int(max_score)
    except ValueError:
        return module_assignments_panel(request, module_run_id=module_run_id)

    # Input is a date; interpret it as end-of-day in the current timezone.
    try:
        due_date_value = timezone.datetime.fromisoformat(due_date)
    except ValueError:
        return module_assignments_panel(request, module_run_id=module_run_id)

    due_dt = timezone.datetime.combine(
        due_date_value.date(),
        timezone.datetime.max.time().replace(microsecond=0),
    )
    if timezone.is_naive(due_dt):
        due_dt = timezone.make_aware(due_dt, timezone.get_current_timezone())

    assignment = Assignment.objects.create(
        module=module_run.module,
        module_run=module_run,
        title=title,
        description=description,
        due_date=due_dt,
        max_score=max_score_int,
        created_by=request.user,
    )

    uploads = request.FILES.getlist("files")
    for upload in uploads:
        # Save each file individually (bulk_create doesn't work with FileField)
        AssignmentFile.objects.create(
            assignment=assignment,
            file_url=upload,  # Directly assign the file object to FileField
            file_name=upload.name,
            file_type=getattr(upload, "content_type", "") or "",
            file_size=getattr(upload, "size", 0) or 0,
            uploaded_by=request.user,
        )

    return module_assignments_panel(request, module_run_id=module_run_id)


@login_required
@admin_or_faculty_required
def delete_module_assignment(request, module_run_id, assignment_id):
    if request.method != "POST":
        return redirect("home")

    assignment = get_object_or_404(Assignment, id=assignment_id, module_run_id=module_run_id)
    if request.user.role == "FACULTY" and assignment.module_run.faculty_id != request.user.id:
        return redirect("faculty_home")
    assignment.delete()
    return module_assignments_panel(request, module_run_id=module_run_id)


@login_required
@admin_or_faculty_required
def update_module_assignment(request, module_run_id, assignment_id):
    if request.method != "POST":
        return redirect("home")

    module_run = get_object_or_404(ModuleRun.objects.select_related("module"), id=module_run_id)
    assignment = get_object_or_404(Assignment, id=assignment_id, module_run=module_run)
    if request.user.role == "FACULTY" and module_run.faculty_id != request.user.id:
        return redirect("faculty_home")

    title = (request.POST.get("title") or "").strip()
    description = (request.POST.get("description") or "").strip()
    due_date = request.POST.get("due_date")
    max_score = request.POST.get("max_score")

    if not title or not due_date or not max_score:
        return module_assignments_panel(request, module_run_id=module_run_id)

    try:
        max_score_int = int(max_score)
    except ValueError:
        return module_assignments_panel(request, module_run_id=module_run_id)

    try:
        due_date_value = timezone.datetime.fromisoformat(due_date)
    except ValueError:
        return module_assignments_panel(request, module_run_id=module_run_id)

    due_dt = timezone.datetime.combine(
        due_date_value.date(),
        timezone.datetime.max.time().replace(microsecond=0),
    )
    if timezone.is_naive(due_dt):
        due_dt = timezone.make_aware(due_dt, timezone.get_current_timezone())

    assignment.title = title
    assignment.description = description
    assignment.due_date = due_dt
    assignment.max_score = max_score_int
    assignment.save()

    # Allow attaching more files when editing.
    uploads = request.FILES.getlist("files")
    for upload in uploads:
        # Save each file individually (bulk_create doesn't work with FileField)
        AssignmentFile.objects.create(
            assignment=assignment,
            file_url=upload,  # Directly assign the file object to FileField
            file_name=upload.name,
            file_type=getattr(upload, "content_type", "") or "",
            file_size=getattr(upload, "size", 0) or 0,
            uploaded_by=request.user,
        )

    return module_assignments_panel(request, module_run_id=module_run_id)


@login_required
@admin_required
def assignment_submission_form(request, assignment_id, student_module_id):
    assignment = get_object_or_404(Assignment.objects.select_related("module_run"), id=assignment_id)
    student_module = get_object_or_404(
        StudentModule.objects.select_related("enrollment", "enrollment__student"),
        id=student_module_id,
        module_run=assignment.module_run,
    )
    submission = AssignmentSubmission.objects.filter(assignment=assignment, student_module=student_module).first()
    return render(
        request,
        "accounts/home/panels/modules/_assignment_submit.html",
        {
            "assignment": assignment,
            "student_module": student_module,
            "submission": submission,
        },
    )


@login_required
@admin_required
def submit_assignment(request, assignment_id, student_module_id):
    if request.method != "POST":
        return redirect("home")

    assignment = get_object_or_404(Assignment.objects.select_related("module_run"), id=assignment_id)
    student_module = get_object_or_404(StudentModule, id=student_module_id, module_run=assignment.module_run)
    upload = request.FILES.get("file")
    if not upload:
        return assignment_submission_form(request, assignment_id=assignment_id, student_module_id=student_module_id)

    # Directly assign the file object to FileField
    AssignmentSubmission.objects.update_or_create(
        assignment=assignment,
        student_module=student_module,
        defaults={
            "file_url": upload,
            # score/feedback/graded_by intentionally left blank on submit
        },
    )

    # Return updated assignments panel so statuses refresh.
    return module_assignments_panel(request, module_run_id=str(assignment.module_run_id))


@login_required
@admin_or_faculty_required
def grade_assignment_form(request, assignment_id, student_module_id):
    assignment = get_object_or_404(Assignment.objects.select_related("module_run", "module_run__faculty"), id=assignment_id)
    if request.user.role == "FACULTY" and assignment.module_run.faculty_id != request.user.id:
        return redirect("faculty_home")
    student_module = get_object_or_404(
        StudentModule.objects.select_related("enrollment", "enrollment__student"),
        id=student_module_id,
        module_run=assignment.module_run,
    )
    submission = AssignmentSubmission.objects.filter(assignment=assignment, student_module=student_module).first()
    return render(
        request,
        "accounts/home/panels/modules/_assignment_grade.html",
        {
            "assignment": assignment,
            "student_module": student_module,
            "submission": submission,
            "faculty": assignment.module_run.faculty,
            "grade_error": "",
            "grade_success": "",
        },
    )


@login_required
@admin_or_faculty_required
def grade_assignment_submission(request, assignment_id, student_module_id):
    if request.method != "POST":
        return redirect("home")

    assignment = get_object_or_404(Assignment.objects.select_related("module_run", "module_run__faculty"), id=assignment_id)
    if request.user.role == "FACULTY" and assignment.module_run.faculty_id != request.user.id:
        return redirect("faculty_home")
    student_module = get_object_or_404(StudentModule, id=student_module_id, module_run=assignment.module_run)
    submission = AssignmentSubmission.objects.filter(assignment=assignment, student_module=student_module).first()
    if not submission:
        return module_assignments_panel(request, module_run_id=str(assignment.module_run_id))

    score = request.POST.get("score")
    feedback = (request.POST.get("feedback") or "").strip()
    graded_by_id = request.POST.get("graded_by_id")

    try:
        score_value = float(score) if score not in (None, "") else None
    except ValueError:
        score_value = None

    if score_value is not None and score_value > float(assignment.max_score):
        student_module = get_object_or_404(
            StudentModule.objects.select_related("enrollment", "enrollment__student"),
            id=student_module_id,
            module_run=assignment.module_run,
        )
        return render(
            request,
            "accounts/home/panels/modules/_assignment_grade.html",
            {
                "assignment": assignment,
                "student_module": student_module,
                "submission": submission,
                "faculty": assignment.module_run.faculty,
                "grade_error": f"Score must be less than or equal to {assignment.max_score}.",
            },
        )

    graded_by = None
    if graded_by_id:
        # Restrict to the faculty assigned to this module run.
        if str(assignment.module_run.faculty_id) == str(graded_by_id):
            graded_by = assignment.module_run.faculty

    submission.score = score_value
    submission.feedback = feedback
    submission.graded_by = graded_by
    submission.save()

    return render(
        request,
        "accounts/home/panels/modules/_assignment_grade.html",
        {
            "assignment": assignment,
            "student_module": student_module,
            "submission": submission,
            "faculty": assignment.module_run.faculty,
            "grade_error": "",
            "grade_success": "Grade saved.",
        },
    )


@login_required
@admin_required
def delete_assignment_submission(request, assignment_id, student_module_id):
    if request.method != "POST":
        return redirect("home")

    assignment = get_object_or_404(Assignment.objects.select_related("module_run"), id=assignment_id)
    student_module = get_object_or_404(StudentModule, id=student_module_id, module_run=assignment.module_run)
    AssignmentSubmission.objects.filter(assignment=assignment, student_module=student_module).delete()
    return module_assignments_panel(request, module_run_id=str(assignment.module_run_id))
