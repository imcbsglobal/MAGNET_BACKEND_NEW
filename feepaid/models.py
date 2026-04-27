from django.db import models

class FeePaid(models.Model):
    institution_id = models.CharField(max_length=100)
    admno = models.CharField(max_length=100)
    particulars = models.TextField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    refno = models.CharField(max_length=100)
    remark = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.admno