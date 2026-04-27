from django.db import models

class AdministratorProfile(models.Model):
    school_name = models.CharField(max_length=255)
    address = models.TextField()
    city = models.CharField(max_length=100)
    district = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    state = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15)
    institution_id = models.CharField(max_length=50, unique=True)
    username = models.CharField(max_length=100, unique=True)
    password = models.CharField(max_length=255) 
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.school_name} ({self.institution_id})"
