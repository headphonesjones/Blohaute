from django.db import models


class Setting(models.Model):
    access_token = models.CharField(max_length=255)
