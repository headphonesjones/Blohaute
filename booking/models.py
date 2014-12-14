from django.db import models
from django.contrib.humanize.templatetags.humanize import apnumber
from django.template.defaultfilters import floatformat
from django_bleach.models import BleachField


class Setting(models.Model):
    access_token = models.CharField(max_length=255)


class Treatment(models.Model):
    booker_id = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=255)
    plural_name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=50, unique=True)
    list_tagline = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    full_description = BleachField(blank=True)
    price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    original_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return self.name

    def cart_description(self):
        return self.name

    def primary_image(self):
        return self.images.filter(primary_image=True).first()


class TreatmentImage(models.Model):
    treatment = models.ForeignKey(Treatment, related_name="images")
    image = models.ImageField(blank=True, null=True, upload_to='treatment_images')
    primary_image = models.BooleanField(default=False)


class Package(models.Model):
    booker_id = models.IntegerField(null=True, blank=True)
    treatment = models.ForeignKey(Treatment, related_name="packages")
    quantity = models.IntegerField()
    price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)

    def __unicode__(self):
        return "%s Pack - $%s" % ((str(apnumber(self.quantity)).capitalize()), floatformat(self.price, -2))

    def cart_description(self):
        return "%s - %s Pack" % (self.treatment.name, self.quantity)


class Membership(models.Model):
    booker_id = models.IntegerField(null=True, blank=True)
    treatment = models.ForeignKey(Treatment, related_name="memberships")
    quantity = models.IntegerField()
    price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)

    def __unicode__(self):
        return "%d %s / $%s per month" % (self.quantity, self.treatment.plural_name, floatformat(self.price, -2))

    def cart_description(self):
        return "%s Membership - %s per month" % (self.treatment.name, self.quantity)

    def price_units(self):
        return "/ month"