import json
from requests import Request, Session
from django.conf import settings
from django.forms import ValidationError
from booking.models import Setting
from datetime import timedelta, datetime
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


class BookerCustomerClient(BookerClient):
    location_id = 29033  # From get location call, we should cache this for now
    customer_token = None
    customer_password = None
    user = None
    customer = None

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
        self.customer = response['Customer']
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
        response = BookerRequest('/customer/%s' % self.customer.booker_id, self.token, params).delete()
        return self.process_response(response)

    def get_availability(self, treatment_id, start_date, end_date):
        actual_product = [{'IsPackage': False,
                          'Treatments': [{'TreatmentID': treatment_id}]}]

        params = {'StartDateTime': "/Date(%s)/" % int(time.mktime(start_date.timetuple()) * 1000),
                  'EndDateTime': "/Date(%s)/" % int(time.mktime(end_date.timetuple()) * 1000),
                  'Itineraries': actual_product,
                  'LocationID': self.location_id}

        response = BookerRequest('/availability/multiservice', self.token, params).post()
        return self.process_response(response)

    def daterange(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    def parse_date(self, datestring):
        timepart = datestring.split('(')[1].split(')')[0]
        milliseconds = int(timepart[:-5])
        hours = int(timepart[-5:]) / 100
        timepart = milliseconds / 1000

        dt = datetime.utcfromtimestamp(timepart + hours * 3600)
        return dt

    def get_unavailable_days_in_range(self, treatment_id, start_date, end_date):
        print(end_date.strftime("%Y-%m-%d"))
        days = []
        for single_date in self.daterange(start_date, end_date + timedelta(days=1)):
            days.append(single_date.strftime("%Y-%m-%d"))

        days.append('2014-12-19')
        days = set(days)

        print('days is %s' % days)
        response = self.get_availability(treatment_id, start_date, end_date)
        for slot in response['ItineraryTimeSlotsLists'][0]['ItineraryTimeSlots']:
            date_key = self.parse_date(slot['StartDateTime']).strftime("%Y-%m-%d")
            print(date_key)
            days.remove(date_key)
        # for single_date in self.daterange(start_date, end_date):
        return days

    def get_available_times_for_day(self, treatment_id, start_date):
        times = []
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=0)
        response = self.get_availability(treatment_id, start_date, end_date)
        for slot in response['ItineraryTimeSlotsLists'][0]['ItineraryTimeSlots']:
            for timeslot in slot['TreatmentTimeSlots']:
                # print(timeslot)
                times.append(self.parse_date(timeslot['StartDateTime']).strftime("%I:%M %p"))
        # for single_date in self.daterange(start_date, end_date):
        return set(times)

    def book_appointment(self):
        # adjusted_customer = self.customer
        # adjusted_customer['Address'] = {
        #
        # }
        params = {
            'LocationID': self.location_id,
            'ItineraryTimeSlotList': {
                'IsPackage': False,
                'TreatmentTimeSlots': [
                    {
                        'CurrentPrice': {
                            'Amount': 0,
                            'CurrencyCode': ""
                        },
                        'Duration': None,
                        'EmployeeID': None,
                        'StartDateTime': None,
                        'TreatmentID': None
                    }
                ]
            },
            'AppointmentPayment': {
                'PaymentItem': {
                    'Amount': {
                        'Amount': 0,
                        'CurrencyCode': 'USD',
                    },

                },
                'CouponCode': ""
            },
            'Customer': self.customer
        }

        return BookerRequest('/appointment/create', self.customer_token, params).post
        
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
                    code='argumnet_error'
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
