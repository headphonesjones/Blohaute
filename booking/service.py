import json
import requests
from django.conf import settings
from django.forms import ValidationError
from booking.models import Setting


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
        print("response was %s" % response.json())
        return response.json()

    def delete(self, path, params):
        headers = {'content-type': 'application/json'}
        request_url = "%s%s" % (self.base_url, path)
        response = requests.delete(request_url, data=json.dumps(params), headers=headers)
        print("response was %s" % response.json())
        return response.json()


class BookerClient(Client):
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
        response = super(BookerClient, self).get('/access_token', params=params)
        self.token = response['access_token']
        if setting is None:
            setting = self.get_settings_object()
        setting.access_token = self.token
        setting.save()

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
        #let the caller override access token
        params['access_token'] = params.get('access_token', self.token)

        response = super(BookerClient, self).post(path, params)
        error_code = response['ErrorCode']
        if error_code == 1000:
            self.load_token()
            response = super(BookerClient, self).post(path, params)
        if error_code == 200:
            for error in response['ArgumentErrors']:
                raise ValidationError(
                    '%s: %s' % (error['ArgumentName'], error['ErrorMessage']),
                    code='argumnet_error'
                )
        if error_code != 0:
            print("Request to %s with params %s Failed with ErrorCode %s: %s" %
                  (path, params, error_code, response['ErrorMessage']))
            # Nathan, should I raise something here? or return some different response?
            # Not super sure how to do error handling so Im just printing for now
        return response

    def delete(self, path, params):
        #let the caller override access token
        params['access_token'] = params.get('access_token', self.token)

        response = super(BookerClient, self).delete(path, params)
        error_code = response['ErrorCode']
        print response
        if error_code == 1000:
            self.load_token()
            response = super(BookerClient, self).delete(path, params)
        if error_code == 200:
            for error in response['ArgumentErrors']:
                raise ValidationError(
                    '%s: %s' % (error['ArgumentName'], error['ErrorMessage']),
                    code='argumnet_error'
                )
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
    customer_token = None
    customer_password = None

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
        response = self.post('/customer/account', params)
        return response

    def login(self, email, password):
        params = {'LocationID': self.location_id,
                  'Email': email,
                  'Password': password,
                  'client_id': settings.BOOKER_API_KEY,
                  'client_secret': settings.BOOKER_API_SECRET}
        response = Client.post(self, '/customer/login', params)
        self.customer_token = response['access_token']
        return response['access_token']

    def logout(self):
        params = {'access_token': self.customer_token}
        Client.get(self, '/logout', params=params)

    def update_password(self, customer_id, email, old_password, new_password):
        params = {'LocationID': self.location_id,
                  'Email': email,
                  'NewPassword': new_password,
                  'OldPassword': old_password,
                  'access_token': self.customer_token,
                  'CustomerID': customer_id
                  }

        response = Client.post(self, '/customer/password', params)
        return response

    #this seems to always fail on invalid token
    def delete_customer(self, customer_id):
        params = {'CustomerID': customer_id, 'access_token': self.customer_token}
        response = self.delete('/customer/%s' % customer_id, params)
        return response

    def get_availability(self, treatment_id, start_date, end_date):
        actual_product = {'IsPackage': False,
                          'Treatments': {'TreatmentID': treatment_id}}

        params = {'StartDateTime': start_date.strftime('%Y%m%d'),
                  'EndDateTime': end_date.strftime('%Y%m%d'),
                  'Itineraries': actual_product}

        return self.delete('/availability/multiservice', params)

    def post(self, path, params):
        params['LocationID'] = self.location_id
        # TODO:
        # params['LocationID'] = settings.BLOHAUTE_LOCATION_ID
        return super(BookerCustomerClient, self).post(path, params)
