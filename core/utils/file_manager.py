"""
File management utilities.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FileManager:
    """Manager for file operations"""
    
    @staticmethod
    def delete_file_safely(file_field) -> bool:
        """
        Safely delete a file from storage.
        
        Args:
            file_field: Django FileField or ImageField
            
        Returns:
            True if deleted successfully, False otherwise
        """
        if not file_field:
            return False
        
        try:
            file_field.delete(save=False)
            return True
        except Exception as e:
            logger.error(f"Error deleting file: {e}", exc_info=True)
            return False
    
    @staticmethod
    def get_file_size_mb(file_field) -> Optional[float]:
        """
        Get file size in megabytes.
        
        Args:
            file_field: Django FileField or ImageField
            
        Returns:
            File size in MB or None if file doesn't exist
        """
        if not file_field:
            return None
        
        try:
            return file_field.size / 1024 / 1024
        except Exception:
            return None
    
    @staticmethod
    def get_file_name(file_field) -> Optional[str]:
        """
        Get filename from file field.
        
        Args:
            file_field: Django FileField or ImageField
            
        Returns:
            Filename or None if file doesn't exist
        """
        if not file_field:
            return None
        
        try:
            return file_field.name.split('/')[-1]
        except Exception:
            return None

# Made with Bob
