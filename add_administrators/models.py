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


class SchoolInfo(models.Model):
    """
    School profile set by the administrator for their institution.
    One record per institution_id. Logo stored on Cloudinary.
    """
    institution_id = models.CharField(max_length=50, unique=True)
    school_name = models.CharField(max_length=255)
    address = models.TextField()
    place = models.CharField(max_length=200)
    pincode = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    logo_url = models.URLField(max_length=500, blank=True, null=True)
    logo_public_id = models.CharField(max_length=255, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"SchoolInfo({self.institution_id})"
