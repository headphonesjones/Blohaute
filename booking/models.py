from django.db import models
from django.contrib.humanize.templatetags.humanize import apnumber
from django.template.defaultfilters import floatformat
from adminsortable.models import Sortable
from datetime import timedelta, datetime, date
from booking.models import Treatment


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

    def price_units(self):
        return ""


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

    def price_units(self):
        return ""


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


class IdCache:
    TREATMENT_IDS = {'Updo': 1500556, 'Braid': 1500553, 'Blow Out': 1500539}
    employees = {'Amanda I': 322953,
                 'Amanda S/D': 319599,
                 'Jessie Hitzeman': 319544,
                 'Morgan': 319549,
                 'Jesse Scheele': 322667,
                 'April Telman': 322866}


class AvailableTimeSlot(object):
    single_employee_slots = []
    multiple_employee_slots = []
    pretty_time = ''

    def __eq__(self, other):
        return self.pretty_time == other.pretty_time

    def __hash__(self):
        return hash(self.pretty_time)

    def __str__(self):
        return "%s has %d single and %d multiple employee slots" % (self.pretty_time,
                                                                    len(self.single_employee_slots),
                                                                    len(self.multiple_employee_slots))


class BookerModel(object):
    def parse_date(self, datestring):
        timepart = datestring.split('(')[1].split(')')[0]
        milliseconds = int(timepart[:-5])
        hours = int(timepart[-5:]) / 100
        # print("hours is what? %s" % hours)
        timepart = milliseconds / 1000

        dt = datetime.utcfromtimestamp(timepart + hours * 3600)
        return dt


class AppointmentItem(BookerModel):
    appointment_id = None
    datetime = None
    treatment = None
    employee_name = None

    def __init__(self, data=None):
        if data:
            self.appointment_id = data['AppointmentID']
            self.datetime = self.parse_date(data['StartDateTime'])
            self.treatment_id = data['Treatment']['ID']
            self.treatment_name = data['Treatment']['Name']
            self.employee_name = data['Employee']['FirstName']
            self.treatment = Treatment.objects.get(booker_id=self.treatment_id)
            print 'creaeted appointment id %d' % self.appointment_id
    def __str__(self):
        return self.treatment + " at " + self.time + " on " + self.date

    def __unicode__(self):
        return self.treatment.name + " at " + self.time + " on " + self.date


class Appointment(BookerModel):
    id = None
    status = None
    customer_id = None
    booking_number = None
    start_datetime = None
    end_datetime = None
    final_total = None
    can_cancel = None
    treatments = []

    def __init__(self, data=None):
        if data:

            self.id = data['ID']
            self.booking_number = data['BookingNumber']
            self.customer_id = data['CustomerID']
            self.start_datetime = self.parse_date(data['StartDateTime'])
            self.end_datetime = self.parse_date(data['EndDateTime'])
            self.final_total = data['FinalTotal']['Amount']
            self.status = data['Status']['ID']
            self.can_cancel = data['CanCancel']
            print "there are %d treatments" % len(data['AppointmentTreatments'])
            self.treatments = []
            for appointment in data['AppointmentTreatments']:
                treatment = AppointmentItem(appointment)
                self.treatments.append(treatment)
            print 'creaeted Itinerary id %d' % self.id


    def is_past(self):
        return datetime.now() - self.start_datetime > timedelta(minutes=5)


