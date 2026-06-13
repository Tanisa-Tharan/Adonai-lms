"""
Core constants for the LMS application.
Centralizes all magic strings and choices.
"""


class UserRoles:
    """User role constants"""
    ADMIN = 'ADMIN'
    SUPERVISOR = 'SUPERVISOR'
    FACULTY = 'FACULTY'
    STUDENT = 'STUDENT'
    
    CHOICES = (
        (ADMIN, 'Admin'),
        (SUPERVISOR, 'Supervisor'),
        (FACULTY, 'Faculty'),
        (STUDENT, 'Student'),
    )
    
    @classmethod
    def is_valid(cls, role: str) -> bool:
        """Check if role is valid"""
        return role in {cls.ADMIN, cls.SUPERVISOR, cls.FACULTY, cls.STUDENT}
    
    @classmethod
    def is_admin_or_supervisor(cls, role: str) -> bool:
        """Check if role is admin or supervisor"""
        return role in {cls.ADMIN, cls.SUPERVISOR}
    
    @classmethod
    def is_admin_or_faculty(cls, role: str) -> bool:
        """Check if role is admin or faculty"""
        return role in {cls.ADMIN, cls.FACULTY}


class EnrollmentStatus:
    """Enrollment status constants"""
    ACTIVE = 'ACTIVE'
    COMPLETED = 'COMPLETED'
    DROPPED = 'DROPPED'
    
    CHOICES = (
        (ACTIVE, 'Active'),
        (COMPLETED, 'Completed'),
        (DROPPED, 'Dropped'),
    )


class EnrollmentTrack:
    """Enrollment track constants"""
    DIPLOMA = 'DIPLOMA'
    CERTIFICATE = 'CERTIFICATE'
    
    CHOICES = (
        (DIPLOMA, 'Diploma Program'),
        (CERTIFICATE, 'Certificate Program'),
    )


class ModuleRunStatus:
    """Module run status constants"""
    SCHEDULED = 'SCHEDULED'
    RUNNING = 'RUNNING'
    COMPLETED = 'COMPLETED'
    
    CHOICES = (
        (SCHEDULED, 'Scheduled'),
        (RUNNING, 'Running'),
        (COMPLETED, 'Completed'),
    )


class StudentModuleStatus:
    """Student module status constants"""
    NOT_STARTED = 'NOT_STARTED'
    IN_PROGRESS = 'IN_PROGRESS'
    COMPLETED = 'COMPLETED'
    
    CHOICES = (
        (NOT_STARTED, 'Not Started'),
        (IN_PROGRESS, 'In Progress'),
        (COMPLETED, 'Completed'),
    )


class AttendanceStatus:
    """Attendance status constants"""
    PRESENT = 'PRESENT'
    ABSENT = 'ABSENT'
    LATE = 'LATE'
    
    CHOICES = (
        (PRESENT, 'Present'),
        (ABSENT, 'Absent'),
        (LATE, 'Late'),
    )


class MaterialType:
    """Course material type constants"""
    PDF = 'PDF'
    VIDEO = 'VIDEO'
    LINK = 'LINK'
    PPT = 'PPT'
    
    CHOICES = (
        (PDF, 'PDF'),
        (VIDEO, 'Video'),
        (LINK, 'Link'),
        (PPT, 'PPT'),
    )


class ResourceType:
    """Resource type constants"""
    REQUIRED = 'REQUIRED'
    RECOMMENDED = 'RECOMMENDED'
    RESOURCES = 'RESOURCES'
    
    CHOICES = (
        (REQUIRED, 'Required'),
        (RECOMMENDED, 'Recommended'),
        (RESOURCES, 'Resources'),
    )


class QuarterType:
    """Quarter type constants"""
    MODULE = 'MODULE'
    QUIZ = 'QUIZ'
    
    CHOICES = (
        (MODULE, 'Module'),
        (QUIZ, 'Quiz'),
    )


class FileValidation:
    """File validation constants"""
    ALLOWED_EXTENSIONS = {
        MaterialType.PDF: ['.pdf'],
        MaterialType.VIDEO: ['.mp4', '.avi', '.mov', '.mkv'],
        MaterialType.PPT: ['.ppt', '.pptx', '.odp']
    }
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_ASSIGNMENT_FILE_SIZE = 100 * 1024 * 1024  # 100MB

# Made with Bob
