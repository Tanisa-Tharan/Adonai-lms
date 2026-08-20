"""
Module marks: the one place a student's grade is worked out.

A module's mark is its published assignments plus, where the faculty awards them,
an attendance mark and a participation mark. Where a faculty does not award a
component it is *not applicable* — it counts toward neither what the student earned
nor what was available, and is never silently treated as a zero.

Nothing here is cached. Grades are computed when they are read, so they cannot go
stale when an assignment is added, a max score is edited, or a mark is changed.
"""
from modules.models import Assignment, AssignmentSubmission

# What a row in the breakdown can be.
STATE_GRADED = "graded"        # marked, counts toward earned and possible
STATE_PENDING = "pending"      # awaiting marking, counts toward neither
STATE_UNMARKED = "unmarked"    # component in use, student not marked yet
STATE_NA = "na"                # faculty does not award this component


def _component_row(kind, label, mark, max_score):
    """One attendance/participation row, resolving the three-state N/A semantics."""
    if max_score is None or max_score <= 0:
        return {"kind": kind, "label": label, "state": STATE_NA,
                "earned": None, "possible": None, "counts": False}
    if mark is None:
        return {"kind": kind, "label": label, "state": STATE_UNMARKED,
                "earned": None, "possible": max_score, "counts": False}
    return {"kind": kind, "label": label, "state": STATE_GRADED,
            "earned": mark, "possible": max_score, "counts": True}


def build_grade_summaries(student_modules, as_of=None):
    """
    Work out the breakdown and module total for many students at once.

    Two extra queries regardless of roster size, so this can be called on a whole
    faculty dashboard. Callers should keep select_related("module_run").

    Returns {str(student_module_id): summary}, where summary has:
        items       - one row per assignment, then attendance, then participation
        earned      - marks awarded across the rows that count
        possible    - marks available across the rows that count
        percentage  - earned/possible as a percentage, or None when nothing counts
        graded_count / total_count - for the "based on N of M" caption
    """
    student_modules = list(student_modules)
    if not student_modules:
        return {}

    run_ids = {sm.module_run_id for sm in student_modules}

    # Drafts are invisible to students, so counting them would deflate a total for
    # work nobody can see.
    assignments = list(
        Assignment.objects.filter(module_run_id__in=run_ids, status="PUBLISHED")
        .order_by("serial_number", "due_date")
    )
    assignments_by_run = {}
    for assignment in assignments:
        assignments_by_run.setdefault(str(assignment.module_run_id), []).append(assignment)

    scores = {}
    for submission in AssignmentSubmission.objects.filter(
        student_module__in=student_modules
    ).only("assignment_id", "student_module_id", "score"):
        scores[(str(submission.student_module_id), str(submission.assignment_id))] = submission.score

    summaries = {}
    for student_module in student_modules:
        module_run = student_module.module_run
        items = []
        earned = 0.0
        possible = 0.0
        graded_count = 0

        for assignment in assignments_by_run.get(str(student_module.module_run_id), []):
            max_score = assignment.max_score or 0
            score = scores.get((str(student_module.id), str(assignment.id)))
            if max_score <= 0:
                # Guards the division, and matches the existing max_score > 0 checks.
                continue
            if score is None:
                # Not submitted, or submitted and not yet marked. Counting it as zero
                # would make every student look like they were failing mid-module.
                items.append({"kind": "assignment", "label": assignment.title,
                              "state": STATE_PENDING, "earned": None,
                              "possible": max_score, "counts": False})
                continue
            items.append({"kind": "assignment", "label": assignment.title,
                          "state": STATE_GRADED, "earned": score,
                          "possible": max_score, "counts": True})
            earned += score
            possible += max_score
            graded_count += 1

        for kind, label, mark, max_score in (
            ("attendance", "Attendance",
             student_module.attendance_mark, module_run.attendance_max_score),
            ("participation", "Participation",
             student_module.participation_mark, module_run.participation_max_score),
        ):
            row = _component_row(kind, label, mark, max_score)
            items.append(row)
            if row["counts"]:
                earned += row["earned"]
                possible += row["possible"]
                graded_count += 1

        counted_total = sum(1 for item in items if item["state"] != STATE_NA)
        assignment_items = [i for i in items if i["kind"] == "assignment"]
        assignments_graded = sum(1 for i in assignment_items if i["state"] == STATE_GRADED)
        summaries[str(student_module.id)] = {
            "items": items,
            "earned": earned,
            "possible": possible,
            "percentage": (earned / possible * 100.0) if possible > 0 else None,
            "graded_count": graded_count,
            "total_count": counted_total,
            # A student is only "graded" once every published assignment is marked;
            # one marked assignment out of eight is grading in progress, not done.
            "assignments_total": len(assignment_items),
            "assignments_graded": assignments_graded,
            "all_assignments_graded": bool(assignment_items) and assignments_graded == len(assignment_items),
        }

    return summaries


def parse_score(raw, max_score, label="Score"):
    """
    Turn a typed score into a number, or explain why it can't be one.

    Every marking surface uses this so the same rules apply everywhere: a score
    must be a number, cannot be negative, and cannot exceed what the assignment is
    marked out of. Out-of-range values are refused rather than clamped — silently
    storing a different number than the faculty typed is worse than rejecting it.

    Blank clears the mark back to "not graded yet".

    Returns (value_or_None, error_or_None).
    """
    if raw is None:
        return None, None
    raw = str(raw).strip()
    if raw == "":
        return None, None

    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None, f"{label} must be a number."

    if value < 0:
        return None, f"{label} cannot be negative."

    if max_score is not None and value > float(max_score):
        return None, f"{label} cannot be more than {max_score}."

    return value, None


def build_faculty_student_flags(submissions, faculty_user):
    """
    Submission state per student-module, for the faculty dashboard.

    Lifted verbatim out of faculty_home and faculty_students_panel, which each held
    their own byte-identical copy.
    """
    has_submission = set()
    graded = set()
    next_ungraded_assignment = {}

    for submission in submissions:
        key = str(submission.student_module_id)
        has_submission.add(key)
        if submission.graded_by_id == faculty_user.id or submission.score is not None:
            graded.add(key)
        if (submission.score is None and submission.graded_by_id is None
                and key not in next_ungraded_assignment):
            next_ungraded_assignment[key] = str(submission.assignment_id)

    return has_submission, graded, next_ungraded_assignment


def apply_module_marks(student_module, post_data, prefix=""):
    """
    Validate and write attendance/participation marks onto a StudentModule.

    Every surface that can set these marks goes through here — the class grading
    sheet, the per-student grade drawer, and the faculty JSON grading endpoint — so
    the range checks and the meaning of "clear this mark" cannot drift apart.

    An empty value clears the mark back to "not marked yet". A component the module
    does not award is ignored entirely. Out-of-range and non-numeric values are
    rejected rather than clamped, because silently storing a different number than
    the faculty typed is worse than refusing it.

    Returns (changed_fields, errors). The caller saves; this never writes.
    """
    module_run = student_module.module_run
    changed = []
    errors = []

    for kind, field, max_score, in_use in (
        ("attendance", "attendance_mark",
         module_run.attendance_max_score, module_run.uses_attendance_mark),
        ("participation", "participation_mark",
         module_run.participation_max_score, module_run.uses_participation_mark),
    ):
        key = f"{prefix}{kind}"
        if key not in post_data or not in_use:
            continue

        raw = (post_data.get(key) or "").strip()
        if raw == "":
            if getattr(student_module, field) is not None:
                setattr(student_module, field, None)
                changed.append(field)
            continue

        try:
            value = float(raw)
        except (TypeError, ValueError):
            errors.append(f"{kind.title()} mark must be a number.")
            continue

        if value < 0 or value > max_score:
            errors.append(f"{kind.title()} mark must be between 0 and {max_score}.")
            continue

        if getattr(student_module, field) != value:
            setattr(student_module, field, value)
            changed.append(field)

    return changed, errors
