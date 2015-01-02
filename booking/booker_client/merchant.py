from booking.booker_client.request import BookerMerchantRequest
from booking.models import Appointment, CustomerSeries
from django.conf import settings
from django.forms import ValidationError
from datetime import timedelta, datetime, date
from booking.booker_client.dates import *


# noinspection PyUnresolvedReferences
class BookerMerchantMixin(object):

    merchant_token = None
    merchant_user = settings.MERCHANT_USERNAME
    merchant_password = settings.MERCHANT_PASSWORD

    def get_locations(self):
        return BookerMerchantRequest('/locations', self.merchant_token).post()

    def check_coupon_code(self, coupon_code):
        params = {
            # 'LocationID': self.location_id,
            'CouponCode': coupon_code
            # 'ValidateSpecial': True
            # ,'BookingDate':
            # ,'AppointmentDate':
        }
        response = BookerMerchantRequest('/special/location/%s' % self.location_id, self.merchant_token, params).get(params)
        coupon_result = self.process_response(response)
        if coupon_result['IsSuccess']:
            coupon_result = {
                'description': coupon_result['Description'],
                'amount': coupon_result['DiscountAmount'],
                'available': coupon_result['AvailableRedemptions'],
                'name': coupon_result['Name']
            }
            print("Coupon result is %s for code %s" % (coupon_result, coupon_code))
            return coupon_result
        else:
            print("I don't know how to exception handle yet and we broke booking with result: %s" % coupon_result)
            return None

    def get_customer_series(self, treatment_id=None):
        """
        Gets a list series for the customer, optionally filtered by a specific treatment.
        """
        print 'performing merchant request'
        series_list = []
        params = {
            'LocationID': self.location_id,
            'CustomerID': self.customer_id
        }
        if treatment_id is not None:
            params['TreatmentID'] = treatment_id
        response = BookerMerchantRequest('/customer/series', self.merchant_token, params).post()
        customer_series = self.process_response(response)['Results']
        for series in customer_series:
            print(series)
            series_list.append(CustomerSeries(series['SeriesID'], series['Series']['Name'],
                               series['QuantityRemaining'], series['QuantityOriginal'],
                               series['ExpirationDate'], series['SeriesRedeemableItems']))

        return series_list

    def get_appointments(self):
        """
        get a list of currrent and past appointments for a specific location and customer
        """
        params = {
            'CustomerID': self.customer_id,
            'LocationID': self.location_id
        }
        response = BookerMerchantRequest('/appointments', self.merchant_token, params).post()
        appointment_results = self.process_response(response)
        result = [Appointment(itinerary) for itinerary in appointment_results['Results']]
        print result
        return result

    # def reschedule(self, appointment_id):
    #     params = {
    #         'CustomerID': self.customer_id,
    #         'LocationID': self.location_id
    #     }
    #     response = BookerMerchantRequest('/appointment/move', self.merchant_token, params).put()
    #     appointment_results = self.process_response(response)
    #     result = [Appointment(itinerary) for itinerary in appointment_results['Results']]
    #     print result
    #     return result

    def get_appointment(self, id):
        """
        get a single appointment by ID
        """
        params = {}
        response = BookerMerchantRequest('/appointment/%s' % id, self.merchant_token, params).get()
        return Appointment(self.process_response(response)['Appointment'])

    def book_appointment(self, itinerary, first_name, last_name, address, city, state, zipcode,
                         email, phone, payment_item, notes, coupon_code):
        # print("Booking with coupon code: %s" % coupon_code)
        if self.customer:
            adjusted_customer = self.customer.copy()
        else:
            adjusted_customer = {
                'LocationID': self.location_id,
                'Email': email,
                'FirstName': first_name,
                'LastName': last_name,
                'HomePhone': phone,
                'SendEmail': True
            }

        adjusted_customer['Address'] = {
            'Street1': address,
            'City': city,
            'State': state,
            'Zip': zipcode
        }

        if 'GUID' in adjusted_customer:
            adjusted_customer.pop('GUID')
        adjusted_customer['ID'] = self.customer_id

        # print("Adjusted customer is: %s" % adjusted_customer)
        treatments = []
        first_treatment = itinerary[0]
        for idx, treatment in enumerate(itinerary):

            end_time_json = format_date_for_booker_json(
                parse_date(treatment['StartDateTime']) + timedelta(minutes=treatment['Duration']))
            treatments.append({
                'TreatmentID': treatment['TreatmentID'],
                'StartTime': treatment['StartDateTime'],
                'RoomID': treatment['RoomID'],
                'EndTime': end_time_json,
                'EmployeeID': treatment['EmployeeID']
            })

        params = {
            'LocationID': self.location_id,
            'ResourceTypeID': 1,
            'AppointmentTreatmentDTOs': treatments,
            'AppointmentDate': first_treatment['StartDateTime'],
            'AppointmentPayment': {
                'CouponCode': coupon_code,
                'PaymentItem': payment_item
            },
            'Customer': adjusted_customer,
            'Notes': notes
        }

        print("BOOK PARAMS IS %s" % params)
        response = BookerMerchantRequest('/appointment', self.merchant_token, params).post()
        print(response)
        appointment = self.process_response(response)

        success = appointment['IsSuccess']
        if not success:
            print("On no, we died on booking, params was %s and appointment was %s" % (params, appointment))
            return None

        return Appointment(appointment['Appointment'])

    def cancel_appointment(self, appointment_id):
        params = {
            'ID': int(appointment_id)
        }
        response = BookerMerchantRequest('/appointment/cancel', self.merchant_token, params).put()
        print response.text
        return self.process_response(response)

    def change_appointment(self, itinerary, appointment):
        treatments = []
        first_treatment = itinerary[0]
        for idx, treatment in enumerate(itinerary):
            end_time_json = format_date_for_booker_json(
                parse_date(treatment['StartDateTime']) + timedelta(minutes=treatment['Duration']))
            treatments.append({
                'TreatmentID': treatment['TreatmentID'],
                'StartTime': treatment['StartDateTime'],
                'RoomID': treatment['RoomID'],
                'EndTime': end_time_json,
                'EmployeeID': treatment['EmployeeID']
            })
        customer_object = appointment.raw['Customer']
        if 'GUID' in customer_object:
            customer_object.pop('GUID')
        params = {
            'AppointmentDate': first_treatment['StartDateTime'],
            'AppointmentTreatmentDTOs': treatments,
            'Customer': customer_object,
            'ID': appointment.raw['ID'],
            'ResourceTypeID': 1
        }
        print("reschedule params: %s" % params)
        response = BookerMerchantRequest('/appointment', self.merchant_token, params).put()
        print("response for reschedule is %s" % response)
        appointment = self.process_response(response)

        success = appointment['IsSuccess']
        if not success:
            print("On no, we died on booking, params was %s and appointment was %s" % (params, appointment))
            return None

        return Appointment(appointment['Appointment'])

    def get_availability(self, treatment, start_date, end_date):
        params = {
            'LocationID': self.location_id,
            'ServiceID': treatment.booker_id,  # product.booker_id
            'ServiceTypeID': 1,
            'Quantity': 1,  # test if quantity would work and what it returns
            'StartDateTime': format_date_for_booker_json(start_date),
            'EndDateTime': format_date_for_booker_json(end_date),
        }
        print(params)
        request = BookerMerchantRequest('/availability/employee_room', self.merchant_token, params)
        response = request.post()
        return self.process_response(response)

    def get_available_times_for_day(self, treatments_requested, start_date):
        times = set()
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = start_date + timedelta(hours=6)  # time zone fix
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=0)
        end_date = end_date + timedelta(hours=6)  # time zone fix
        treatment = treatments_requested[0].product
        response = self.get_availability(treatment, start_date, end_date)

        # When more than one employee, that 0 below goes away and we iterate
        for itinerary_option in response['ItineraryTimeSlotsLists'][0]['ItineraryTimeSlots']:
            itin_time = parse_as_time(parse_date(itinerary_option['StartDateTime']))
            emp_list = set()
            for time_slot in itinerary_option['TreatmentTimeSlots']:
                emp_list.add(time_slot['EmployeeID'])
            times.add(itin_time)
        return list(times)

    def get_unavailable_days_in_range(self, treatments_requested, start_date, number_of_weeks):
        """
        Returns a list of python dates that are unavailable during the specified range
        """
        end_date = start_date + timedelta(weeks=number_of_weeks)
        days = [start_date + timedelta(days=x) for x in range((end_date - start_date).days + 1)]

        current_date = start_date
        treatment = treatments_requested[0].product
        for i in range(0, number_of_weeks):
            end_date = current_date + timedelta(weeks=1)
            response = self.get_availability(treatment, start_date, end_date)
            slots = response['ItineraryTimeSlotsLists'][0]['ItineraryTimeSlots']
            dates_to_remove = [parse_date(slot['StartDateTime']).date() for slot in slots]
            days = [day for day in days if day not in dates_to_remove]
            current_date = end_date
        print("days unavail is %s" % days)
        return days

    def get_unavailable_warm_period(self, treatments_requested):
        """
        Returns a list of python dates that are unavailable during the warm periond
        """
        return self.get_unavailable_days_in_range(treatments_requested, date.today(), 3)

    def get_itinerary_for_slot_multiple(self, treatments_requested, date, time_string):
        time_string = time_string.split(" ")[0]
        new_time = map(int, time_string.split(":"))
        start_date = datetime(date.year, date.month, date.day, new_time[0], new_time[1], 0, 0)
        # TODO: end_date should be start date + duration of appt
        end_date = start_date.replace(hour=23, minute=59, second=59, microsecond=0)
        end_date = end_date + timedelta(hours=6)  # time zone fix
        # print("start %r and end %r" % (start_date, end_date))

        total_treatments = 0
        for treatment in treatments_requested:
            total_treatments += treatment.quantity
        print("total treatments is %d" % total_treatments)
        response = self.get_availability(treatments_requested[0].product, start_date, end_date)

        # When more than one employee, that 0 below goes away and we iterate
        current_time_string = time_string
        times_to_slot_by_employee = {}
        employee_in_all_set = set()
        for itinerary_option in response['ItineraryTimeSlotsLists'][0]['ItineraryTimeSlots']:
            # avail_time_slot = AvailableTimeSlot()
            parsed_date = parse_date(itinerary_option['StartDateTime'])
            itin_time = parse_as_time(parsed_date)
            # parse_as_time(parse_date(itinerary_option['EndDateTime']))
            print(itin_time)
            if current_time_string == itin_time:
                print("match")
                new_date = parsed_date + timedelta(minutes=itinerary_option['TreatmentTimeSlots'][0]['Duration'])
                emp_list = set()
                for time_slot in itinerary_option['TreatmentTimeSlots']:
                    emp_list.add(time_slot['EmployeeID'])
                    times_to_slot_by_employee[current_time_string] = {time_slot['EmployeeID']: time_slot}
                if len(times_to_slot_by_employee.keys()) == 1:
                    employee_in_all_set.update(emp_list)
                else:
                    employee_in_all_set = employee_in_all_set.intersection(emp_list)
                if len(times_to_slot_by_employee.keys()) == total_treatments:
                    break
                current_time_string = parse_as_time(new_date)
            else:
                print("nope %s vs %s" % (current_time_string, itin_time))
        result = []
        if len(employee_in_all_set) <= 0:
            # what should we do here - this means no appointment is available with one employee for all services?
            print("No timeslot actually had the same employee back to back. We don't handle this yet")
        else:
            employee = employee_in_all_set.pop()
            for time in times_to_slot_by_employee:
                by_emp = times_to_slot_by_employee.get(time)
                for_emp = by_emp.get(employee)
                result.append(for_emp)
        return result

    def login_merchant(self):
        """
        Login a user to the API using their email and password
        """
        params = {'AccountName': 'blohauteil',
                  'UserName': self.merchant_user,
                  'Password': self.merchant_password,
                  'client_id': settings.BOOKER_API_KEY,
                  'client_secret': settings.BOOKER_API_SECRET}
        response = BookerMerchantRequest('/accountlogin', self.token, params)
        response = response.post()
        print("merchant login response is %r" % response)
        response = self.process_response(response)
        if response['access_token']:
            self.merchant_token = response['access_token']
            setting = self.get_settings_object()
            setting.merchant_access_token = self.merchant_token
            print("merch token is %s" % self.merchant_token)
            setting.save()
        else:
            raise ValidationError(response['error'])

        return response['access_token']
