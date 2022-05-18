from django.db import models

# Create your models here.

from django.db import models


class TrainingResults(models.Model):
    results =  models.CharField(max_length=10000,null=True,blank=True)
    task_id = models.CharField(max_length=200)
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
