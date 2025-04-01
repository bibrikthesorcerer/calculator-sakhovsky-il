from django.db import models

# Create your models here.
class CalculatedResult(models.Model):
    expression = models.TextField(max_length=1024)
    result = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'calculated_result'
        verbose_name_plural = 'calculated_results'
        db_table = 'calc_result'