from django.db import models

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('P', 'Present'),
        ('A', 'Absent'),
        ('H', 'Holiday'),
        ('HD', 'Half Day'),
    ]
    institution_id = models.CharField(max_length=100)
    admno = models.CharField(max_length=100)
    date = models.DateField()
    status = models.CharField(max_length=2, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('institution_id', 'admno', 'date')

    def __str__(self):
        return f"{self.admno} - {self.date} - {self.status}"
