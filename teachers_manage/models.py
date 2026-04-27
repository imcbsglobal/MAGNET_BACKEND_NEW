from django.db import models

class Teacher(models.Model):
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    job_category = models.CharField(max_length=255, null=True, blank=True)
    institution_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.username
