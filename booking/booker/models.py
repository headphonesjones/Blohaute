class Location(object):
    pass


class Customer(object):
    id = None
    password = None
    access_token = None
    home_phone = None
    email = None
    city = None
    country_id = None
    country_name = None
    state = None 
    street_1 = None
    street_2 = None
    zip = None

    def save(self):
        pass

    def delete(self):
        pass

    def confirm_account(self):
        pass

    def change_password(self, old_password, new_password):
        pass

    def get_appointments(self):
        pass


class Category(object):
    pass


class Treatment(object):
    pass


class Appointment(object):
    pass