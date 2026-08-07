"""
Permission-checked downloads for files kept in object storage.

Objects in DigitalOcean Spaces are private, so linking a browser straight at the
bucket URL returns AccessDenied. Every download goes through these views
instead: they check that the requesting user is allowed to see the file, then
redirect to a short-lived signed URL (or stream the file directly when the
storage backend is the local filesystem, i.e. in development).
"""
import os
import re

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404

from .models import (
    AssignmentFile,
    AssignmentSubmission,
    CourseMaterial,
    ModuleRun,
    StudentModule,
)

# Content-Disposition filenames are quoted, so keep them to plain ASCII.
UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._ ()\[\]-]")


def _is_staff_viewer(user):
    """Admins and supervisors can read every file."""
    return user.role in ("ADMIN", "SUPERVISOR")


def _can_access_module(user, module):
    """Files attached to a module: teachers of any run, plus enrolled students."""
    if _is_staff_viewer(user):
        return True
    if user.role == "FACULTY":
        return ModuleRun.objects.filter(module=module, faculty=user).exists()
    return StudentModule.objects.filter(
        module_run__module=module,
        enrollment__student=user,
    ).exists()


def _can_access_run(user, module_run):
    """Files attached to a specific run: its faculty, plus students in that run."""
    if _is_staff_viewer(user):
        return True
    if user.role == "FACULTY":
        return module_run.faculty_id == user.id
    return StudentModule.objects.filter(
        module_run=module_run,
        enrollment__student=user,
    ).exists()


def _download_name(preferred_title, stored_name):
    """Name the browser saves the file as: the record's title, real extension."""
    extension = os.path.splitext(stored_name)[1]
    base = preferred_title or os.path.splitext(os.path.basename(stored_name))[0]
    if extension and base.lower().endswith(extension.lower()):
        extension = ""
    return UNSAFE_FILENAME_CHARS.sub("_", f"{base}{extension}").strip() or "download"


def _external_url(raw):
    """LINK materials store a bare URL, sometimes without a scheme."""
    raw = (raw or "").strip()
    if not raw:
        raise Http404("This link is empty.")
    if not raw.startswith(("http://", "https://")):
        raw = f"https://{raw}"
    return raw


def _file_response(request, file_field, preferred_title):
    """
    Hand the file to the browser.

    Pass ?inline=1 to display it in place (video players, PDF preview tabs)
    rather than forcing a save dialog.
    """
    stored_name = getattr(file_field, "name", "") or ""
    if not stored_name:
        raise Http404("File is not available.")

    # LINK-type records keep a plain URL in the FileField instead of a file.
    if stored_name.startswith(("http://", "https://")):
        return HttpResponseRedirect(stored_name)

    inline = request.GET.get("inline") == "1"
    disposition = "inline" if inline else "attachment"
    filename = _download_name(preferred_title, stored_name)

    storage = file_field.storage
    if hasattr(storage, "bucket_name"):
        # S3-compatible storage (DigitalOcean Spaces): redirect to a signed URL
        # that expires after AWS_QUERYSTRING_EXPIRE seconds.
        signed_url = storage.url(
            stored_name,
            parameters={"ResponseContentDisposition": f'{disposition}; filename="{filename}"'},
        )
        response = HttpResponseRedirect(signed_url)
        # The signature expires, so no proxy or CDN may hand this redirect to a
        # later visitor — they would get a dead URL.
        response["Cache-Control"] = "private, no-store"
        return response

    try:
        handle = file_field.open("rb")
    except (FileNotFoundError, ValueError):
        raise Http404("File is missing from storage.")
    return FileResponse(handle, as_attachment=not inline, filename=filename)


@login_required
def download_course_material(request, material_id):
    material = get_object_or_404(
        CourseMaterial.objects.select_related("module"),
        id=material_id,
    )
    if not _can_access_module(request.user, material.module):
        raise PermissionDenied("You do not have access to this course material.")
    if material.material_type == "LINK":
        return HttpResponseRedirect(_external_url(material.file_url.name))
    return _file_response(request, material.file_url, material.title)


@login_required
def download_assignment_file(request, file_id):
    assignment_file = get_object_or_404(
        AssignmentFile.objects.select_related("assignment__module_run"),
        id=file_id,
    )
    if not _can_access_run(request.user, assignment_file.assignment.module_run):
        raise PermissionDenied("You do not have access to this assignment file.")
    return _file_response(request, assignment_file.file_url, assignment_file.file_name)


@login_required
def download_assignment_submission(request, submission_id):
    submission = get_object_or_404(
        AssignmentSubmission.objects.select_related(
            "assignment__module_run",
            "student_module__enrollment",
        ),
        id=submission_id,
    )
    user = request.user
    module_run = submission.assignment.module_run
    is_owner = submission.student_module.enrollment.student_id == user.id
    if not (is_owner or _is_staff_viewer(user) or module_run.faculty_id == user.id):
        raise PermissionDenied("You do not have access to this submission.")
    # Submissions have no title of their own — keep the student's own filename.
    return _file_response(request, submission.file_url, None)
