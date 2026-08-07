"""
Report which uploaded files are missing from storage.

A file recorded in the database but absent from the Space means the record was
created while storage pointed somewhere else (e.g. before USE_SPACES was turned
on) — those files have to be re-uploaded; no permission change will bring them
back.

    python manage.py check_media_files

Add --fetch to also request each file's signed URL over plain HTTP, exactly as a
student's browser does after being redirected. That is the end-to-end proof that
downloads work: it exercises the signature, not just the stored object.

    python manage.py check_media_files --fetch
"""
import urllib.error
import urllib.request

from django.core.management.base import BaseCommand

from modules.models import AssignmentFile, AssignmentSubmission, CourseMaterial


class Command(BaseCommand):
    help = "Check that every uploaded file recorded in the database exists in storage."

    def add_arguments(self, parser):
        parser.add_argument(
            "--fetch",
            action="store_true",
            help="Also download the first byte of each file through its signed URL.",
        )

    def handle(self, *args, **options):
        fetch = options["fetch"]
        targets = (
            ("Course material", CourseMaterial.objects.select_related("module"), self._material_label),
            ("Assignment file", AssignmentFile.objects.select_related("assignment"), self._assignment_file_label),
            ("Submission", AssignmentSubmission.objects.select_related("assignment"), self._submission_label),
        )

        total = missing = links = unfetchable = 0
        for kind, queryset, label in targets:
            for obj in queryset.iterator():
                name = obj.file_url.name or ""
                if not name or name.startswith(("http://", "https://")):
                    links += 1
                    continue
                total += 1

                if not obj.file_url.storage.exists(name):
                    missing += 1
                    self.stdout.write(self.style.ERROR(f"MISSING  {kind}: {label(obj)}"))
                    self.stdout.write(f"         key: {name}")
                    continue

                if fetch:
                    error = self._fetch_error(obj.file_url)
                    if error:
                        unfetchable += 1
                        self.stdout.write(self.style.ERROR(f"UNREADABLE  {kind}: {label(obj)}"))
                        self.stdout.write(f"            key: {name}")
                        self.stdout.write(f"            {error}")

        self.stdout.write("")
        self.stdout.write(f"Checked {total} stored file(s); skipped {links} link-only record(s).")
        if missing:
            self.stdout.write(self.style.ERROR(f"{missing} file(s) missing from storage — these need re-uploading."))
        if unfetchable:
            self.stdout.write(self.style.ERROR(f"{unfetchable} file(s) present but not readable over their signed URL."))
        if not missing and not unfetchable:
            message = "All files present and downloadable." if fetch else "All files present in storage."
            self.stdout.write(self.style.SUCCESS(message))

    def _fetch_error(self, file_field):
        """Request one byte over the signed URL; return an error string, or None on success."""
        storage = file_field.storage
        if not hasattr(storage, "bucket_name"):
            return None  # Local filesystem storage — existence is all there is to check.

        url = storage.url(file_field.name)
        request = urllib.request.Request(url, headers={"Range": "bytes=0-0"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                if response.status not in (200, 206):
                    return f"unexpected status {response.status}"
        except urllib.error.HTTPError as exc:
            return f"HTTP {exc.code} {exc.reason} — {exc.read(200).decode('utf-8', 'replace')}"
        except Exception as exc:
            return f"{type(exc).__name__}: {exc}"
        return None

    @staticmethod
    def _material_label(obj):
        return f"{obj.title} ({obj.module.title})"

    @staticmethod
    def _assignment_file_label(obj):
        return f"{obj.file_name} ({obj.assignment.title})"

    @staticmethod
    def _submission_label(obj):
        return f"submission {obj.id} ({obj.assignment.title})"
