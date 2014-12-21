import json
from datetime import timedelta, datetime, date
from booking.models import Treatment

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


class JSONSerializable:
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)

    def parse_date(self, datestring):
        timepart = datestring.split('(')[1].split(')')[0]
        milliseconds = int(timepart[:-5])
        hours = int(timepart[-5:]) / 100
        # print("hours is what? %s" % hours)
        timepart = milliseconds / 1000

        dt = datetime.utcfromtimestamp(timepart + hours * 3600)
        return dt


class Appointment(JSONSerializable):
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

    def __str__(self):
        return self.treatment + " at " + self.time + " on " + self.date


class Itinerary(JSONSerializable):
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
                treatment = Appointment(appointment)
                self.treatments.append(treatment)

    def is_past(self):
        return datetime.now() - self.start_datetime > timedelta(minutes=5)
