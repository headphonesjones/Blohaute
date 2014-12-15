import json
from requests import Request, Session
from django.conf import settings
from django.forms import ValidationError
from booking.models import Setting
from datetime import timedelta, datetime
import calendar
import time


class BookerRequest(Request):
    """
    Sets up, sends, and processes a single request to the Booker API
    """
    base_url = 'https://stable-app.secure-booker.com/webservice4/json/CustomerService.svc'
    path = None
    method = None
    params = {}
    needs_user_token = False
    token = None

    def __init__(self, path, token, params={}):
        headers = {'content-type': 'application/json'}
        super(BookerRequest, self).__init__(params=params, headers=headers)
        self.path = path
        if token:
            self.token = token

    def send(self):
        self.url = "%s%s" % (self.base_url, self.path)
        prepped = self.prepare()
        s = Session()
        print(self.data)
        response = s.send(prepped)
        response.needs_user_token = self.needs_user_token
        response.original_request = self
        return response

    def post(self):
        self.method = 'POST'
        if self.token:
            self.params['access_token'] = self.token
        self.data = json.dumps(self.params)
        self.original_params = self.params
        self.params = None
        return self.send()

    def get(self):
        self.method = 'GET'
        if self.token:
            self.params['access_token'] = self.token
        return self.send()

    def delete(self):
        self.method = 'DELETE'
        if self.token:
            self.params['access_token'] = self.token
        self.data = json.dumps(self.params)
        self.original_params = self.params
        self.params = None
        return self.send()


class BookerAuthedRequest(BookerRequest):
    needs_user_token = True


class BookerClient(object):
    token = None

    def __init__(self, token=None):
        if token is None:
            setting = self.get_settings_object()

            self.token = setting.access_token
            if self.token is None:
                self.load_token()

    def get_settings_object(self):
        setting = Setting.objects.first()
        if setting is None:
            setting = Setting()
        return setting

    def load_token(self, setting=None):
        params = {'client_id': settings.BOOKER_API_KEY,
                  'client_secret': settings.BOOKER_API_SECRET,
                  'grant_type': 'client_credentials'}
        response = BookerRequest('/access_token', None, params).get()
        self.token = response.json()['access_token']
        if setting is None:
            setting = self.get_settings_object()
        setting.access_token = self.token
        setting.save()


class AvailableTimeSlot(object):
        single_employee_slots = []
        multiple_employee_slots = []
        raw_time = None
        pretty_time = ''

        def __init__(self):
            self.single_employee_slots = []
            self.multiple_employee_slots = []
            self.raw_time = None
            self.pretty_time = ''

        def __eq__(self, other):
            return self.pretty_time == other.pretty_time

        def __hash__(self):
            return hash(self.pretty_time)


class BookerCustomerClient(BookerClient):
    location_id = 29033  # From get location call, we should cache this for now
    customer_token = None
    customer_password = None
    user = None
    customer = None
    customer_id = None

    def get_services(self):
        """
        Returns treatments for a spa/location
        """
        params = {'LocationID': self.location_id}
        response = BookerRequest('/treatments', self.token, params).post()
        return self.process_response(response)['Treatments']

    def get_packages(self):
        """
        Returns packages for a spa/location
        """
        response = BookerRequest('/series', self.token).post()
        return self.process_response(response)

    def get_employees(self):
        """
        Returns packages for a spa/location
        """
        response = BookerRequest('/employees', self.token, {'LocationID': self.location_id}).post()
        return self.process_response(response)

    def create_user(self, email, password, fname, lname, phone):
        """
        Create a new user account and customer
        """
        params = {'LocationID': self.location_id,
                  'Email': email,
                  'Password': password,
                  'FirstName': fname,
                  'LastName': lname,
                  'HomePhone': phone,
                  'Address': {'Street1': None}}
        response = BookerRequest('/customer/account', self.token, params).post()
        return self.process_response(response)

    def login(self, email, password):
        """
        Login a user to the API using their email and password
        """
        params = {'LocationID': self.location_id,
                  'Email': email,
                  'Password': password,
                  'client_id': settings.BOOKER_API_KEY,
                  'client_secret': settings.BOOKER_API_SECRET}
        response = BookerRequest('/customer/login', self.token, params).post()
        response = self.process_response(response)
        self.customer_token = response['access_token']
        self.customer = response['Customer']['Customer']
        self.customer_id = response['Customer']['CustomerID']
        print response
        print("customer is %r" % self.customer)
        return response['access_token']

    def logout(self):
        """
        Logout the currently logged in user
        This doesn't seem to work
        """
        response = BookerAuthedRequest('/logout', self.customer_token, None).get()
        return self.process_response(response)

    def update_password(self, email, old_password, new_password):
        """
        Updates a user's password
        """
        params = {'LocationID': self.location_id,
                  'Email': email,
                  'NewPassword': new_password,
                  'OldPassword': old_password,
                  'CustomerID': self.customer_id}

        response = BookerAuthedRequest('/customer/password', self.customer_token, params).post()
        return self.process_response(response)

    def delete_customer(self):
        """
        Delete a customer
        This doesn't seem to work
        """
        params = {'CustomerID': self.customer.booker_id}
        response = BookerRequest('/customer/%s' % self.customer_id, self.token, params).delete()
        return self.process_response(response)

    def get_upcoming(self):
        params = {
            'CustomerID': self.customer_id,
            'LocationID': self.location_id
        }
        response = BookerRequest('/appointments', self.token, params).post()
        return self.process_response(response)


    def format_date_for_booker_json(self, start_date):
        return "/Date(%s)/" % int(time.mktime(start_date.timetuple()) * 1000)

    def date_range(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    def parse_date(self, datestring):
        timepart = datestring.split('(')[1].split(')')[0]
        milliseconds = int(timepart[:-5])
        hours = int(timepart[-5:]) / 100
        timepart = milliseconds / 1000

        dt = datetime.utcfromtimestamp(timepart + hours * 3600)
        return dt

    def get_availability(self, treatments_requested, start_date, end_date):
        treatments = []
        for treatment in treatments_requested:
            for i in range(0, treatment['quantity']):
                treatments.append({'TreatmentID': treatment['treatment_id']})

        itinerary = [{
                'IsPackage': False,
                'Treatments': treatments}]

        params = {'StartDateTime': self.format_date_for_booker_json(start_date),
                  'EndDateTime': self.format_date_for_booker_json(end_date),
                  'Itineraries': itinerary,
                  'LocationID': self.location_id}

        response = BookerRequest('/availability/multiservice', self.token, params).post()
        # print(response)
        return self.process_response(response)

    def get_unavailable_days_in_range(self, treatments_requested, start_date, number_of_weeks):
        end_date = start_date + timedelta(weeks=number_of_weeks)
        days = set()
        for single_date in self.date_range(start_date, end_date + timedelta(days=1)):
            days.add(single_date.strftime("%Y-%m-%d"))

        current_date = start_date
        for i in range(0, number_of_weeks):
            end_date = current_date + timedelta(weeks=1)
            response = self.get_availability(treatments_requested, current_date, end_date)
            for slot in response['ItineraryTimeSlotsLists'][0]['ItineraryTimeSlots']:
                date_key = self.parse_date(slot['StartDateTime']).strftime("%Y-%m-%d")
                days.discard(date_key)
            current_date = end_date
        return days

    def get_available_times_for_day(self, treatments_requested, start_date):
        times = []
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=0)
        response = self.get_availability(treatments_requested, start_date, end_date)

        # When more than one employee, that 0 below goes away and we iterate
        for itinerary_option in response['ItineraryTimeSlotsLists'][0]['ItineraryTimeSlots']:
            avail_time_slot = AvailableTimeSlot()
            # singles = []
            # multi = []
            itin_time = self.parse_date(itinerary_option['StartDateTime'])
            avail_time_slot.raw_time = itin_time
            avail_time_slot.pretty_time = itin_time.strftime("%I:").lstrip('0') + \
                                          itin_time.strftime("%M") + \
                                          itin_time.strftime(" %p")
            print("timeslot: %s and item %s" % (avail_time_slot.pretty_time, itinerary_option))
            emp_list = set()
            for time_slot in itinerary_option['TreatmentTimeSlots']:
                emp_list.add(time_slot['EmployeeID'])
            print(" slot %s with employee list %r" % (avail_time_slot.pretty_time, emp_list))
            if len(emp_list) == 1:
                avail_time_slot.single_employee_slots.append(itinerary_option)
            elif len(emp_list) == 2:  # Just 2 for now to handle services where one employee doesnt do both only use the singles for now
                avail_time_slot.multiple_employee_slots.append(itinerary_option)
            # avail_time_slot.single_employee_slots = singles
            # avail_time_slot.multiple_employee_slots = multi
            times.append(avail_time_slot)
        return times

    def book_appointment(self, itinerary, address, city, state, zipcode, ccnum, name_on_card, expyear, expmonth, cccode, billingzip):
        adjusted_customer = self.customer
        print(adjusted_customer)
        if adjusted_customer is None:
            print("Null customer")

        adjusted_customer['Address'] = {
            'Street1': address,
            'City': city,
            'State': state,
            'Zip': zipcode
        }
        adjusted_customer.pop('GUID')
        params = {
            'LocationID': self.location_id,
            'ItineraryTimeSlotList': itinerary,
            'AppointmentPayment': {
                'CouponCode': '',
                'PaymentItem': {
                    'Amount': {
                        'Amount': 0,
                        'CurrencyCode': ''
                    },
                    'CreditCard': {
                        'BillingZip': billingzip,
                        'NameOnCard': name_on_card,
                        'ExpirationDate': self.format_date_for_booker_json(datetime(expyear, expmonth, calendar.monthrange(expyear, expmonth)[1])),
                        'Number': ccnum,
                        'SecurityCode': cccode,
                        'Type': {
                            'ID': 1,
                            'Name': ''
                        }
                    },
                    "Method": {
                        "ID": 1,
                        "Name": ""
                    }
                }
            },
            'Customer': adjusted_customer
        }

        print(params)

        return BookerRequest('/appointment/create', self.customer_token, params).post()
        
    def process_response(self, response):
        print 'response is %s' % response
        formatted_response = response.json()
        error_code = formatted_response.get('ErrorCode', 0)
        if error_code == 1000:

            if response.needs_user_token:
                self.login(self.user.email, self.customer_password)
                new_request = BookerAuthedRequest(response.original_request.path, self.token)
            else:
                self.load_token()
                new_request = BookerRequest(response.original_request.path, self.token)
            new_request.method = response.original_request.method
            if new_request.method == 'GET':
                new_request.params = response.original_request.params
                return self.process_response(new_request.get())
            else:
                new_request.params = response.original_request.original_params
                if new_request.token:
                    new_request.params['access_token'] = self.token
                new_request.data = json.dumps(new_request.params)
                new_request.params = None
                return self.process_response(new_request.send())

        if error_code == 200:
            for error in formatted_response['ArgumentErrors']:
                raise ValidationError(
                    '%s: %s' % (error['ArgumentName'], error['ErrorMessage']),
                    code='argument_error'
                )
        if error_code != 0:
            print("Request to %s with params %s Failed with ErrorCode %s: %s" %
                  (response.original_request.path, response.original_request.params, error_code, formatted_response['ErrorMessage']))
            # Nathan, should I raise something here? or return some different response?
            # Not super sure how to do error handling so Im just printing for now
        return formatted_response


class BookerMerchantClient(BookerClient):
    base_url = 'https://stable-app.secure-booker.com/webservice4/json/BusinessService.svc'

    def get_locations(self):
        return self.post('/locations', {})
