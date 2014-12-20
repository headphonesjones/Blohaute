import json
from requests import Request, Session
from django.conf import settings
from django.forms import ValidationError
from booking.models import Setting, Treatment
from datetime import timedelta, datetime, date
import calendar
import time


class BookerRequest(Request):
    """
    Sets up, sends, and processes a single request to the Booker API
    """
    base_url = None
    path = None
    method = None
    params = {}
    needs_user_token = False
    token = None

    def __init__(self, base_url, path, token, params={}):
        headers = {'content-type': 'application/json'}
        super(BookerRequest, self).__init__(params=params, headers=headers)
        self.base_url = base_url
        self.path = path
        if token:
            self.token = token

    def send(self):
        self.url = "%s%s" % (self.base_url, self.path)
        prepped = self.prepare()
        s = Session()
        # print(self.data)
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

    def put(self):
        self.method = 'PUT'
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
    CREDIT_CARD_TYPES = {
        4: 2,  # visa
        3: 1,  # american express
        2: 4,  # discover
        5: 3   # mastercard
    }

    token = None
    location_id = 29033  # From get location call, we should cache this for now

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
        response = BookerRequest(self.base_url, '/access_token', None, params).get()
        self.token = response.json()['access_token']
        if setting is None:
            setting = self.get_settings_object()
        setting.access_token = self.token
        setting.save()

    def parse_as_time(self, date_time):
        return date_time.strftime("%H:%M")

    def parse_as_date(self, date_time):
        return date_time.strftime("%Y-%m-%d")

    def format_date_for_booker_json(self, start_date):
        return "/Date(%s%s)/" % (int(time.mktime(start_date.timetuple()) * 1000), "-0500")

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

    def credit_card_type(self, credit_card_number):
        first_character = int(credit_card_number[0])
        card_type = self.CREDIT_CARD_TYPES.get(first_character, None)
        return card_type

    def get_booker_credit_card_payment_item(self, billingzip, cccode, ccnum, expmonth, expyear, name_on_card):
        return {
            'Amount': {
                'Amount': 0.0,
                'CurrencyCode': 'USD'
            },
            'CreditCard': {
                'BillingZip': billingzip,
                'NameOnCard': name_on_card,
                'ExpirationDate': self.format_date_for_booker_json(
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


class AppointmentResult(object):
    def __init__(self):
        self.upcoming = []
        self.past = []


class Appointment(object):
    appointment_id = None
    time = None
    date = None
    treatment = None

    def __init__(self, appointment_id, appt_time, date, service_id, service_name):
        self.appointment_id = appointment_id
        self.date = date
        self.time = appt_time
        self.treatment_id = service_id
        self.treatment_name = service_name
        self.treatment = Treatment.objects.filter(booker_id=service_id)

    def __str__(self):
        return self.treatment + " at " + self.time + " on " + self.date


class CustomerSeries(object):
    series_id = None
    name = None
    quantity = None
    remaining = None
    expiration = None
    redeemable_items = None
    treatment = None

    def __init__(self, series_id, name, quantity, remaining, expiration, redeemable):
        self.series_id = series_id
        self.name = name
        self.quantity = quantity
        self.remaining = remaining
        # self.expiration = expiration
        self.redeemable_items = redeemable
        treatment_id = self.redeemable_items[0]['TreatmentID']
        self.treatment = Treatment.objects.get(booker_id=treatment_id)

    def __str__(self):
        if self.expiration is None:
            self.expiration = "Never"
        return self.name + " " + str(self.remaining) + " of " + str(self.quantity)


class BookerCustomerClient(BookerClient):
    base_url = 'https://stable-app.secure-booker.com/webservice4/json/CustomerService.svc'
    customer_token = None
    customer_password = None
    user = None
    customer = None
    customer_id = None

    def get_server_information(self):
        response = BookerRequest(self.base_url, '/server_information', self.token, {}).get()
        return self.process_response(response)

    def get_services(self):
        """
        Returns treatments for a spa/location
        """
        params = {'LocationID': self.location_id}
        response = BookerRequest(self.base_url, '/treatments', self.token, params).post()
        return self.process_response(response)['Treatments']

    def get_packages(self):
        """
        Returns packages for a spa/location
        """
        params = {'LocationID': self.location_id}
        response = BookerRequest(self.base_url, '/series', self.token, params).post()
        return self.process_response(response)['Results']

    def get_memberships(self):
        """
        Returns memberships for a spa/location
        """
        params = {'LocationID': self.location_id}
        response = BookerRequest(self.base_url, '/memberships', self.token, params).post()
        return self.process_response(response)['Results']

    def get_series(self):
        params = {'LocationID': self.location_id}
        response = BookerRequest(self.base_url, '/series', self.token, params).post()
        return self.process_response(response)['Results']

    def get_customer_series(self, treatment_id=None):
        series_list = []
        params = {
            'LocationID': self.location_id,
            'CustomerID': self.customer_id
        }
        if treatment_id is not None:
            params['TreatmentID'] = treatment_id
        response = BookerAuthedRequest(self.base_url, '/customer/series', self.customer_token, params).post()
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
        response = BookerRequest(self.base_url, '/employees', self.token, {'LocationID': self.location_id}).post()
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
        response = BookerRequest(self.base_url, '/customer/account', self.token, params).post()
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
        response = BookerRequest(self.base_url, '/customer/login', self.token, params).post()
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
        response = BookerAuthedRequest(self.base_url, '/logout', self.customer_token, None).get()
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

        response = BookerAuthedRequest(self.base_url, '/customer/password', self.customer_token, params).post()
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
        response = BookerAuthedRequest(self.base_url, '/customer/%s' % self.customer_id, self.customer_token, params).put()
        return self.process_response(response)

    def reset_password(self, email, first_name):
        """
        resets a forgotten customer password
        """
        params = {'FirstName': first_name,
                  'LocationID': self.location_id,
                  'Email': email}
        response = BookerRequest('/forgot_password/custom', self.token, params).post()
        print response.text
        return self.process_response(response)
       
    def delete_customer(self):
        """
        Delete a customer
        This doesn't seem to work
        """
        params = {'CustomerID': self.customer.booker_id}
        response = BookerRequest(self.base_url, '/customer/%s' % self.customer_id, self.token, params).delete()
        return self.process_response(response)

    def get_appointments(self):
        """
        get a list of currrent and past customer appointments for a specific location
        """
        params = {
            'CustomerID': self.customer_id,
            'LocationID': self.location_id
        }
        response = BookerAuthedRequest(self.base_url, '/appointments', self.customer_token, params).post()
        appointment_results = self.process_response(response)
        result = AppointmentResult()
        for itinerary in appointment_results['Results']:
            for appointment in itinerary['AppointmentTreatments']:
                if itinerary['Status']['ID'] != 6:
                    appointment_id = appointment['AppointmentID']
                    start_time = self.parse_date(appointment['StartDateTime'])
                    appointment_result = Appointment(appointment_id,
                                                     self.parse_as_time(start_time),
                                                     self.parse_as_date(start_time),
                                                     appointment['Treatment']['ID'],
                                                     appointment['Treatment']['Name'])
                    if datetime.now() - start_time > timedelta(minutes=5):
                        result.past.append(appointment_result)
                    else:
                        result.upcoming.append(appointment_result)

        return result

    def cancel_appointment(self, appointment_id):
        params = {
            'ID': appointment_id
        }
        response = BookerAuthedRequest(self.base_url, '/appointment/cancel', self.customer_token, params).put()
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

        params = {'StartDateTime': self.format_date_for_booker_json(start_date),
                  'EndDateTime': self.format_date_for_booker_json(end_date),
                  'Itineraries': itinerary,
                  'LocationID': self.location_id}

        response = BookerRequest(self.base_url, '/availability/multiservice', self.token, params).post()
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
            dates_to_remove = [self.parse_date(slot['StartDateTime']).date() for slot in slots]
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
            itin_time = self.parse_as_time(self.parse_date(itinerary_option['StartDateTime']))
            # avail_time_slot.raw_time = itin_time
            # avail_time_slot.pretty_time = self.parse_as_time(itin_time)
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
        start_date = datetime(date.year, date.month, date.day, new_time[0]-1, new_time[1], 0, 0)
        print(start_date)
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=0)
        response = self.get_availability(treatments_requested, start_date, end_date)

        # When more than one employee, that 0 below goes away and we iterate
        for itinerary_option in response['ItineraryTimeSlotsLists'][0]['ItineraryTimeSlots']:
            # avail_time_slot = AvailableTimeSlot()
            itin_time = self.parse_as_time(self.parse_date(itinerary_option['StartDateTime']))
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

        response = BookerAuthedRequest(self.base_url, '/appointment/create', self.customer_token, params).post()
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
        response = BookerAuthedRequest(self.base_url, '/series/purchase', self.customer_token, params).post()
        return self.process_response(response)

    def process_response(self, response):
        formatted_response = response.json()
        error_code = formatted_response.get('ErrorCode', 0)
        if error_code == 1000:
            self.load_token()
            if response.needs_user_token:
                self.login(self.user.email, self.customer_password)
                new_request = BookerAuthedRequest(self.base_url, response.original_request.path, self.customer_token)
            else:
                new_request = BookerRequest(self.base_url, response.original_request.path, self.token)
            new_request.method = response.original_request.method
            if new_request.method == 'GET':
                new_request.params = response.original_request.params or {}
                return self.process_response(new_request.get())
            else:
                new_request.params = response.original_request.original_params or {}
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
                  (response.original_request.path, response.original_request.params, error_code,
                   formatted_response['ErrorMessage']))
        return formatted_response


class BookerMerchantClient(BookerClient):
    base_url = 'https://stable-app.secure-booker.com/webservice4/json/BusinessService.svc'
    merchant_token = None
    merchant_password = 'Test123!'
    merchant_user = 'blohauteweb'

    def get_locations(self):
        return BookerRequest(self.base_url, '/locations', self.token).post()

    def book_appointment(self, itinerary, customer, first_name, last_name, address, city, state, zipcode,
                         email, phone, ccnum, name_on_card, expyear, expmonth, cccode, billingzip, notes):
        if customer:
            adjusted_customer = customer.copy()
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
            'City': city,
            'State': state,
            'Zip': zipcode
        }

        adjusted_customer.pop('GUID')
        appt = itinerary[0]['TreatmentTimeSlots'][0]
        print(appt)
        params = {
            'LocationID': self.location_id,
            'ResourceTypeID': 1,
            'AppointmentTreatmentDTOs': [
                {
                    'TreatmentID': appt['TreatmentID'],
                    'StartTime': appt['StartDateTime'],
                    'RoomID': appt['RoomID'],
                    'EmployeeID': appt['EmployeeID']
                    # ,
                    # 'GapFinishDuration': 0,  # for multi appts no time between, recovery time after
                    # 'RecoveryTime': 0    #  for non final treatment 0 then 45 on last treatment
                }
            ],
            'AppointmentDate': appt['StartDateTime'],  # Date needs to be itinerary start date
            'AppointmentPayment': {
                'CouponCode': '',
                'PaymentItem': self.get_booker_credit_card_payment_item(billingzip, cccode, ccnum, expmonth, expyear,
                                                                        name_on_card)
            },
            'Customer': adjusted_customer,
            'Notes': notes
        }

        # print(params)

        response = BookerAuthedRequest(self.base_url, '/appointment/create', self.merchant_token, params).post()
        print("book response %s" % response)
        return self.process_response(response)

    def get_availability(self, treatment, start_date, end_date):
        # for treatment in treatments:
        # if isinstance(treatment.product, Treatment):
        params = {
            'LocationID': self.location_id,
            'ServiceID': treatment.booker_id,  # product.booker_id
            'Quantity': 2,  # test if quantity would work and what it returns
            'StartDateTime': self.format_date_for_booker_json(start_date),
            'EndDateTime': self.format_date_for_booker_json(end_date),
        }
        request = BookerAuthedRequest(self.base_url, '/availability/employee_room', self.merchant_token, params)
        response = request.post()
        print(response)
        return self.process_response(response)

    def get_available_slots_for_day(self, treatment, date):
        start_date = datetime.strptime(date, '%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=0)
        availability = self.get_availability(treatment, start_date, end_date)
        print("processed is :  %r" % availability)

        times = set()
        for slot in availability['ItineraryTimeSlotsLists'][0]['ItineraryTimeSlots']:
            times.add(self.parse_as_time(self.parse_date(slot['StartDateTime'])))
            # for tslot in slot['TreatmentTimeSlots']:
                # print(tslot['EmployeeID'])
        print(times)
        return list(times)

    def get_available_times_for_day(self, treatment, start_date):
        times = []
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=0)
        response = self.get_availability(treatment, start_date, end_date)

        # When more than one employee, that 0 below goes away and we iterate
        for itinerary_option in response['ItineraryTimeSlotsLists'][0]['ItineraryTimeSlots']:
            # avail_time_slot = AvailableTimeSlot()
            itin_time = self.parse_as_time(self.parse_date(itinerary_option['StartDateTime']))
            # avail_time_slot.raw_time = itin_time
            # avail_time_slot.pretty_time = self.parse_as_time(itin_time)
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

    def process_response(self, response):
        formatted_response = response.json()
        error_code = formatted_response.get('ErrorCode', 0)
        if error_code == 1000:
            self.load_token()
            if response.needs_user_token:
                self.login()
                new_request = BookerAuthedRequest(self.base_url, response.original_request.path, self.merchant_token)
            else:
                new_request = BookerRequest(self.base_url, response.original_request.path, self.token)
            new_request.method = response.original_request.method
            if new_request.method == 'GET':
                new_request.params = response.original_request.params or {}
                return self.process_response(new_request.get())
            else:
                new_request.params = response.original_request.original_params or {}
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
                  (response.original_request.path, response.original_request.params, error_code,
                   formatted_response['ErrorMessage']))
        return formatted_response

    def login(self):
        """
        Login a user to the API using their email and password
        """
        params = {'AccountName': 'blohauteil',
                  'UserName': self.merchant_user,
                  'Password': self.merchant_password,
                  'client_id': settings.BOOKER_API_KEY,
                  'client_secret': settings.BOOKER_API_SECRET}
        response = BookerRequest(self.base_url, '/accountlogin', self.token, params)
        response = response.post()
        print("response is %r" % response)
        response = self.process_response(response)
        if response['access_token']:
            self.merchant_token = response['access_token']
        else:
            raise ValidationError(response['error'])

        return response['access_token']
