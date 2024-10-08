from django.db import models

class UploadedImage(models.Model):
    original_image = models.CharField(max_length=255)
    copy_image = models.CharField(max_length=255)
    original_heatmap = models.CharField(max_length=255)
    copy_heatmap = models.CharField(max_length=255)

    def __str__(self):
        return f"Original: {self.original_image}, Copy: {self.copy_image}"
