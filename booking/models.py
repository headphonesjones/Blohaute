from django.db import models
from django.contrib.humanize.templatetags.humanize import apnumber
from django.template.defaultfilters import floatformat
from adminsortable.models import Sortable


class Setting(models.Model):
    access_token = models.CharField(max_length=255, null=True, blank=True)
    merchant_access_token = models.CharField(max_length=255, null=True, blank=True)


class Treatment(Sortable):
    name = models.CharField(max_length=255)
    plural_name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=50, unique=True)
    booker_id = models.IntegerField(null=True, blank=True)
    list_tagline = models.CharField(max_length=255, blank=True)
    list_image = models.ImageField(upload_to='treatment_images')
    thumb_image = models.ImageField(upload_to='thumbnail_images')
    description = models.TextField(blank=True)
    price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2)
    original_price = models.DecimalField(default=0.00, max_digits=10, decimal_places=2, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta(Sortable.Meta):
        pass

    def __unicode__(self):
        return self.name

    def cart_description(self):
        return self.name

    @property
    def list_image_url(self):
        print self.list_image
        if self.list_image and hasattr(self.list_image, 'url'):
            return self.list_image.url

    @property
    def thumb_image_url(self):
        print self.thumb_image
        if self.thumb_image and hasattr(self.list_image, 'url'):
            return self.thumb_image.url


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


class AppointmentResult(object):
    def __init__(self):
        self.upcoming = []
        self.past = []


class Appointment(object):
    appointment_id = None
    time = None
    date = None
    treatment = None

    def __init__(self, appointment_id, appt_time, date, service_id, service_name):
        self.appointment_id = appointment_id
        self.date = date
        self.time = appt_time
        self.treatment_id = service_id
        self.treatment_name = service_name
        self.treatment = Treatment.objects.filter(booker_id=service_id)

    def __str__(self):
        return self.treatment + " at " + self.time + " on " + self.date


class CustomerSeries(object):
    series_id = None
    name = None
    quantity = None
    remaining = None
    expiration = None
    redeemable_items = None
    treatment = None

    def __init__(self, series_id, name, quantity, remaining, expiration, redeemable):
        self.series_id = series_id
        self.name = name
        self.quantity = quantity
        self.remaining = remaining
        # self.expiration = expiration
        self.redeemable_items = redeemable
        treatment_id = self.redeemable_items[0]['TreatmentID']
        self.treatment = Treatment.objects.get(booker_id=treatment_id)

    def __str__(self):
        if self.expiration is None:
            self.expiration = "Never"
        return self.name + " " + str(self.remaining) + " of " + str(self.quantity)
