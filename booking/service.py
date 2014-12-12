import json
import requests
from django.conf import settings


class Client(object):
    base_url = None

    def get(self, path, params):
        request_url = "%s%s" % (self.base_url, path)
        response = requests.get(request_url, params=params)
        return response.json()

    def post(self, path, params):
        headers = {'content-type': 'application/json'}
        request_url = "%s%s" % (self.base_url, path)
        response = requests.post(request_url, data=json.dumps(params), headers=headers)
        return response.json()


class BookerClient(Client):
    token = None

    def __init__(self):
        self.load_token()

    def load_token(self):
        params = {'client_id': settings.BOOKER_API_KEY,
                  'client_secret': settings.BOOKER_API_SECRET,
                  'grant_type': 'client_credentials'}
        response = super(BookerClient, self).get('/access_token', params=params)
        self.token = response['access_token']

    def get(self, path, params):
        response = super(BookerClient, self).get(path, params)
        error_code = response['ErrorCode']
        if error_code == 1000:
            self.load_token()
            response = super(BookerClient, self).get(path, params)
        if error_code != 0:
            print("Request to %s with params %s Failed with ErrorCode %s: %s" %
                  (path, params, error_code, response['ErrorMessage']))
        return response

    def post(self, path, params):
        params['access_token'] = self.token
        response = super(BookerClient, self).post(path, params)
        error_code = response['ErrorCode']
        if error_code == 1000:
            self.load_token()
            response = super(BookerClient, self).post(path, params)
        if error_code != 0:
            print("Request to %s with params %s Failed with ErrorCode %s: %s" %
                  (path, params, error_code, response['ErrorMessage']))
            # Nathan, should I raise something here? or return some different response?
            # Not super sure how to do error handling so Im just printing for now
        return response


class BookerMerchantClient(BookerClient):
    base_url = 'https://stable-app.secure-booker.com/webservice4/json/BusinessService.svc'

    def get_locations(self):
        return self.post('/locations', {})


class BookerCustomerClient(BookerClient):
    base_url = 'https://stable-app.secure-booker.com/webservice4/json/CustomerService.svc'
    location_id = 29033  # From get location call, we should cache this for now

    def get_services(self):
        return self.post('/treatments', {})

    def get_packages(self):
        return self.post('/series', {})

    def create_user(self, email, password, fname, lname, phone):
        params = {'Email': email,
                  'Password': password,
                  'FirstName': fname,
                  'LastName': lname,
                  'HomePhone': phone,
                  'Address': {'Street1': None}}
        return self.post('/customer/account', params)

    def get_availability(self, treatment_id, start_date, end_date):
        actual_product = {'IsPackage': False,
                          'Treatments': {'TreatmentID': treatment_id}}

        params = {'StartDateTime': start_date.strftime('%Y%m%d'),
                  'EndDateTime': end_date.strftime('%Y%m%d'),
                  'Itineraries': actual_product}

        return self.post('/availability/multiservice', params)

    def post(self, path, params):
        params['LocationID'] = self.location_id
        # TODO:
        # params['LocationID'] = settings.BLOHAUTE_LOCATION_ID
        return super(BookerCustomerClient, self).post(path, params)
