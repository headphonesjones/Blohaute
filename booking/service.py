from django.conf import settings
from django.forms import ValidationError
from settings.models import Setting
import calendar
from booking.booker_client.dates import *
from booking.booker_client.merchant import BookerMerchantMixin
from booking.booker_client.customer import BookerCustomerMixin
from booking.booker_client.request import BookerRequest, BookerAuthedRequest, BookerMerchantRequest


class BookerClient(BookerMerchantMixin, BookerCustomerMixin, object):
    token = None

    CREDIT_CARD_TYPES = {
        4: 2,  # visa
        3: 1,  # american express
        2: 4,  # discover
        5: 3   # mastercard
    }

    location_id = 29033  # From get location call, we should cache this for now

    def __init__(self, token=None):
        if token is None:
            setting = self.get_settings_object()

            self.token = setting.access_token
            self.merchant_token = setting.merchant_access_token
            if self.token is None:
                self.load_token()
            if self.merchant_token is None:
                print('logging in merchant')
                self.login_merchant()

    def get_settings_object(self):
        setting = Setting.objects.first()
        if setting is None:
            setting = Setting()
        return setting

    def load_token(self):
        params = {'client_id': settings.BOOKER_API_KEY,
                  'client_secret': settings.BOOKER_API_SECRET,
                  'grant_type': 'client_credentials'}
        response = BookerRequest('/access_token', None, params).get()
        self.token = response.json()['access_token']
        setting = self.get_settings_object()
        setting.access_token = self.token
        setting.save()

    def resubmit_denied_request(self, response):
        new_request = response.original_request
        if new_request.original_params:
            new_request.params = new_request.original_params

        if isinstance(new_request, BookerAuthedRequest):
            self.login(self.user.email, self.customer_password)
            new_request.token = self.customer_token
        elif isinstance(new_request, BookerMerchantRequest):
            setting = self.get_settings_object()
            if self.merchant_token != setting.merchant_access_token:
                self.merchant_token = setting.merchant_access_token
            else:
                self.login_merchant()
            new_request.token = self.merchant_token
        else:
            setting = self.get_settings_object()
            if self.token != setting.access_token:
                self.token = setting.access_token
            else:
                self.load_token()
            new_request.token = self.token

        if new_request.method == 'GET':
            return self.process_response(new_request.get())
        if new_request.method == 'POST':
            return self.process_response(new_request.post())
        if new_request.method == 'PUT':
            return self.process_response(new_request.put())
        if new_request.method == 'DELETE':
            return self.process_response(new_request.delete())

    def process_response(self, response):
        formatted_response = response.json()
        error_code = formatted_response.get('ErrorCode', 0)
        if error_code == 1000:
            return self.resubmit_denied_request(response)
        if error_code == 200:
            for error in formatted_response['ArgumentErrors']:
                raise ValidationError(
                    '%s: %s' % (error['ArgumentName'], error['ErrorMessage']),
                    code='argument_error'
                )
        if error_code != 0:
            print("Request to %s with params %s Failed with ErrorCode %s: %s" %
                  (response.original_request.path, response.original_request.params, error_code,
                   formatted_response['ErrorMessage']))
        return formatted_response

    def date_range(self, start_date, end_date):
        for n in range(int((end_date - start_date).days)):
            yield start_date + timedelta(n)

    def credit_card_type(self, credit_card_number):
        first_character = int(credit_card_number[0])
        card_type = self.CREDIT_CARD_TYPES.get(first_character, None)
        return card_type

    def get_booker_credit_card_payment_item(self, billingzip, cccode, ccnum, expmonth, expyear,
                                            name_on_card):
        return {
            'Amount': {
                'Amount': 0.0,
                'CurrencyCode': 'USD'
            },
            'CreditCard': {
                'BillingZip': billingzip,
                'NameOnCard': name_on_card,
                'ExpirationDate': format_date_for_booker_json(
                    datetime(expyear, expmonth, calendar.monthrange(expyear, expmonth)[1])),
                'Number': ccnum,
                'SecurityCode': cccode,
                'Type': {
                    'ID': self.credit_card_type(ccnum),
                }
            },
            'Method': {
                'ID': 1,
            }
        }

    def get_booker_series_payment_item(self, series_id):
        return {
            'Amount': {
                'Amount': 0.0,
                'CurrencyCode': 'USD'
            },
            'CustomerSeries': {
                'SeriesID': series_id
            },
            'Method': {
                'ID': 5,
            }
        }
