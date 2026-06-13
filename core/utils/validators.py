"""
File validation utilities.
"""
import os
from typing import Optional
from django.core.exceptions import ValidationError
from core.constants import FileValidation, MaterialType


class FileValidator:
    """Validator for file uploads"""
    
    @classmethod
    def validate_file(
        cls,
        file,
        material_type: Optional[str] = None,
        max_size: Optional[int] = None
    ) -> bool:
        """
        Validate uploaded file.
        
        Args:
            file: Uploaded file object
            material_type: Type of material (PDF, VIDEO, PPT)
            max_size: Maximum file size in bytes
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        if not file:
            raise ValidationError("No file provided")
        
        # Check file size
        max_allowed_size = max_size or FileValidation.MAX_FILE_SIZE
        if file.size > max_allowed_size:
            size_mb = max_allowed_size / 1024 / 1024
            raise ValidationError(
                f"File too large. Maximum size: {size_mb:.0f}MB"
            )
        
        # Check file extension if material type specified
        if material_type and material_type != MaterialType.LINK:
            ext = os.path.splitext(file.name)[1].lower()
            allowed = FileValidation.ALLOWED_EXTENSIONS.get(material_type, [])
            
            if allowed and ext not in allowed:
                raise ValidationError(
                    f"Invalid file type '{ext}'. "
                    f"Allowed types: {', '.join(allowed)}"
                )
        
        return True
    
    @classmethod
    def validate_assignment_file(cls, file) -> bool:
        """
        Validate assignment file upload.
        
        Args:
            file: Uploaded file object
            
        Returns:
            True if valid
            
        Raises:
            ValidationError: If validation fails
        """
        return cls.validate_file(
            file,
            max_size=FileValidation.MAX_ASSIGNMENT_FILE_SIZE
        )
    
    @classmethod
    def get_file_extension(cls, filename: str) -> str:
        """
        Get file extension from filename.
        
        Args:
            filename: Name of the file
            
        Returns:
            File extension (lowercase, with dot)
        """
        return os.path.splitext(filename)[1].lower()
    
    @classmethod
    def is_valid_extension(cls, filename: str, material_type: str) -> bool:
        """
        Check if filename has valid extension for material type.
        
        Args:
            filename: Name of the file
            material_type: Type of material
            
        Returns:
            True if extension is valid
        """
        ext = cls.get_file_extension(filename)
        allowed = FileValidation.ALLOWED_EXTENSIONS.get(material_type, [])
        return ext in allowed if allowed else True

# Made with Bob
