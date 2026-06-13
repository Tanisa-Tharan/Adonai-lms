"""
User service for managing user operations.
"""
import secrets
import logging
from typing import Tuple, Optional, Dict, Any
from django.db import transaction
from django.contrib.auth import get_user_model

from accounts.models import UserProfile
from academics.models import Enrollment
from .email_service import EmailService
from core.constants import UserRoles

User = get_user_model()
logger = logging.getLogger(__name__)


class UserService:
    """Service for user management operations"""
    
    def __init__(self):
        self.email_service = EmailService()
    
    def create_user(self, user_data: Dict[str, Any]) -> Tuple[User, str]:
        """
        Create a new user with profile and enrollment (if student).
        
        Args:
            user_data: Dictionary containing user information
            
        Returns:
            Tuple of (User instance, generated password)
            
        Raises:
            Exception: If user creation fails
        """
        with transaction.atomic():
            # Create user instance
            user = self._create_user_instance(user_data)
            
            # Generate and set password
            password = self._generate_password()
            user.set_password(password)
            user.save()
            
            logger.info(f"User created: {user.email} (role: {user.role})")
            
            # Create profile
            self._create_profile(user, user_data)
            
            # Create enrollment if student
            if user.role == UserRoles.STUDENT:
                self._create_enrollment(user, user_data)
            
            # Send welcome email
            self.email_service.send_welcome_email(user, password)
            
            return user, password
    
    def update_user(self, user: User, user_data: Dict[str, Any]) -> User:
        """
        Update existing user information.
        
        Args:
            user: User instance to update
            user_data: Dictionary containing updated user information
            
        Returns:
            Updated User instance
        """
        with transaction.atomic():
            # Update user fields
            user.email = user_data.get('email', user.email)
            user.first_name = user_data.get('first_name', user.first_name)
            user.last_name = user_data.get('last_name', user.last_name)
            user.role = user_data.get('role', user.role)
            user.save()
            
            logger.info(f"User updated: {user.email}")
            
            # Update profile
            self._update_profile(user, user_data)
            
            # Update or create enrollment if student
            if user.role == UserRoles.STUDENT:
                self._update_or_create_enrollment(user, user_data)
            else:
                # Remove enrollment if role changed from student
                Enrollment.objects.filter(student=user).delete()
            
            return user
    
    def reset_password(self, user: User) -> str:
        """
        Reset user password and send email.
        
        Args:
            user: User instance
            
        Returns:
            New generated password
        """
        new_password = self._generate_password()
        user.set_password(new_password)
        user.save()
        
        logger.info(f"Password reset for user: {user.email}")
        
        # Send password reset email
        self.email_service.send_password_reset_email(user, new_password)
        
        return new_password
    
    def _create_user_instance(self, data: Dict[str, Any]) -> User:
        """Create user instance without saving"""
        return User(
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role=data['role'],
            is_active=True
        )
    
    def _generate_password(self) -> str:
        """Generate secure random password"""
        return secrets.token_urlsafe(8)
    
    def _create_profile(self, user: User, data: Dict[str, Any]):
        """Create user profile"""
        UserProfile.objects.create(
            user=user,
            phone=data.get('phone', ''),
            address=data.get('address', ''),
            dob=data.get('dob')
        )
        logger.debug(f"Profile created for user: {user.email}")
    
    def _update_profile(self, user: User, data: Dict[str, Any]):
        """Update user profile"""
        profile, created = UserProfile.objects.get_or_create(user=user)
        profile.phone = data.get('phone', '')
        profile.address = data.get('address', '')
        profile.dob = data.get('dob')
        profile.save()
        logger.debug(f"Profile updated for user: {user.email}")
    
    def _create_enrollment(self, user: User, data: Dict[str, Any]):
        """Create student enrollment"""
        Enrollment.objects.create(
            student=user,
            academic_year=data.get('academic_year'),
            track=data.get('track'),
            start_date=data.get('start_date'),
            expected_completion_date=data.get('expected_completion_date'),
            start_quarter=data.get('start_quarter')
        )
        logger.debug(f"Enrollment created for student: {user.email}")
    
    def _update_or_create_enrollment(self, user: User, data: Dict[str, Any]):
        """Update or create student enrollment"""
        Enrollment.objects.update_or_create(
            student=user,
            defaults={
                'academic_year': data.get('academic_year'),
                'track': data.get('track'),
                'start_date': data.get('start_date'),
                'expected_completion_date': data.get('expected_completion_date'),
                'start_quarter': data.get('start_quarter'),
            }
        )
        logger.debug(f"Enrollment updated for student: {user.email}")

# Made with Bob
