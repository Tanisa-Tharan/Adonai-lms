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


def _create_user_from_form(form):
    password = secrets.token_urlsafe(8)

    user = User.objects.create(
        email=form.cleaned_data["email"],
        first_name=form.cleaned_data["first_name"],
        last_name=form.cleaned_data["last_name"],
        role=form.cleaned_data["role"],
        is_active=True,
    )
    user.set_password(password)
    user.save()

    UserProfile.objects.create(
        user=user,
        phone=form.cleaned_data.get("phone"),
        address=form.cleaned_data.get("address"),
        dob=form.cleaned_data.get("dob"),
    )

    if user.role == "STUDENT":
        Enrollment.objects.create(
            student=user,
            academic_year=form.cleaned_data.get("academic_year"),
            track=form.cleaned_data.get("track"),
            start_date=form.cleaned_data.get("start_date"),
            expected_completion_date=form.cleaned_data.get("expected_completion_date"),
        )

    return password


def _admin_home_context(user_form=None, active_tab="dashboard", user_panel_mode="table"):
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
    }


@login_required
@admin_required
def create_user(request):

    if request.method == "POST":

        form = CreateUserForm(request.POST)

        if form.is_valid():
            password = _create_user_from_form(form)

            # store success message
            messages.success(request, f"User created. Password: {password}")

            # redirect (clears form)
            return redirect("create_user")

    else:
        form = CreateUserForm()

    return render(request, "accounts/create_user.html", {
        "form": form,
        "page_title": "Create User",
        "submit_label": "Create User",
        "back_url": "home",
    })


@login_required
@admin_required
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
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

    if request.method == "POST":
        form = CreateUserForm(request.POST)

        if form.is_valid():
            user.email = form.cleaned_data["email"]
            user.first_name = form.cleaned_data["first_name"]
            user.last_name = form.cleaned_data["last_name"]
            user.role = form.cleaned_data["role"]
            user.save()

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

            messages.success(request, "User updated successfully.")
            return redirect("home")
    else:
        form = CreateUserForm(initial=initial)

    return render(request, "accounts/create_user.html", {
        "form": form,
        "page_title": "Edit User",
        "submit_label": "Update User",
        "back_url": "home",
        "editing_user": user,
    })

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
    user_panel_mode = "create" if request.GET.get("mode") == "create" else "table"
    user_form = CreateUserForm()

    if request.method == "POST" and request.POST.get("form_name") == "inline_create_user":
        user_form = CreateUserForm(request.POST)
        active_tab = "users"
        user_panel_mode = "create"

        if user_form.is_valid():
            password = _create_user_from_form(user_form)
            messages.success(request, f"User created. Password: {password}")
            return redirect(f"{reverse('home')}?tab=users")

    return render(
        request,
        "accounts/home.html",
        _admin_home_context(
            user_form=user_form,
            active_tab=active_tab,
            user_panel_mode=user_panel_mode,
        ),
    )

@login_required
@admin_required
def dashboard(request):
    return render(request, "accounts/dashboard.html", _admin_home_context())

def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
@admin_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == "POST":
        user.delete()
    
    if user == request.user:
        return redirect("home")

    return redirect("home")
