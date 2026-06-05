import uuid
from django.db import models


class IDCardForm(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_USED = 'used'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_USED, 'Used'),
    ]

    institution_id = models.CharField(max_length=50)
    admno = models.CharField(max_length=100)
    token = models.CharField(max_length=64, unique=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    sent_at = models.DateTimeField(null=True, blank=True)
    used_at = models.DateTimeField(null=True, blank=True)

    # Parent-entered ID card details
    student_name = models.CharField(max_length=200, blank=True)
    house_name = models.CharField(max_length=200, blank=True)
    place = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    pin = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    father_name = models.CharField(max_length=200, blank=True)
    mother_name = models.CharField(max_length=200, blank=True)
    dob = models.DateField(null=True, blank=True)

    # Student photo stored on Cloudflare R2
    photo_url = models.URLField(max_length=500, blank=True, null=True)
    photo_key = models.CharField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('institution_id', 'admno')
        ordering = ['-updated_at']

    def __str__(self):
        return f"IDCardForm({self.institution_id}, {self.admno})"

    @staticmethod
    def generate_token():
        return uuid.uuid4().hex
