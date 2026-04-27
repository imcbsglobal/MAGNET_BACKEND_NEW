from django.db import models

class JobCategory(models.Model):
    name = models.CharField(max_length=255)
    institution_id = models.CharField(max_length=100) # This links the category to a specific school
    created_at = models.DateTimeField(auto_now_add=True)

    def __cl__(self):
        return self.name
