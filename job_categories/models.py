from django.db import models

class JobCategory(models.Model):
    name = models.CharField(max_length=255)
    institution_id = models.CharField(max_length=100)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
