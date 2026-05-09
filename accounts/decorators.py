from django.shortcuts import redirect


def admin_required(view_func):
    def wrapper(request, *args, **kwargs):

        if not request.user.is_authenticated:
            return redirect("login")

        if request.user.role != "ADMIN":
            return redirect("login")

        return view_func(request, *args, **kwargs)

    return wrapper


def admin_or_faculty_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        if request.user.role not in {"ADMIN", "FACULTY"}:
            return redirect("login")

        return view_func(request, *args, **kwargs)

    return wrapper


def admin_or_supervisor_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        if request.user.role not in {"ADMIN", "SUPERVISOR"}:
            return redirect("login")

        return view_func(request, *args, **kwargs)

    return wrapper


def faculty_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        if request.user.role != "FACULTY":
            return redirect("login")

        return view_func(request, *args, **kwargs)

    return wrapper


def student_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("login")

        if request.user.role != "STUDENT":
            return redirect("login")

        return view_func(request, *args, **kwargs)

    return wrapper
