from django.db import models

class StudentData(models.Model):
    institution_id = models.CharField(max_length=100)
    admno = models.CharField(max_length=100)
    student_name = models.CharField(max_length=200)
    student_class = models.CharField(max_length=100)
    div = models.CharField(max_length=50)
    password = models.CharField(max_length=100)
    mobile = models.CharField(max_length=20, blank=True, null=True)
    fathername = models.CharField(max_length=200, blank=True, null=True)
    mothername = models.CharField(max_length=200, blank=True, null=True)
    imageurl = models.TextField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    place = models.CharField(max_length=200, blank=True, null=True)
    remark = models.TextField(blank=True, null=True)
    refno = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.student_name