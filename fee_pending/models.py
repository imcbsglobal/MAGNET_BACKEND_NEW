from django.db import models

class FeePending(models.Model):
    institution_id = models.CharField(max_length=100)
    admno = models.CharField(max_length=100)
    month = models.CharField(max_length=100)
    particulars = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    fine = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refno = models.CharField(max_length=100)
    remark = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.admno