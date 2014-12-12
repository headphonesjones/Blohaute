import json


class JSONSerializable:
    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)


class Treatment(object, JSONSerializable):
    treatment_id = None
    treatment_name = None

    def __init__(self, treatment_id, treatment_name):
        self.treatment_id = treatment_id;
        self.treatment_name = treatment_name


class Itinerary(object, JSONSerializable):
    treatments = []

    def __init__(self, treatments=[]):
        self.treatments = treatments