from django.db import models


class CaseInsensitiveEmailField(models.EmailField):
    def get_prep_value(self, value):
        value = super(CaseInsensitiveEmailField, self).get_prep_value(value)
        if value is not None:
            value = value.lower()
        return value
