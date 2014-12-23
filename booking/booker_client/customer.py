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

    def get_customer_series(self, treatment_id=None):
        """
        Gets a list series for the customer, optionally filtered by a specific treatmetn
        Replaced by the get customer series method in merchant.
        """
        series_list = []
        params = {
            'LocationID': self.location_id,
            'CustomerID': self.customer_id
        }
        if treatment_id is not None:
            params['TreatmentID'] = treatment_id
        response = BookerAuthedRequest('/customer/series', self.customer_token, params).post()
        customer_series = self.process_response(response)['Results']
        for series in customer_series:
            print(series)
            series_list.append(CustomerSeries(series['SeriesID'], series['Series']['Name'],
                               series['QuantityRemaining'], series['QuantityOriginal'],
                               series['ExpirationDate'], series['SeriesRedeemableItems']))

        return series_list

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

    def reset_password(self, email, first_name):
        """
        resets a forgotten customer password
        """
        params = {'Firstname': first_name,
                  'LocationID': self.location_id,
                  'Email': email,
                  'BaseUrlOfHost': "http://blohaute.com%s" % reverse('reset_password')
                  }
        response = BookerRequest('/forgot_password/custom', self.token, params).post()
        print response.text
        return self.process_response(response)

    def delete_customer(self):
        """
        Delete a customer
        This doesn't seem to work
        """
        params = {'CustomerID': self.customer.booker_id}
        response = BookerRequest('/customer/%s' % self.customer_id, self.token, params).delete()
        return self.process_response(response)

    def cancel_appointment(self, appointment_id):
        params = {
            'ID': int(appointment_id)
        }
        print appointment_id
        response = BookerAuthedRequest('/appointment/cancel', self.customer_token, params).put()
        print response.text
        return self.process_response(response)

    # def reschedule_appointment(self):

    def get_availability(self, treatments_requested, start_date, end_date):
        treatments = []
        for treatment in treatments_requested:
            if isinstance(treatment.product, Treatment):
                for i in range(0, treatment.quantity):
                    treatments.append({'TreatmentID': treatment.product.booker_id})

        itinerary = [{'IsPackage': False,
                      'Treatments': treatments}]

        params = {'StartDateTime': format_date_for_booker_json(start_date),
                  'EndDateTime': format_date_for_booker_json(end_date),
                  'Itineraries': itinerary,
                  'LocationID': self.location_id}

        response = BookerRequest('/availability/multiservice', self.token, params).post()
        # print(response)
        return self.process_response(response)

    def get_unavailable_days_in_range(self, treatments_requested, start_date, number_of_weeks):
        """
        Returns a list of python dates that are unavailable during the specified range
        """
        end_date = start_date + timedelta(weeks=number_of_weeks)
        days = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

        current_date = start_date
        for i in range(0, number_of_weeks):
            end_date = current_date + timedelta(weeks=1)
            response = self.get_availability(treatments_requested, current_date, end_date)
            slots = response['ItineraryTimeSlotsLists'][0]['ItineraryTimeSlots']
            dates_to_remove = [parse_date(slot['StartDateTime']).date() for slot in slots]
            days = [day for day in days if day not in dates_to_remove]
            current_date = end_date
        return days

    def get_unavailable_warm_period(self, treatments_requested):
        """
        Returns a list of python dates that are unavailable during the warm periond
        """
        return self.get_unavailable_days_in_range(treatments_requested, date.today(), 3)

    def get_available_times_for_day(self, treatments_requested, start_date):
        times = []
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=0)
        response = self.get_availability(treatments_requested, start_date, end_date)

        # When more than one employee, that 0 below goes away and we iterate
        for itinerary_option in response['ItineraryTimeSlotsLists'][0]['ItineraryTimeSlots']:
            # avail_time_slot = AvailableTimeSlot()
            itin_time = parse_as_time(parse_date(itinerary_option['StartDateTime']))
            # avail_time_slot.raw_time = itin_time
            # avail_time_slot.pretty_time = parse_as_time(itin_time)
            # print("timeslot: %s and item %s" % (avail_time_slot.pretty_time, itinerary_option))
            emp_list = set()
            for time_slot in itinerary_option['TreatmentTimeSlots']:
                emp_list.add(time_slot['EmployeeID'])
            # print(" slot %s with employee list %r" % (avail_time_slot.pretty_time, emp_list))

            # if len(emp_list) == 1:

                # avail_time_slot.single_employee_slots.append(itinerary_option)
            times.append(itin_time)
            # elif len(emp_list) == 2:  # Just 2 for now to handle services where one employee doesnt do both only use the singles for now
            #     avail_time_slot.multiple_employee_slots.append(itinerary_option)
        return times

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

    def book_appointment(self, itinerary, first_name, last_name, address, city, state, zipcode,
                         email, phone, ccnum, name_on_card, expyear, expmonth, cccode, billingzip, notes):
        if self.customer:
            adjusted_customer = self.customer.copy()
        else:
            adjusted_customer = {
                'LocationID': self.location_id,
                'Email': email,
                'FirstName': first_name,
                'LastName': last_name,
                'HomePhone': phone
            }

        adjusted_customer['Address'] = {
            'Street1': address,
            # 'Street2': notes,
            'City': city,
            'State': state,
            'Zip': zipcode
        }

        adjusted_customer.pop('GUID')
        params = {
            'LocationID': self.location_id,
            'ItineraryTimeSlotList': [itinerary],
            'AppointmentPayment': {
                'CouponCode': '',
                'PaymentItem': self.get_booker_credit_card_payment_item(billingzip, cccode, ccnum, expmonth, expyear,
                                                                        name_on_card)
            },
            'Customer': adjusted_customer,
            'Notes': notes
        }

        # print(params)

        response = BookerAuthedRequest('/appointment/create', self.customer_token, params).post()
        print("book response %s" % response)
        return self.process_response(response)

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
