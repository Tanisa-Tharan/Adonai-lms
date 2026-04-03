import secrets
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from .decorators import admin_required
from django.contrib import messages


from .forms import CreateUserForm
from .models import User, UserProfile
from academics.models import AcademicYear, Enrollment


@login_required
@admin_required
def create_user(request):

    if request.method == "POST":

        form = CreateUserForm(request.POST)

        if form.is_valid():

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

            # store success message
            messages.success(request, f"User created. Password: {password}")

            # redirect (clears form)
            return redirect("create_user")

    else:
        form = CreateUserForm()

    return render(request, "accounts/create_user.html", {"form": form})

def login_view(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

        if user:
            login(request, user)

            # Redirect after login
            if user.role == "ADMIN":
                return redirect("dashboard")

    return render(request, "accounts/login.html")

@login_required
@admin_required
def dashboard(request):

    users = User.objects.all().order_by("-created_at")
    
    academic_years = AcademicYear.objects.all().order_by("-start_date")

    return render(request, "accounts/dashboard.html", {
        "users": users,
        "academic_years": academic_years,
    })

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
        return redirect("dashboard")

    return redirect("dashboard")