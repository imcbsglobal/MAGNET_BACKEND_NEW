from django.db import models

class StudentData(models.Model):
    institution_id = models.CharField(max_length=100)
    admno = models.CharField(max_length=100)
    student_name = models.CharField(max_length=200)
    student_class = models.CharField(max_length=100)
    div = models.CharField(max_length=100)
    password = models.CharField(max_length=100)
    mobile = models.CharField(max_length=50)
    fathername = models.CharField(max_length=200)
    mothername = models.CharField(max_length=200)
    imageurl = models.TextField(blank=True, null=True)
    address = models.TextField()
    place = models.CharField(max_length=200)
    remark = models.TextField(blank=True, null=True)
    refno = models.CharField(max_length=100)

    def __str__(self):
        return self.student_name