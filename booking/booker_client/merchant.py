from booking.booker_client.request import BookerMerchantRequest
from booking.models import AppointmentResult, Appointment, CustomerSeries
from django.conf import settings
from django.forms import ValidationError
from datetime import timedelta, datetime, date


class BookerMerchantMixin(object):

    merchant_token = None
    merchant_password = 'Test123!'
    merchant_user = 'blohauteweb'

    def get_locations(self):
        return BookerMerchantRequest('/locations', self.merchant_token).post()

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
                'HomePhone': phone,
                'SendEmail': True
            }

        adjusted_customer['Address'] = {
            'Street1': address,
            'City': city,
            'State': state,
            'Zip': zipcode
        }

        adjusted_customer.pop('GUID')
        params = {
            'LocationID': self.location_id,
            'ResourceTypeID': 1,
            'AppointmentTreatmentDTOs': [
                {
                    'TreatmentID': 0,
                    'StartTime': 0,
                    'RoomID': None,
                    'EndTime': 0,
                    'EmployeeID': 0
                    # ,
                    # 'GapFinishDuration': 0,  # for multi appts no time between, recovery time after
                    # 'RecoveryTime': 0    #  for non final treatment 0 then 45 on last treatment
                }
            ],
            'AppointmentDate': date,  # Date needs to be itinerary start date
            'AppointmentPayment': {
                'CouponCode': '',
                'PaymentItem': self.get_booker_credit_card_payment_item(billingzip, cccode, ccnum, expmonth, expyear,
                                                                        name_on_card)
            },
            'Customer': adjusted_customer,
            'Notes': notes
        }

        # print(params)

        response = BookerMerchantRequest('/appointment/create', self.merchant_token, params).post()
        print("book response %s" % response)
        return self.process_response(response)

    # def get_availability(self, treatment, start_date, end_date):
    #     # for treatment in treatments:
    #     # if isinstance(treatment.product, Treatment):
    #     params = {
    #         'LocationID': self.location_id,
    #         'ServiceID': treatment.booker_id,  # product.booker_id
    #         'Quantity': 2,  # test if quantity would work and what it returns
    #         'StartDateTime': self.format_date_for_booker_json(start_date),
    #         'EndDateTime': self.format_date_for_booker_json(end_date),
    #     }
    #     request = BookerMerchantRequest('/availability/employee_room', self.merchant_token, params)
    #     response = request.post()
    #     print(response)
    #     return self.process_response(response)

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
        print("response is %r" % response)
        response = self.process_response(response)
        if response['access_token']:
            self.merchant_token = response['access_token']
            setting = self.get_settings_object()
            setting.merchant_access_token = self.merchant_token
            setting.save()
        else:
            raise ValidationError(response['error'])

        return response['access_token']
