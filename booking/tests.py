from datetime import datetime, timedelta
from django.test import TestCase
from settings.models import Setting
from service import BookerClient
from booking.models import Treatment


class BookerClientTest(TestCase):

    def test_get_setting_object_returns_first_setting_object(self):
        new_settings_object = Setting.objects.create()
        client = BookerClient()
        self.assertEqual(client.get_settings_object(), new_settings_object)

    def test_get_setting_object_creates_setting_if_does_not_exist(self):
        client = BookerClient()
        self.assertIsInstance(client.get_settings_object(), Setting)


class BookerCustomerClientTest(TestCase):
    def setUp(self):
        self.client = BookerClient()

    def test_get_server_information(self):
        response = self.client.get_server_information()
        print response['ServerIsDaylightSavingsTime']
        print response['ServerTimeZoneOffset']

    def test_get_services(self):
        response = self.client.get_services()
        print response

    def test_get_availability(self):
        treatment = Treatment.objects.create(booker_id=1500539)
        start_date = datetime.now() + timedelta(days=7)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=0)

        response = self.client.get_availability(treatment, start_date, end_date)
        print response


    def test_get_availability_multiservice(self):
        treatment = Treatment.objects.create(booker_id=1500539)

        start_date = datetime.now() + timedelta(days=7)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=0)

        response = self.client.get_availability_multiservice([treatment,], start_date, end_date)
        print response

    def test_get_availability_multiservice_with_two_services(self):
        Treatment.objects.create(booker_id=1500539)
        Treatment.objects.create(booker_id=1500556, slug="upstyles")

        start_date = datetime.now() + timedelta(days=7)
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=0)

        response = self.client.get_availability_multiservice(Treatment.objects.all(), start_date, end_date)
        slots = response['ItineraryTimeSlotsLists'][0]['ItineraryTimeSlots']
        print slots
        print len(slots)
        for slot in slots:

            time_slots = slot['TreatmentTimeSlots']
            print "%s - %s" % (time_slots[0]['StartDateTime'], time_slots[1]['StartDateTime'])
            print "%s - %s" % (time_slots[0]['EmployeeID'], time_slots[1]['EmployeeID'])