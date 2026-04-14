import secrets
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db.models import Prefetch
from django.urls import reverse
from .decorators import admin_required
from django.contrib import messages


from .forms import CreateUserForm
from .models import User, UserProfile
from academics.models import AcademicYear, Enrollment
from academics.models import Quarter


def _build_user_form(user=None):
    if not user:
        return CreateUserForm()

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
        enrollment, _ = Enrollment.objects.get_or_create(student=user)
        enrollment.academic_year = form.cleaned_data.get("academic_year")
        enrollment.track = form.cleaned_data.get("track")
        enrollment.start_date = form.cleaned_data.get("start_date")
        enrollment.expected_completion_date = form.cleaned_data.get("expected_completion_date")
        enrollment.save()
    else:
        Enrollment.objects.filter(student=user).delete()

    return user, generated_password


def _admin_home_context(user_form=None, active_tab="dashboard", user_panel_mode="table", editing_user=None):
    users = User.objects.all().order_by("-created_at")
    academic_years = AcademicYear.objects.all().prefetch_related(
        Prefetch("quarter_set", queryset=Quarter.objects.all().order_by("quarter_number"))
    ).order_by("-start_date")

    return {
        "users": users,
        "academic_years": academic_years,
        "user_form": user_form or CreateUserForm(),
        "active_tab": active_tab,
        "user_panel_mode": user_panel_mode,
        "editing_user": editing_user,
    }

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
    user_panel_mode = request.GET.get("mode", "table") if active_tab == "users" else "table"
    editing_user = None

    if active_tab == "users" and user_panel_mode == "edit":
        editing_user = get_object_or_404(User, id=request.GET.get("user_id"), role__in=["STUDENT", "FACULTY", "SUPERVISOR"])
        user_form = _build_user_form(editing_user)
    else:
        user_form = CreateUserForm()

    if request.method == "POST" and active_tab == "users":
        user_panel_mode = request.GET.get("mode", "create")
        user_id = request.GET.get("user_id")
        editing_user = None

        if user_panel_mode == "edit" and user_id:
            editing_user = get_object_or_404(User, id=user_id, role__in=["STUDENT", "FACULTY", "SUPERVISOR"])

        user_form = CreateUserForm(request.POST)
        if user_form.is_valid():
            saved_user, generated_password = _save_user_from_form(user_form, editing_user)

            if generated_password:
                messages.success(request, f"User created. Password: {generated_password}")
            else:
                messages.success(request, f"User updated for {saved_user.first_name} {saved_user.last_name}.")

            return redirect(f"{reverse('home')}?tab=users")

    return render(request, "accounts/home.html", _admin_home_context(
        user_form=user_form,
        active_tab=active_tab,
        user_panel_mode=user_panel_mode,
        editing_user=editing_user,
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
