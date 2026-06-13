"""
Email service for sending notifications.
"""
import logging
from typing import Optional
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def send_welcome_email(user, password: str) -> bool:
        """
        Send welcome email to new user with login credentials.
        
        Args:
            user: User instance
            password: Generated password
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            subject = "Your LMS Account Created"
            message = f"""
Hello {user.first_name},

Your LMS account has been created.

Login Details:
Email: {user.email}
Password: {password}

Please login and change your password.

Regards,
LMS Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            logger.info(f"Welcome email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to send welcome email to {user.email}: {e}",
                exc_info=True
            )
            return False
    
    @staticmethod
    def send_password_reset_email(user, new_password: str) -> bool:
        """
        Send password reset email to user.
        
        Args:
            user: User instance
            new_password: New generated password
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            subject = "Your LMS Password Has Been Reset"
            message = f"""
Hello {user.first_name},

Your LMS password has been reset.

New Login Details:
Email: {user.email}
Password: {new_password}

Please login and change your password.

Regards,
LMS Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
            
            logger.info(f"Password reset email sent to {user.email}")
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to send password reset email to {user.email}: {e}",
                exc_info=True
            )
            return False
    
    @staticmethod
    def send_assignment_notification(
        student_email: str,
        assignment_title: str,
        module_title: str,
        due_date: str
    ) -> bool:
        """
        Send assignment notification to student.
        
        Args:
            student_email: Student's email address
            assignment_title: Title of the assignment
            module_title: Title of the module
            due_date: Due date string
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            subject = f"New Assignment: {assignment_title}"
            message = f"""
Hello,

A new assignment has been posted for {module_title}.

Assignment: {assignment_title}
Due Date: {due_date}

Please login to the LMS to view details and submit your work.

Regards,
LMS Team
            """
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[student_email],
                fail_silently=False,
            )
            
            logger.info(f"Assignment notification sent to {student_email}")
            return True
            
        except Exception as e:
            logger.error(
                f"Failed to send assignment notification to {student_email}: {e}",
                exc_info=True
            )
            return False

# Made with Bob
