import json


class IdCache:
    treatments_ids = {'Updo': 1500556, 'Braid': 1500553, 'Blow Out': 1500539}


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