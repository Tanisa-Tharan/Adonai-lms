import secrets
from datetime import date as date_type
from datetime import timedelta

from django.shortcuts import get_object_or_404, render, redirect
from django.http import JsonResponse
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
            "quarters": enrollment.quarters.all(),
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
        # Generate password in format: Firstname@abs@2026
        generated_password = f"{user.first_name}@abs@2026"
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
        enrollment, created = Enrollment.objects.update_or_create(
            student=user,
            defaults={
                "academic_year": form.cleaned_data.get("academic_year"),
                "track": form.cleaned_data.get("track"),
                "start_date": form.cleaned_data.get("start_date"),
                "expected_completion_date": form.cleaned_data.get("expected_completion_date"),
            },
        )
        
        # Handle ManyToMany quarters field
        quarters = form.cleaned_data.get("quarters")
        if quarters:
            enrollment.quarters.set(quarters)
            # Auto-enroll student in all modules from selected quarters
            _auto_enroll_student_in_quarter_modules(enrollment, quarters)
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


def _auto_enroll_students_in_module(module_run):
    """
    Automatically enroll all students from the module's quarter into the module.
    Creates StudentModule records for all active enrollments in the quarter.
    """
    quarter = module_run.quarter
    
    # Get all active enrollments that include this quarter
    enrollments = Enrollment.objects.filter(
        academic_year=quarter.academic_year,
        status="ACTIVE",
        quarters=quarter
    ).select_related("student")
    
    # Create StudentModule records for students who aren't already enrolled
    student_modules_to_create = []
    for enrollment in enrollments:
        # Check if student is already enrolled in this module run
        if not StudentModule.objects.filter(
            enrollment=enrollment,
            module_run=module_run
        ).exists():
            student_modules_to_create.append(
                StudentModule(
                    enrollment=enrollment,
                    module_run=module_run,
                    status="NOT_STARTED"
                )
            )
    
    # Bulk create all student module records
    if student_modules_to_create:
        StudentModule.objects.bulk_create(student_modules_to_create)
    
    return len(student_modules_to_create)


def _auto_enroll_student_in_quarter_modules(enrollment, quarters):
    """
    Automatically enroll a student in all modules from their selected quarters.
    Creates StudentModule records for all module runs in the specified quarters.
    """
    if not quarters:
        return 0
    
    # Get all module runs for the selected quarters
    module_runs = ModuleRun.objects.filter(
        quarter__in=quarters
    ).select_related("module", "quarter")
    
    # Create StudentModule records for modules the student isn't already enrolled in
    student_modules_to_create = []
    for module_run in module_runs:
        # Check if student is already enrolled in this module run
        if not StudentModule.objects.filter(
            enrollment=enrollment,
            module_run=module_run
        ).exists():
            student_modules_to_create.append(
                StudentModule(
                    enrollment=enrollment,
                    module_run=module_run,
                    status="NOT_STARTED"
                )
            )
    
    # Bulk create all student module records
    if student_modules_to_create:
        StudentModule.objects.bulk_create(student_modules_to_create)
    
    return len(student_modules_to_create)


def _save_module_from_form(form):
    with transaction.atomic():
        module = Module.objects.create(
            moduleId=form.cleaned_data["moduleId"],
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
        
        # Auto-enroll all students from the selected quarter
        _auto_enroll_students_in_module(module_run)

    return module


def _build_module_form(module=None):
    if not module:
        return CreateModuleForm()

    latest_run = module.runs.select_related("quarter", "faculty").order_by("-created_at").first()
    initial = {
        "moduleId": module.moduleId,
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
        module.moduleId = form.cleaned_data["moduleId"]
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
        
        # Auto-enroll all students from the selected quarter
        _auto_enroll_students_in_module(module_run)

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
    assignment_mode = request.GET.get("mode", "table")  # 'table' or 'create'

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
    pending_grades_count = submissions.filter(score__isnull=True, graded_by__isnull=True).count()
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

    faculty_module_items = [
        {
            "id": str(run.id),
            "module_id": str(run.module.id),
            "title": run.module.title,
            "subtitle": run.quarter.name,
            "meta_icon": "assignments",
            "meta_text": f"{run.assignments.count()} Assignment{'s' if run.assignments.count() != 1 else ''}",
            "action_url": reverse("faculty_view_class_panel", args=[run.id]),
        }
        for run in faculty_runs
    ]

    # Get all assignments for faculty
    faculty_assignments = (
        Assignment.objects.filter(module_run__in=faculty_runs)
        .select_related("module_run", "module_run__module")
        .order_by("-due_date")
    )

    return render(
        request,
        "accounts/faculty/home.html",
        {
            "active_tab": active_tab,
            "assignment_mode": assignment_mode,
            "faculty_runs": faculty_runs,
            "modules": modules,
            "student_modules": student_modules,
            "faculty_student_has_submission": has_submission,
            "faculty_student_graded": graded_by_faculty,
            "faculty_next_ungraded_assignment": next_ungraded_assignment_by_student_module,
            "faculty_grade_percentage": grade_percentage_by_student_module,
            "pending_grades_count": pending_grades_count,
            "faculty_module_items": faculty_module_items,
            "faculty_assignments": faculty_assignments,
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
@faculty_required
def faculty_view_class_panel(request, module_run_id):
    """View class details with enrolled students for faculty"""
    module_run = get_object_or_404(
        ModuleRun.objects.select_related("module", "faculty", "quarter"),
        id=module_run_id,
        faculty=request.user
    )
    
    enrolled_students = StudentModule.objects.filter(
        module_run=module_run
    ).select_related(
        "enrollment",
        "enrollment__student",
        "enrollment__academic_year"
    ).order_by("enrollment__student__first_name", "enrollment__student__last_name")
    
    return render(
        request,
        "accounts/faculty/panels/_view_class.html",
        {
            "module_run": module_run,
            "enrolled_students": enrolled_students,
        },
    )



@login_required
@faculty_required
def faculty_student_submissions(request, student_module_id, module_run_id):
    """Get all assignment submissions for a specific student in a module"""
    student_module = get_object_or_404(
        StudentModule.objects.select_related(
            "enrollment",
            "enrollment__student",
            "module_run",
            "module_run__module"
        ),
        id=student_module_id,
        module_run_id=module_run_id
    )
    
    # Verify faculty has access to this module
    if student_module.module_run.faculty_id != request.user.id:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    # Get all assignments for this module
    assignments = Assignment.objects.filter(
        module_run_id=module_run_id
    ).order_by('due_date')
    
    # Get all submissions for this student
    submissions = AssignmentSubmission.objects.filter(
        student_module=student_module
    ).select_related('assignment')
    
    # Create a dictionary of submissions by assignment_id
    submissions_dict = {sub.assignment_id: sub for sub in submissions}
    
    # Attach submission to each assignment
    assignments_with_submissions = []
    for assignment in assignments:
        assignment.submission = submissions_dict.get(assignment.id)
        assignments_with_submissions.append(assignment)
    
    # Update header with student info
    student = student_module.enrollment.student
    student_name = f"{student.first_name} {student.last_name}"
    module_title = student_module.module_run.module.title
    
    context = {
        "student_module": student_module,
        "assignments": assignments_with_submissions,
        "student_name": student_name,
        "module_title": module_title,
    }
    
    # Render and return the template with header update script
    response = render(request, "accounts/faculty/panels/_student_submissions_table.html", context)
    
    # Add script to update header
    header_script = f"""
<script>
document.getElementById('student-name-header').textContent = '{student_name}';
document.getElementById('student-info-subtitle').textContent = '{module_title}';
</script>
"""
    
    # Append script to response content
    content = response.content.decode('utf-8') + header_script
    response.content = content.encode('utf-8')
    
    return response


@login_required
@faculty_required
def faculty_grade_submission_view(request, assignment_id, submission_id):
    """Display the grading view for a specific submission"""
    assignment = get_object_or_404(
        Assignment.objects.select_related('module_run', 'module_run__faculty'),
        id=assignment_id
    )
    
    # Verify faculty has access to this assignment
    if assignment.module_run.faculty_id != request.user.id:
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    submission = get_object_or_404(
        AssignmentSubmission.objects.select_related(
            'student_module',
            'student_module__enrollment',
            'student_module__enrollment__student'
        ),
        id=submission_id,
        assignment=assignment
    )
    
    context = {
        'assignment': assignment,
        'submission': submission,
        'student_module': submission.student_module,
    }
    
    return render(request, 'accounts/faculty/panels/_submission_grading_view.html', context)


@login_required
@faculty_required
def faculty_grade_submission_submit(request, assignment_id, submission_id):
    """Handle the submission of a grade"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"Grade submission request received - Assignment: {assignment_id}, Submission: {submission_id}")
    logger.info(f"Request method: {request.method}")
    logger.info(f"POST data: {request.POST}")
    
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    
    assignment = get_object_or_404(
        Assignment.objects.select_related('module_run'),
        id=assignment_id
    )
    
    logger.info(f"Assignment found: {assignment.title}, Faculty: {assignment.module_run.faculty_id}, Current user: {request.user.id}")
    
    # Verify faculty has access to this assignment
    if assignment.module_run.faculty_id != request.user.id:
        logger.error(f"Unauthorized access attempt by user {request.user.id}")
        return JsonResponse({"error": "Unauthorized"}, status=403)
    
    submission = get_object_or_404(
        AssignmentSubmission,
        id=submission_id,
        assignment=assignment
    )
    
    logger.info(f"Submission found: {submission.id}, Current status: {submission.status}")
    
    # Get form data
    score = request.POST.get('score')
    feedback = request.POST.get('feedback', '').strip()
    graded_by_id = request.POST.get('graded_by_id')
    
    logger.info(f"Form data - Score: {score}, Feedback length: {len(feedback)}, Graded by: {graded_by_id}")
    
    # Validate score
    if not score:
        logger.error("Score is missing")
        return JsonResponse({"success": False, "error": "Score is required"}, status=400)
    
    try:
        score_value = float(score)
    except ValueError:
        logger.error(f"Invalid score value: {score}")
        return JsonResponse({"success": False, "error": "Invalid score value"}, status=400)
    
    if score_value < 0 or score_value > assignment.max_score:
        logger.error(f"Score out of range: {score_value}, Max: {assignment.max_score}")
        return JsonResponse({
            "success": False,
            "error": f"Score must be between 0 and {assignment.max_score}"
        }, status=400)
    
    # Verify graded_by is the current user
    if str(graded_by_id) != str(request.user.id):
        logger.error(f"Grader mismatch: {graded_by_id} vs {request.user.id}")
        return JsonResponse({"success": False, "error": "Invalid grader"}, status=400)
    
    # Update submission
    logger.info(f"Updating submission - Score: {score_value}, Status: graded")
    submission.score = score_value
    submission.feedback = feedback
    submission.graded_by = request.user
    submission.status = 'graded'
    submission.save()
    
    logger.info(f"Submission updated successfully - ID: {submission.id}")
    
    return JsonResponse({
        "success": True,
        "message": "Grade submitted successfully"
    })


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

    student_module_items = [
        {
            "id": str(sm.id),
            "module_id": str(sm.module_run.module.id),
            "title": sm.module_run.module.title,
            "subtitle": sm.module_run.quarter.name,
            "meta_icon": "modules",
            "meta_text": (
                f"{sm.attendance_percentage:.0f}% Attendance"
                if sm.attendance_percentage is not None
                else "Attendance not available"
            ),
            "action_url": reverse("student_module_assignments_panel", args=[sm.module_run.id]),
        }
        for sm in student_modules
    ]

    return render(
        request,
        "accounts/student/home.html",
        {
            "active_tab": active_tab,
            "student_modules": student_modules,
            "due_assignments": due_assignments,
            "submission_by_assignment": submission_by_assignment,
            "student_module_items": student_module_items,
        },
    )


@login_required
@student_required
def student_module_assignments_panel(request, module_run_id):
    student_module = get_object_or_404(
        StudentModule.objects.select_related("module_run", "module_run__module", "module_run__faculty"),
        module_run_id=module_run_id,
        enrollment__student=request.user,
    )
    module_run = student_module.module_run
    assignments = (
        Assignment.objects.filter(module_run_id=module_run_id)
        .prefetch_related("files")
        .order_by("-due_date", "-id")
    )
    submissions = AssignmentSubmission.objects.filter(student_module=student_module, assignment__in=assignments)
    submission_by_assignment = {str(s.assignment_id): s for s in submissions}
    
    # Get course materials categorized by resource type
    all_materials = CourseMaterial.objects.filter(module_id=module_run.module.id).select_related("uploaded_by").order_by("-created_at")
    required_materials = all_materials.filter(resource_type="REQUIRED")
    recommended_materials = all_materials.filter(resource_type="RECOMMENDED")
    resource_materials = all_materials.filter(resource_type="RESOURCES")
    
    now = timezone.now()
    # Use the same template as faculty/admin but with student-specific context
    return render(
        request,
        "accounts/home/panels/modules/_assignments.html",
        {
            "student_module": student_module,
            "module_run": module_run,
            "assignments": assignments,
            "submission_by_assignment": submission_by_assignment,
            "required_materials": required_materials,
            "recommended_materials": recommended_materials,
            "resource_materials": resource_materials,
            "now": now,
        },
    )


@login_required
def student_submit_assignment(request, assignment_id, module_run_id=None):
    if request.method != "POST":
        if request.user.role == "STUDENT":
            return redirect("student_home")
        return redirect("home")

    # Handle both URL patterns - with and without module_run_id
    if not module_run_id:
        assignment = get_object_or_404(Assignment, id=assignment_id)
        module_run_id = assignment.module_run_id
    
    assignment = get_object_or_404(Assignment, id=assignment_id, module_run_id=module_run_id)
    
    # For ADMIN, allow selecting which student to submit for
    # For STUDENT, use their own enrollment
    if request.user.role == "ADMIN":
        # Check if a student_module_id was provided in the request
        student_module_id = request.POST.get("student_module_id")
        
        if student_module_id:
            # Admin selected a specific student
            student_module = get_object_or_404(
                StudentModule,
                id=student_module_id,
                module_run_id=module_run_id
            )
        else:
            # No student selected, check if admin has their own enrollment
            admin_enrollment = Enrollment.objects.filter(student=request.user).first()
            if admin_enrollment:
                # Admin is also a student, use their student module
                student_module, created = StudentModule.objects.get_or_create(
                    module_run_id=module_run_id,
                    enrollment=admin_enrollment
                )
            else:
                # Admin is not a student, create enrollment with proper fields
                from academics.models import AcademicYear
                academic_year = AcademicYear.objects.first()
                if not academic_year:
                    messages.error(request, "No academic year found. Please create one first.")
                    return module_assignments_panel(request, module_run_id=module_run_id)
                
                # Calculate expected completion date (1 year from start)
                from datetime import timedelta
                start_date = timezone.now().date()
                expected_completion = start_date + timedelta(days=365)
                
                # Create enrollment for admin with all required fields
                admin_enrollment, _ = Enrollment.objects.get_or_create(
                    student=request.user,
                    defaults={
                        'academic_year': academic_year,
                        'track': 'FULL_TIME',
                        'start_date': start_date,
                        'expected_completion_date': expected_completion,
                    }
                )
                
                # Create student module
                student_module, created = StudentModule.objects.get_or_create(
                    module_run_id=module_run_id,
                    enrollment=admin_enrollment
                )
    else:
        # Student user
        student_module = get_object_or_404(
            StudentModule,
            module_run_id=module_run_id,
            enrollment__student=request.user,
        )
    
    # Get description and status from POST data
    description = request.POST.get("description", "")
    status = request.POST.get("status", "submitted")  # Default to 'submitted' for backward compatibility
    upload = request.FILES.get("file")
    
    # Allow submission with description only (no file required)
    if not description and not upload:
        if request.user.role == "STUDENT":
            return student_module_assignments_panel(request, module_run_id=module_run_id)
        # For admin, return to the module assignments panel
        return module_assignments_panel(request, module_run_id=module_run_id)

    # Update or create submission
    defaults = {
        "description": description,
        "status": status,
    }
    
    # Only update file if provided
    if upload:
        defaults["file_url"] = upload
    
    try:
        submission, created = AssignmentSubmission.objects.update_or_create(
            assignment=assignment,
            student_module=student_module,
            defaults=defaults,
        )
        
        # Log the submission for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Assignment submission {'created' if created else 'updated'}: "
                   f"Assignment={assignment.id}, StudentModule={student_module.id}, "
                   f"Description length={len(description)}, Has file={bool(upload)}")
        
        # # Add success message
        # if created:
        #     messages.success(request, "Assignment submitted successfully!")
        # else:
        #     messages.success(request, "Assignment updated successfully!")
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error saving assignment submission: {str(e)}")
        messages.error(request, f"Error submitting assignment: {str(e)}")

    # Return appropriate panel based on user role
    if request.user.role == "STUDENT":
        return student_module_assignments_panel(request, module_run_id=module_run_id)
    else:
        return module_assignments_panel(request, module_run_id=module_run_id)


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
            
            # Redirect to the return tab if specified, otherwise default to modules
            return_tab = request.GET.get("return_tab", "modules")
            return redirect(f"{reverse('home')}?tab={return_tab}")

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

    # Generate password in format: Firstname@abs@2026
    new_password = f"{user.first_name}@abs@2026"
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
    resource_type = request.POST.get("resource_type") or "REQUIRED"
    link_url = (request.POST.get("link_url") or request.POST.get("file_url") or "").strip()
    upload = request.FILES.get("file")
    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"

    if (
        not module_id
        or not title
        or material_type not in {"PDF", "VIDEO", "LINK", "PPT"}
        or resource_type not in {"REQUIRED", "RECOMMENDED", "RESOURCES"}
    ):
        if is_ajax:
            return JsonResponse({"success": False, "error": "Invalid material data."}, status=400)
        return course_materials_panel(request)

    module = get_object_or_404(Module, id=module_id)
    if request.user.role == "FACULTY" and not ModuleRun.objects.filter(module=module, faculty=request.user).exists():
        if is_ajax:
            return JsonResponse({"success": False, "error": "You do not have permission to upload materials for this module."}, status=403)
        return course_materials_panel(request)

    if material_type == "LINK":
        if not link_url:
            if is_ajax:
                return JsonResponse({"success": False, "error": "Link URL is required."}, status=400)
            return course_materials_panel(request)
        CourseMaterial.objects.create(
            module=module,
            title=title,
            file_url=link_url,
            material_type=material_type,
            resource_type=resource_type,
            uploaded_by=request.user,
        )
    else:
        if not upload:
            if is_ajax:
                return JsonResponse({"success": False, "error": "A file is required."}, status=400)
            return course_materials_panel(request)
        CourseMaterial.objects.create(
            module=module,
            title=title,
            file_url=upload,
            material_type=material_type,
            resource_type=resource_type,
            uploaded_by=request.user,
        )

    if is_ajax:
        return JsonResponse({"success": True})

    # Preserve module filter after submit.
    request.GET = request.GET.copy()
    request.GET["module_id"] = module_id
    return course_materials_panel(request)


@login_required
@admin_or_faculty_required
def delete_course_material(request, material_id):
    if request.method != "POST":
        return redirect("home")

    is_ajax = request.headers.get("x-requested-with") == "XMLHttpRequest"
    try:
        material = get_object_or_404(CourseMaterial, id=material_id)

        if request.user.role == "FACULTY" and not ModuleRun.objects.filter(
            module_id=material.module_id,
            faculty_id=request.user.id,
        ).exists():
            if is_ajax:
                return JsonResponse({"success": False, "error": f"Faculty {request.user.id} is not assigned to module {material.module_id} for this material."}, status=403)
            return course_materials_panel(request)

        module_id = str(material.module_id)
        material.delete()

        if is_ajax:
            return JsonResponse({"success": True, "module_id": module_id})
    except Exception as exc:
        if is_ajax:
            return JsonResponse({"success": False, "error": str(exc)}, status=500)
        raise

    request.GET = request.GET.copy()
    request.GET["module_id"] = module_id
    return course_materials_panel(request)


@login_required
@admin_or_faculty_required
def module_assignments_panel(request, module_run_id):
    module_run = get_object_or_404(ModuleRun.objects.select_related("module"), id=module_run_id)
    if request.user.role == "FACULTY" and module_run.faculty_id != request.user.id:
        return redirect("faculty_home")
    
    # Check if viewing a specific assignment (from faculty assignments page)
    view_assignment_id = request.GET.get("view_assignment_id")
    
    if view_assignment_id:
        # Show only the specific assignment
        assignments = (
            Assignment.objects.filter(module_run=module_run, id=view_assignment_id)
            .select_related("created_by", "module", "module_run")
            .prefetch_related("files")
            .order_by("-due_date", "-id")
        )
    else:
        # Show all assignments for the module
        assignments = (
            Assignment.objects.filter(module_run=module_run)
            .select_related("created_by", "module", "module_run")
            .prefetch_related("files")
            .order_by("-due_date", "-id")
        )
    assignment_files = AssignmentFile.objects.filter(
        assignment__module_run=module_run
    ).select_related("assignment", "uploaded_by").order_by("-uploaded_at")
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
    
    # Fetch course materials for the module, separated by resource type
    required_materials = CourseMaterial.objects.filter(
        module=module_run.module,
        resource_type="REQUIRED"
    ).select_related("uploaded_by").order_by("-created_at")
    
    recommended_materials = CourseMaterial.objects.filter(
        module=module_run.module,
        resource_type="RECOMMENDED"
    ).select_related("uploaded_by").order_by("-created_at")

    resource_materials = CourseMaterial.objects.filter(
        module=module_run.module,
        resource_type="RESOURCES"
    ).select_related("uploaded_by").order_by("-created_at")
    
    # Combine all course materials for the readings tab
    course_materials = CourseMaterial.objects.filter(
        module=module_run.module
    ).select_related("uploaded_by").order_by("-created_at")
    
    # Check if this is being called from faculty assignments page
    from_faculty_assignments = request.GET.get("from_faculty_assignments") == "true"
    
    context = {
        "module_run": module_run,
        "assignments": assignments,
        "assignment_files": assignment_files,
        "editing_assignment": editing_assignment,
        "student_modules": student_modules,
        "submissions_by_assignment": submissions_by_assignment,
        "percentage_by_assignment": percentage_by_assignment,
        "required_materials": required_materials,
        "recommended_materials": recommended_materials,
        "resource_materials": resource_materials,
        "course_materials": course_materials,
        "from_faculty_assignments": from_faculty_assignments,
    }
    if request.headers.get("HX-Request") == "true" and editing_assignment:
        return render(
            request,
            "accounts/home/panels/modules/_assignment_form.html",
            context,
        )
    
    if from_faculty_assignments:
        return render(
            request,
            "accounts/faculty/panels/modules/_assignments_detail.html",
            context,
        )
    
    return render(
        request,
        "accounts/home/panels/modules/_assignments.html",
        context,
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
    status = request.POST.get("status", "DRAFT")  # Default to DRAFT if not provided

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
        status=status,
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

    # Check if this is from faculty assignments page
    from_faculty_assignments = request.GET.get("from_faculty_assignments") == "true"
    
    if from_faculty_assignments and request.user.role == "FACULTY":
        # Return the full assignments panel with updated data
        faculty_runs = (
            ModuleRun.objects.filter(faculty=request.user)
            .select_related("module", "quarter", "quarter__academic_year")
            .prefetch_related("sessions")
            .order_by("-created_at")
        )
        faculty_assignments = (
            Assignment.objects.filter(module_run__in=faculty_runs)
            .select_related("module_run", "module_run__module")
            .order_by("-due_date")
        )
        return render(
            request,
            "accounts/faculty/panels/_assignments.html",
            {
                "active_tab": "assignments",
                "faculty_runs": faculty_runs,
                "faculty_assignments": faculty_assignments,
            },
        )
    
    return module_assignments_panel(request, module_run_id=module_run_id)


@login_required
@admin_or_faculty_required
def delete_module_assignment(request, module_run_id, assignment_id):
    if request.method not in ["POST", "DELETE"]:
        return redirect("home")

    assignment = get_object_or_404(Assignment, id=assignment_id, module_run_id=module_run_id)
    if request.user.role == "FACULTY" and assignment.module_run.faculty_id != request.user.id:
        return redirect("faculty_home")
    assignment.delete()
    
    # Check if this is from faculty assignments page
    from_faculty_assignments = request.GET.get("from_faculty_assignments") == "true"
    
    if from_faculty_assignments and request.user.role == "FACULTY":
        # Return the full assignments panel with updated data
        faculty_runs = (
            ModuleRun.objects.filter(faculty=request.user)
            .select_related("module", "quarter", "quarter__academic_year")
            .prefetch_related("sessions")
            .order_by("-created_at")
        )
        faculty_assignments = (
            Assignment.objects.filter(module_run__in=faculty_runs)
            .select_related("module_run", "module_run__module")
            .order_by("-due_date")
        )
        return render(
            request,
            "accounts/faculty/panels/_assignments.html",
            {
                "active_tab": "assignments",
                "faculty_runs": faculty_runs,
                "faculty_assignments": faculty_assignments,
            },
        )
    
    return module_assignments_panel(request, module_run_id=module_run_id)


@login_required
@admin_or_faculty_required
def delete_assignment_file(request, module_run_id, file_id):
    if request.method != "POST":
        return redirect("home")

    assignment_file = get_object_or_404(
        AssignmentFile.objects.select_related("assignment", "assignment__module_run"),
        id=file_id,
        assignment__module_run_id=module_run_id,
    )
    if request.user.role == "FACULTY" and assignment_file.assignment.module_run.faculty_id != request.user.id:
        return redirect("faculty_home")

    if assignment_file.file_url:
        assignment_file.file_url.delete(save=False)
    assignment_file.delete()
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

    # Check if this is from faculty assignments page
    from_faculty_assignments = request.GET.get("from_faculty_assignments") == "true"
    
    if from_faculty_assignments and request.user.role == "FACULTY":
        # Return the full assignments panel with updated data
        faculty_runs = (
            ModuleRun.objects.filter(faculty=request.user)
            .select_related("module", "quarter", "quarter__academic_year")
            .prefetch_related("sessions")
            .order_by("-created_at")
        )
        faculty_assignments = (
            Assignment.objects.filter(module_run__in=faculty_runs)
            .select_related("module_run", "module_run__module")
            .order_by("-due_date")
        )
        return render(
            request,
            "accounts/faculty/panels/_assignments.html",
            {
                "active_tab": "assignments",
                "faculty_runs": faculty_runs,
                "faculty_assignments": faculty_assignments,
            },
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


@login_required
@faculty_required
def faculty_assignment_detail_view(request, assignment_id):
    """
    Display a comprehensive assignment view panel for faculty.
    Shows module information with tabs for assignments and readings.
    Renders as a panel fragment within the faculty home page.
    """
    assignment = get_object_or_404(
        Assignment.objects.select_related(
            'module_run',
            'module_run__module',
            'module_run__quarter',
            'module_run__faculty'
        ).prefetch_related('files'),
        id=assignment_id,
        module_run__faculty=request.user
    )
    
    module_run = assignment.module_run
    
    # Get course materials for readings tab
    required_materials = CourseMaterial.objects.filter(
        module=module_run.module,
        resource_type='REQUIRED'
    ).select_related('uploaded_by').order_by('-created_at')
    
    recommended_materials = CourseMaterial.objects.filter(
        module=module_run.module,
        resource_type='RECOMMENDED'
    ).select_related('uploaded_by').order_by('-created_at')
    
    # Check if this is an HTMX request
    is_htmx = request.headers.get('HX-Request') == 'true'
    
    context = {
        'assignments': [assignment],
        'module_run': module_run,
        'required_materials': required_materials,
        'recommended_materials': recommended_materials,
    }
    
    if is_htmx:
        # Return just the panel fragment for HTMX requests
        return render(request, 'accounts/faculty/panels/_assignment_detail_page.html', context)
    else:
        # Return full page with faculty home structure for direct navigation
        return render(request, 'accounts/faculty/home.html', {
            **context,
            'active_tab': 'assignments',
        })
    return module_assignments_panel(request, module_run_id=str(assignment.module_run_id))


@faculty_required
def module_run_readings(request, module_run_id):
    """
    Load readings content for a specific module run.
    Used for AJAX loading in the faculty assignments add page.
    """
    module_run = get_object_or_404(
        ModuleRun.objects.select_related('module', 'quarter', 'quarter__academic_year'),
        id=module_run_id,
        faculty=request.user
    )
    
    # Get course materials for this module
    required_materials = CourseMaterial.objects.filter(
        module=module_run.module,
        resource_type='REQUIRED'
    ).order_by('-created_at')
    
    recommended_materials = CourseMaterial.objects.filter(
        module=module_run.module,
        resource_type='RECOMMENDED'
    ).order_by('-created_at')
    
    context = {
        'module_run': module_run,
        'required_materials': required_materials,
        'recommended_materials': recommended_materials,
    }
    
    return render(request, 'accounts/shared/_readings_tab.html', context)


@faculty_required
def faculty_assignment_detail_ajax(request, assignment_id):
    """
    Load assignment details for AJAX request.
    Returns JSON with assignment info and readings HTML.
    """
    assignment = get_object_or_404(
        Assignment.objects.select_related('module_run', 'module_run__module', 'module_run__quarter', 'module_run__faculty'),
        id=assignment_id,
        module_run__faculty=request.user
    )
    
    # Get assignment files
    assignment_files = AssignmentFile.objects.filter(assignment=assignment).order_by('uploaded_at')
    
    # Get course materials for this module
    required_materials = CourseMaterial.objects.filter(
        module=assignment.module_run.module,
        resource_type='REQUIRED'
    ).order_by('-created_at')
    
    recommended_materials = CourseMaterial.objects.filter(
        module=assignment.module_run.module,
        resource_type='RECOMMENDED'
    ).order_by('-created_at')
    
    # Render assignment info HTML
    assignment_html = f'''
    <div style="display: flex; width: 956px; max-width: 100%; padding: 16px; flex-direction: column; align-items: flex-start; gap: 32px; border-radius: 16px; background: #FFF;">
      <!-- Due Date, Max Score, Status, and Action Icons -->
      <div style="display: flex; justify-content: space-between; align-items: flex-start; width: 100%; gap: 16px;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; flex: 1;">
          <div>
            <h4 style="font-size: 14px; font-weight: 600; color: #6B7280; margin: 0 0 4px 0;">Due Date</h4>
            <p style="font-size: 16px; color: #1F2937; margin: 0;">{assignment.due_date.strftime("%B %d, %Y")}</p>
          </div>
          <div>
            <h4 style="font-size: 14px; font-weight: 600; color: #6B7280; margin: 0 0 4px 0;">Max Score</h4>
            <p style="font-size: 16px; color: #1F2937; margin: 0;">{assignment.max_score}</p>
          </div>
          <div>
            <h4 style="font-size: 14px; font-weight: 600; color: #6B7280; margin: 0 0 4px 0;">Status</h4>
            {'<span class="assignment-status-badge status-draft">Draft</span>' if assignment.status == 'DRAFT' else '<span class="assignment-status-badge status-published">Published</span>'}
          </div>
        </div>
        
        <!-- Action Icons -->
        <div style="display: flex; gap: 12px; align-items: center;">
          <button
            onclick="editAssignment('{assignment.id}')"
            title="Edit Assignment"
            style="display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; background: transparent; border: none; cursor: pointer; transition: all 0.2s; padding: 0;"
            onmouseover="this.querySelector('svg path').setAttribute('fill', '#7A1A1C');"
            onmouseout="this.querySelector('svg path').setAttribute('fill', '#921F22');">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 16 16" fill="none">
              <path d="M2 11.5V14H4.5L11.8733 6.62667L9.37333 4.12667L2 11.5ZM13.8067 4.69333C14.0667 4.43333 14.0667 4.01333 13.8067 3.75333L12.2467 2.19333C11.9867 1.93333 11.5667 1.93333 11.3067 2.19333L10.0867 3.41333L12.5867 5.91333L13.8067 4.69333Z" fill="#921F22"/>
            </svg>
          </button>
          <button
            onclick="deleteAssignment('{assignment.id}')"
            title="Delete Assignment"
            style="display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; background: transparent; border: none; cursor: pointer; transition: all 0.2s; padding: 0;"
            onmouseover="this.querySelector('svg path').setAttribute('fill', '#7A1A1C');"
            onmouseout="this.querySelector('svg path').setAttribute('fill', '#921F22');">
            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 16 16" fill="none">
              <path d="M4 12.6667C4 13.4 4.6 14 5.33333 14H10.6667C11.4 14 12 13.4 12 12.6667V4.66667H4V12.6667ZM12.6667 2.66667H10.3333L9.66667 2H6.33333L5.66667 2.66667H3.33333V4H12.6667V2.66667Z" fill="#921F22"/>
            </svg>
          </button>
        </div>
      </div>
      
      <!-- Description -->
      <div style="width: 100%;">
        <h4 style="font-size: 16px; font-weight: 600; color: #1F2937; margin: 0 0 12px 0;">Description</h4>
        <div style="display: flex; height: 422px; flex-direction: column; align-items: flex-start; flex-shrink: 0; align-self: stretch; border-radius: 8px; border: 1px solid #D1D5DB; background: #FFF; padding: 16px; overflow-y: auto; color: #4B5563; line-height: 1.6;">
          {assignment.description or 'No description provided.'}
        </div>
      </div>
    '''
    
    if assignment_files.exists():
        assignment_html += '''
      <div class="assignment-card-files-box">
        <div class="assignment-card-files-header">Uploaded Assignments</div>
        <div class="assignment-card-files-list">
    '''
        for file in assignment_files:
            file_name = file.file_url.name.split('/')[-1]
            assignment_html += f'''
          <div class="resource-item">
            <div class="resource-item-icon-box">
              <svg xmlns="http://www.w3.org/2000/svg" width="25" height="25" viewBox="0 0 25 25" fill="none">
                <path d="M8.75 13.125H10V10.625H11.25C11.6042 10.625 11.901 10.5052 12.1406 10.2656C12.3802 10.026 12.5 9.72917 12.5 9.375V8.125C12.5 7.77083 12.3802 7.47396 12.1406 7.23438C11.901 6.99479 11.6042 6.875 11.25 6.875H8.75V13.125ZM10 9.375V8.125H11.25V9.375H10ZM13.75 13.125H16.25C16.6042 13.125 16.901 13.0052 17.1406 12.7656C17.3802 12.526 17.5 12.2292 17.5 11.875V8.125C17.5 7.77083 17.3802 7.47396 17.1406 7.23438C16.901 6.99479 16.6042 6.875 16.25 6.875H13.75V13.125ZM15 11.875V8.125H16.25V11.875H15ZM18.75 13.125H20V10.625H21.25V9.375H20V8.125H21.25V6.875H18.75V13.125ZM7.5 20C6.8125 20 6.22396 19.7552 5.73438 19.2656C5.24479 18.776 5 18.1875 5 17.5V2.5C5 1.8125 5.24479 1.22396 5.73438 0.734375C6.22396 0.244792 6.8125 0 7.5 0H22.5C23.1875 0 23.776 0.244792 24.2656 0.734375C24.7552 1.22396 25 1.8125 25 2.5V17.5C25 18.1875 24.7552 18.776 24.2656 19.2656C23.776 19.7552 23.1875 20 22.5 20H7.5ZM7.5 17.5H22.5V2.5H7.5V17.5ZM2.5 25C1.8125 25 1.22396 24.7552 0.734375 24.2656C0.244792 23.776 0 23.1875 0 22.5V5H2.5V22.5H20V25H2.5ZM7.5 2.5V17.5V2.5Z" fill="#921F22"/>
              </svg>
            </div>
            <span class="resource-item-title">{file_name}</span>
            <a href="{file.file_url.url}" download class="resource-item-download-icon" title="Download {file_name}">
              <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path d="M8 12L3 7L4.4 5.55L7 8.15V0H9V8.15L11.6 5.55L13 7L8 12ZM2 16C1.45 16 0.979167 15.8042 0.5875 15.4125C0.195833 15.0208 0 14.55 0 14V11H2V14H14V11H16V14C16 14.55 15.8042 15.0208 15.4125 15.4125C15.0208 15.8042 14.55 16 14 16H2Z" fill="#94A3B8"/>
              </svg>
            </a>
          </div>
    '''
        assignment_html += '''
        </div>
      </div>
    '''
    else:
        assignment_html += '''
      <div class="assignment-card-files-box">
        <div class="assignment-card-files-header">Uploaded Assignments</div>
        <div class="assignment-card-files-list">
          <div class="resources-empty-state">No assignment files uploaded yet.</div>
        </div>
      </div>
    '''
    
    assignment_html += '</div>'
    
    # Render readings HTML
    readings_context = {
        'module_run': assignment.module_run,
        'required_materials': required_materials,
        'recommended_materials': recommended_materials,
    }
    readings_html = render(request, 'accounts/shared/_readings_tab.html', readings_context).content.decode('utf-8')
    
    # Prepare files data
    files_data = []
    for file in assignment_files:
        files_data.append({
            'id': str(file.id),
            'name': file.file_url.name.split('/')[-1],
            'url': file.file_url.url
        })
    
    return JsonResponse({
        'success': True,
        'id': str(assignment.id),
        'title': assignment.title,
        'module_name': assignment.module_run.module.title,
        'due_date': assignment.due_date.strftime("%B %d, %Y"),
        'max_score': assignment.max_score,
        'description': assignment.description,
        'status': assignment.status,
        'files': files_data,
        'assignment_html': assignment_html,
        'readings_html': readings_html,
    })

@login_required
@faculty_required
def faculty_assignment_update(request, assignment_id):
    """
    Update an existing assignment
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)
    
    try:
        assignment = Assignment.objects.get(id=assignment_id, module_run__faculty=request.user)
    except Assignment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Assignment not found'}, status=404)
    
    try:
        # Validate required fields
        due_date = request.POST.get('due_date')
        max_score = request.POST.get('max_score')
        
        if not due_date:
            return JsonResponse({
                'success': False,
                'error': 'Due date is required'
            }, status=400)
        
        if not max_score:
            return JsonResponse({
                'success': False,
                'error': 'Max score is required'
            }, status=400)
        
        # Update basic fields
        assignment.due_date = due_date
        assignment.max_score = int(max_score)
        assignment.description = request.POST.get('description', '')
        assignment.status = request.POST.get('status', 'DRAFT')
        assignment.save()
        
        # Handle file uploads
        files = request.FILES.getlist('files')
        for file in files:
            AssignmentFile.objects.create(
                assignment=assignment,
                file_url=file,
                uploaded_by=request.user
            )
        
        return JsonResponse({
            'success': True,
            'message': 'Assignment updated successfully'
        })
    except ValueError as e:
        return JsonResponse({
            'success': False,
            'error': f'Invalid data format: {str(e)}'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error updating assignment: {str(e)}'
        }, status=400)
