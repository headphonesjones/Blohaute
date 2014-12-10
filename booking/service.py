import json
import requests
from django.conf import settings


class BookerClient(object):
    token = None
    base_url = None

    def __init__(self):
        self.load_token()

    def load_token(self):
        params = {'client_id': settings.BOOKER_API_KEY,
                  'client_secret': settings.BOOKER_API_SECRET,
                  'grant_type': 'client_credentials'
                  }

        request = requests.get("%s/access_token" % self.base_url, params=params)
        self.token = request.json()['access_token']

    def post(self, path, params):
        params['access_token'] = self.token
        headers = {'content-type': 'application/json'}
        request_url = "%s%s" % (self.base_url, path)
        request = requests.post(request_url, data=json.dumps(params), headers=headers)
        return request.json()


class BookerCustomerClient(BookerClient):
    base_url = 'https://stable-app.secure-booker.com/webservice4/json/CustomerService.svc'
    location_id = None

    def get_services(self):
        params = {}
        return self.post('/treatments', params)

    def get_packages(self):
        params = {}
        return self.post('/series', params)

    def get_availability(self, treatment_id, start_date, end_date):
        actual_product = {'IsPackage': False,
                          'Treatments': {'TreatmentID': treatment_id}
                          }

        params = {'StartDateTime': start_date.strftime('%Y%m%d'),
                  'EndDateTime': end_date.strftime('%Y%m%d'),
                  'Itineraries': actual_product
                  }

        return self.post('/availability/multiservice', params)

    def post(self, path, params):
        params['LocationID'] = self.location_id
        super(BookerCustomerClient, self).post(path, params)


class BookerMerchantClient(BookerClient):
    base_url = 'https://stable-app.secure-booker.com/webservice4/json/BusinessService.svc'

    def get_locations(self):
        params = {}
        return self.post('/locations', params)
