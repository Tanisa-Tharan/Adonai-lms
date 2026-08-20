"""
Tests for the module mark calculation.

build_grade_summaries decides what every student is told their grade is, so each
of its states is pinned here — especially the two that are easy to get wrong: a
mark of zero (which must count) and a component the faculty does not award (which
must not).
"""
import datetime

from django.test import TestCase
from django.utils import timezone

from academics.models import AcademicYear, Enrollment, Quarter
from accounts.models import User
from modules.grading import apply_module_marks, build_grade_summaries, parse_score
from modules.models import (
    Assignment,
    AssignmentSubmission,
    Module,
    ModuleRun,
    StudentModule,
)


class GradeSummaryTests(TestCase):
    def setUp(self):
        today = datetime.date.today()
        self.faculty = User.objects.create_user(
            email="f@test.local", password="x", first_name="F", last_name="Ac",
            role="FACULTY")
        student = User.objects.create_user(
            email="s@test.local", password="x", first_name="S", last_name="Tu",
            role="STUDENT")
        year = AcademicYear.objects.create(
            name="2026", start_date=today, end_date=today + datetime.timedelta(days=365))
        quarter = Quarter.objects.create(
            academic_year=year, name="Q1", quarter_number=1, start_date=today,
            end_date=today + datetime.timedelta(days=90), type="MODULE")
        module = Module.objects.create(title="Theology", order_number=1)
        self.run = ModuleRun.objects.create(
            module=module, quarter=quarter, faculty=self.faculty, start_date=today,
            end_date=today + datetime.timedelta(days=90), max_students=30, status="RUNNING")
        enrollment = Enrollment.objects.create(
            student=student, academic_year=year, track="DIPLOMA", start_date=today,
            expected_completion_date=today + datetime.timedelta(days=365), status="ACTIVE")
        self.student_module = StudentModule.objects.create(
            enrollment=enrollment, module_run=self.run)

    def _assignment(self, title, max_score=10, status="PUBLISHED"):
        return Assignment.objects.create(
            module=self.run.module, module_run=self.run, title=title,
            due_date=timezone.now() + datetime.timedelta(days=7),
            max_score=max_score, status=status, created_by=self.faculty)

    def summary(self):
        student_module = StudentModule.objects.select_related("module_run").get(
            id=self.student_module.id)
        return build_grade_summaries([student_module])[str(student_module.id)]

    def state_of(self, summary, label):
        return next(i["state"] for i in summary["items"] if i["label"] == label)

    # --- components -------------------------------------------------------

    def test_components_are_na_by_default(self):
        """A brand new run awards neither component, so both read N/A."""
        summary = self.summary()
        self.assertEqual(self.state_of(summary, "Attendance"), "na")
        self.assertEqual(self.state_of(summary, "Participation"), "na")
        self.assertEqual(summary["possible"], 0)
        self.assertIsNone(summary["percentage"])

    def test_na_component_is_not_a_zero(self):
        """N/A must not drag the total down: it leaves both sides untouched."""
        assignment = self._assignment("A1", max_score=10)
        AssignmentSubmission.objects.create(
            assignment=assignment, student_module=self.student_module, score=8)
        summary = self.summary()
        self.assertEqual(summary["earned"], 8)
        self.assertEqual(summary["possible"], 10)
        self.assertAlmostEqual(summary["percentage"], 80.0)

    def test_configured_but_unmarked_counts_toward_neither_side(self):
        self.run.attendance_max_score = 10
        self.run.save()
        summary = self.summary()
        self.assertEqual(self.state_of(summary, "Attendance"), "unmarked")
        self.assertEqual(summary["possible"], 0)

    def test_zero_is_a_real_mark(self):
        """A zero counts, and keeps its denominator — it is not 'unmarked'."""
        self.run.attendance_max_score = 10
        self.run.save()
        self.student_module.attendance_mark = 0
        self.student_module.save()
        summary = self.summary()
        self.assertEqual(self.state_of(summary, "Attendance"), "graded")
        self.assertEqual(summary["earned"], 0)
        self.assertEqual(summary["possible"], 10)
        self.assertEqual(summary["percentage"], 0.0)

    def test_marked_components_add_to_the_total(self):
        self.run.attendance_max_score = 10
        self.run.participation_max_score = 5
        self.run.save()
        self.student_module.attendance_mark = 8
        self.student_module.participation_mark = 5
        self.student_module.save()
        summary = self.summary()
        self.assertEqual(summary["earned"], 13)
        self.assertEqual(summary["possible"], 15)

    # --- assignments ------------------------------------------------------

    def test_draft_assignments_are_excluded(self):
        self._assignment("Draft one", status="DRAFT")
        summary = self.summary()
        labels = [item["label"] for item in summary["items"]]
        self.assertNotIn("Draft one", labels)

    def test_ungraded_assignment_counts_toward_neither_side(self):
        assignment = self._assignment("A1", max_score=10)
        AssignmentSubmission.objects.create(
            assignment=assignment, student_module=self.student_module, score=None)
        summary = self.summary()
        self.assertEqual(self.state_of(summary, "A1"), "pending")
        self.assertEqual(summary["possible"], 0)

    def test_assignment_with_zero_max_is_skipped(self):
        """Guards the division rather than raising."""
        self._assignment("Zero max", max_score=0)
        summary = self.summary()
        self.assertNotIn("Zero max", [item["label"] for item in summary["items"]])
        self.assertIsNone(summary["percentage"])

    # --- writing marks ----------------------------------------------------

    def test_apply_module_marks_rejects_out_of_range(self):
        self.run.attendance_max_score = 10
        self.run.save()
        student_module = StudentModule.objects.select_related("module_run").get(
            id=self.student_module.id)
        changed, errors = apply_module_marks(student_module, {"attendance": "11"})
        self.assertEqual(changed, [])
        self.assertTrue(errors)
        self.assertIsNone(student_module.attendance_mark)

    def test_apply_module_marks_clears_on_blank(self):
        self.run.attendance_max_score = 10
        self.run.save()
        student_module = StudentModule.objects.select_related("module_run").get(
            id=self.student_module.id)
        student_module.attendance_mark = 7
        changed, errors = apply_module_marks(student_module, {"attendance": ""})
        self.assertEqual(errors, [])
        self.assertIn("attendance_mark", changed)
        self.assertIsNone(student_module.attendance_mark)

    def test_apply_module_marks_ignores_components_not_in_use(self):
        student_module = StudentModule.objects.select_related("module_run").get(
            id=self.student_module.id)
        changed, errors = apply_module_marks(student_module, {"participation": "3"})
        self.assertEqual(changed, [])
        self.assertEqual(errors, [])
        self.assertIsNone(student_module.participation_mark)


class ScoreValidationTests(TestCase):
    """parse_score is the single gate every marking surface passes through."""

    def test_accepts_a_score_within_range(self):
        self.assertEqual(parse_score("8", 20), (8.0, None))

    def test_accepts_the_maximum_itself(self):
        self.assertEqual(parse_score("20", 20), (20.0, None))

    def test_accepts_zero(self):
        self.assertEqual(parse_score("0", 20), (0.0, None))

    def test_rejects_above_the_maximum(self):
        value, error = parse_score("21", 20)
        self.assertIsNone(value)
        self.assertIn("more than 20", error)

    def test_rejects_negative(self):
        value, error = parse_score("-1", 20)
        self.assertIsNone(value)
        self.assertIn("negative", error)

    def test_rejects_non_numeric_rather_than_wiping_the_grade(self):
        value, error = parse_score("8a", 20)
        self.assertIsNone(value)
        self.assertIn("must be a number", error)

    def test_blank_clears_without_an_error(self):
        self.assertEqual(parse_score("", 20), (None, None))
