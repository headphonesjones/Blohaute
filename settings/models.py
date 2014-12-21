from django.db import models


class Setting(models.Model):
    access_token = models.CharField(max_length=255, null=True, blank=True)
    merchant_access_token = models.CharField(max_length=255, null=True, blank=True)
