import json


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


class Treatment(JSONSerializable):
    TreatmentId = None
    TreatmentName = None
    Price = None

    def __init__(self, treatment_id, treatment_name, price):
        self.id = treatment_id
        self.name = treatment_name
        self.price = price


class Itinerary(JSONSerializable):
    Treatments = []

    def __init__(self, treatments=[]):
        self.Treatments = treatments