"""
Model mixins for common functionality.
"""
import logging
from django.db import models

logger = logging.getLogger(__name__)


class FileCleanupMixin(models.Model):
    """
    Mixin to automatically delete files when model instance is deleted.
    
    Usage:
        class MyModel(FileCleanupMixin, models.Model):
            file_url = models.FileField(upload_to='uploads/')
    """
    
    class Meta:
        abstract = True
    
    def delete(self, *args, **kwargs):
        """Delete model instance and associated file"""
        self._delete_file()
        super().delete(*args, **kwargs)
    
    def _delete_file(self):
        """Delete the file from storage, unless another record still uses it"""
        file_field = getattr(self, 'file_url', None)
        if not file_field or not file_field.name:
            return

        # LINK-type records keep a plain URL here rather than a stored file.
        if file_field.name.startswith(('http://', 'https://')):
            return

        # Uploads to S3 overwrite by default, so older records can share one key.
        # Removing it here would blank out every other record pointing at it.
        still_referenced = (
            type(self)._default_manager
            .filter(file_url=file_field.name)
            .exclude(pk=self.pk)
            .exists()
        )
        if still_referenced:
            logger.info(
                f"Keeping file {file_field.name!r} — still referenced by another "
                f"{self.__class__.__name__} record"
            )
            return

        try:
            file_field.delete(save=False)
        except Exception as e:
            logger.error(
                f"Error deleting file for {self.__class__.__name__} "
                f"(id={self.pk}): {e}",
                exc_info=True
            )


class TimestampMixin(models.Model):
    """
    Mixin to add created_at and updated_at timestamps.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

# Made with Bob
