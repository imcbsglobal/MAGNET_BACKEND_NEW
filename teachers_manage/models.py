from django.db import models
import uuid

def generate_staff_id():
    return 'STF-' + uuid.uuid4().hex[:6].upper()

class Teacher(models.Model):
    staff_id = models.CharField(max_length=20, unique=True, blank=True)
    username = models.CharField(max_length=255)
    password = models.CharField(max_length=255)
    job_category = models.CharField(max_length=255, null=True, blank=True)
    institution_id = models.CharField(max_length=100)
    reg_number = models.CharField(max_length=100, null=True, blank=True)
    school_reg_number = models.CharField(max_length=100, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    pincode = models.CharField(max_length=10, null=True, blank=True)
    nationality = models.CharField(max_length=100, null=True, blank=True)
    assigned_class = models.CharField(max_length=100, null=True, blank=True)
    assigned_division = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.staff_id:
            while True:
                new_id = generate_staff_id()
                if not Teacher.objects.filter(staff_id=new_id).exists():
                    self.staff_id = new_id
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Staff'
        verbose_name_plural = 'Staff'
