from booking.booker_client.request import BookerRequest, BookerAuthedRequest
from booking.models import Treatment, CustomerSeries
from django.conf import settings
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from datetime import date
from booking.booker_client.dates import *


class BookerCustomerMixin(object):
    customer_token = None
    customer_password = None

    user = None
    customer = None
    customer_id = None

    def get_server_information(self):
        """
        Returns server time zone information
        """
        response = BookerRequest('/server_information', self.token, {}).get()
        return self.process_response(response)

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
        params = {'LocationID': self.location_id}
        response = BookerRequest('/series', self.token, params).post()
        return self.process_response(response)['Results']

    def get_memberships(self):
        """
        Returns memberships for a spa/location
        """
        params = {'LocationID': self.location_id}
        response = BookerRequest('/memberships', self.token, params).post()
        return self.process_response(response)['Results']

    def get_series(self):
        params = {'LocationID': self.location_id}
        response = BookerRequest('/series', self.token, params).post()
        return self.process_response(response)['Results']

    def get_employees(self):
        """
        Returns employees for a spa/location
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
        if response['access_token']:
            self.customer_token = response['access_token']
            self.customer_password = password
            self.customer = response['Customer']['Customer']
            self.customer_id = response['Customer']['CustomerID']
        else:
            raise ValidationError(response['error'])

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
        self.customer_password = new_password
        return self.process_response(response)

    def update_email(self, email):
        """
        updates email on a customer
        """
        params = {'LocationID': self.location_id,
                  'Email': email,
                  'FirstName': self.user.first_name,
                  'LastName': self.user.last_name,
                  'HomePhone': self.user.phone_number,
                  'Address': self.customer['Address'],
                  'CustomerID': self.customer_id}
        response = BookerAuthedRequest('/customer/%s' % self.customer_id, self.customer_token, params).put()
        return self.process_response(response)

    def send_reset_password_link(self, email, first_name):
        """
        sends an email to allow the user to reset their password
        """
        params = {'Firstname': first_name,
                  'LocationID': self.location_id,
                  'Email': email,
                  'BaseUrlOfHost': "http://blohaute.com%s" % reverse('reset_password')
                  }
        response = BookerRequest('/forgot_password/custom', self.token, params).post()
        return self.process_response(response)

    def reset_password(self, key, password):
        """
        resets a forgotten customer password
        """
        params = {'Key': key,
                  'Password': password,
          }
        response = BookerRequest('/password/reset', self.token, params).post()
        return self.process_response(response)

    def delete_customer(self):
        """
        Delete a customer
        This doesn't seem to work
        """
        params = {'CustomerID': self.customer.booker_id}
        response = BookerRequest('/customer/%s' % self.customer_id, self.token, params).delete()
        return self.process_response(response)

    def get_availability_multiservice(self, treatments_requested, start_date, end_date):
        treatments = [{'TreatmentID': treatment.booker_id} for treatment in treatments_requested]
        itinerary = [{'IsPackage': False,
                      'Treatments': treatments}]

        params = {'StartDateTime': format_date_for_booker_json(start_date),
                  'EndDateTime': format_date_for_booker_json(end_date),
                  'Itineraries': itinerary,
                  'LocationID': self.location_id}

        response = BookerRequest('/availability/multiservice', self.token, params).post()
        # print(response)
        return self.process_response(response)

    def get_itinerary_for_slot(self, treatments_requested, date, time_string):
        time_string = time_string.split(" ")[0]
        new_time = map(int, time_string.split(":"))
        print("time %s" % new_time)
        start_date = datetime(date.year, date.month, date.day, new_time[0] - 1, new_time[1], 0, 0)
        print(start_date)
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=0)
        response = self.get_availability(treatments_requested, start_date, end_date)

        # When more than one employee, that 0 below goes away and we iterate
        for itinerary_option in response['ItineraryTimeSlotsLists'][0]['ItineraryTimeSlots']:
            # avail_time_slot = AvailableTimeSlot()
            itin_time = parse_as_time(parse_date(itinerary_option['StartDateTime']))
            if time_string == itin_time:
                # emp_list = set()
                # for time_slot in itinerary_option['TreatmentTimeSlots']:
                #     emp_list.add(time_slot['EmployeeID'])
                return itinerary_option
                # break
            else:
                print("nope %s vs %s" % (new_time, itin_time))
        return None

    def buy_series(self, series_id, ccnum, name_on_card, expyear, expmonth, cccode, billingzip):
        params = {
            'LocationID': self.location_id,
            'CustomerID': self.customer_id,
            'CustomerFirstName': self.customer['FirstName'],
            'CustomerLastName': self.customer['LastName'],
            'CustomerPhone': self.customer['HomePhone'],
            # 'CustomerPhone': self.user.phone_number,
            'CustomerEmail': self.customer['Email'],
            # 'CustomerEmail': self.user.email,
            'PaymentItem': self.get_booker_credit_card_payment_item(billingzip, cccode, ccnum, expmonth, expyear,
                                                                    name_on_card),
            'SeriesID': series_id
        }
        response = BookerAuthedRequest('/series/purchase', self.customer_token, params).post()
        return self.process_response(response)
