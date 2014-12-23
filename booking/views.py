from django.contrib import messages
from django.contrib.auth import login as auth_login
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from booking.forms import AddToCartForm, QuickBookForm, ContactForm, CheckoutForm, CouponForm
from booking.models import Treatment, Appointment
from accounts.forms import AuthenticationRememberMeForm
from changuito.models import Cart
import json


class TreatmentList(ListView):
    model = Treatment

    def post(self, request, *args, **kwargs):
        form = QuickBookForm(request.POST)
        if form.is_valid():
            treatment = form.cleaned_data['treatment']
            cart = request.cart
            cart.add(treatment, treatment.price, 1)
            return HttpResponseRedirect(reverse('cart'))
        print form.errors
        return super(TreatmentList, self).get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {}
        context['form'] = QuickBookForm()
        return super(TreatmentList, self).get_context_data(**context)


class TreatmentDetail(DetailView):
    model = Treatment
    form = None

    def post(self, request, *args, **kwargs):
        self.form = AddToCartForm(request.POST, treatment=self.get_object())

        if self.form.is_valid():
            cart = request.cart
            package = self.form.cleaned_data['package']
            membership = self.form.cleaned_data['membership']
            if package:
                cart.add(package, package.price, 1)
            if membership:
                cart.add(membership, membership.price, 1)

            return HttpResponseRedirect(reverse('cart'))

        return super(TreatmentDetail, self).get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {}
        if self.form is None:
            self.form = AddToCartForm(treatment=self.object)
        context['add_to_cart_form'] = self.form
        return super(TreatmentDetail, self).get_context_data(**context)


def unavailable_days(request, services_requested=None):
    if services_requested is None:
        services_requested = get_services_from_cart(request)
    client = request.session['client']
    unavailable_days = client.get_unavailable_warm_period(services_requested)
    unavailable_days = [[date.year, date.month - 1, date.day] for date in unavailable_days]
    return HttpResponse(json.dumps(unavailable_days))


def available_times_for_day(request, services_requested=None):
    time_slots = [True]
    if services_requested is None:
        services_requested = get_services_from_cart(request)

    client = request.session['client']
    available_times = client.get_available_times_for_day(services_requested, request.POST['date'])
    for time in available_times:
        time_parts = time.split(":")
        time_parts = map(int, time_parts)
        time_array = [time_parts[0], time_parts[1]]
        time_slots.append(time_array)
    return HttpResponse(json.dumps(time_slots))


def get_services_from_cart(request):
    return [item for item in request.cart if isinstance(item.product, Treatment)]


def get_payment_from_cart(request):
    return [item for item in request.cart if isinstance(item.product, Treatment)]


@csrf_protect
def checkout(request):
    if request.cart.is_empty():
        return HttpResponseRedirect(reverse('book'))  # if there's nothing in the cart, go to book

    coupon_form = CouponForm(prefix='coupon')
    remember_me_form = AuthenticationRememberMeForm(prefix='login')
    checkout_form = CheckoutForm(prefix="checkout", user=request.user, payment_required=request.cart.cart.needs_payment())

    client = request.session['client']
    services_requested = get_services_from_cart(request)
    for item in services_requested:
        print("item is %r %s" % (item, item.series_id))

    if request.method == 'POST':
        if 'login-password' in request.POST:
            remember_me_form = AuthenticationRememberMeForm(data=request.POST or None,
                                                            prefix='login')
            if remember_me_form.is_valid():
                if not remember_me_form.cleaned_data.get('remember_me'):
                    request.session.set_expiry(0)

                user = remember_me_form.get_user()
                try:
                    client.login(user.email, remember_me_form.cleaned_data.get('password'))
                    client.user = user
                    auth_login(request, remember_me_form.get_user())
                    return HttpResponseRedirect(reverse('checkout'))

                except ValidationError as e:
                    remember_me_form.add_error(None, e)
            else:
                messages.error(request, 'There was a problem signing in. Please check the form and make sure that everything is filled out correctly.')
        if 'coupon-coupon_code' in request.POST:
            coupon_form = CouponForm(data=request.POST or None, prefix='coupon')
            if coupon_form.is_valid():
                coupon = coupon_form.cleaned_data.get('coupon_code')
                client = request.session['client']
                print('coupon is %s' % coupon)
                # find out if its good or not and do stuff?  Get and print value?  Whatever

        if 'checkout-address' in request.POST:
            checkout_form = CheckoutForm(data=request.POST or None, prefix='checkout', user=request.user,
                                         payment_required=request.cart.cart.needs_payment())
            print("in form")
            print("valid: %s" % checkout_form.is_valid())
            if checkout_form.is_valid():

                data = checkout_form.cleaned_data
                try:
                    itinerary = client.get_itinerary_for_slot_multiple(services_requested,
                                                                       data['date'], data['time'])
                    print("itin is %s" % itinerary)
                    # get payment method
                    payment_item = client.get_booker_credit_card_payment_item(data['billing_zip_code'],
                                                                              data['card_code'],
                                                                              data['card_number'],
                                                                              data['expiry_date'].month,
                                                                              data['expiry_date'].year,
                                                                              data['name_on_card'])
                    for item in services_requested:
                        print("item is %r %s" % (item, item.series_id))
                        # if item.series_id:
                        #     payment_items.append(client.get_booker_series_payment_item(item.series_id))
                        # else:
                        # # BOOKER DOES NOT ACCEPT SERIES AS PAYMENT - Waiting on feedback, but CC for now
                    appointment = client.book_appointment(itinerary, data['first_name'], data['last_name'], data['address'],
                                                          data['city'], data['state'], data['zip_code'],
                                                          data['email_address'], data['phone_number'], payment_item,
                                                          data['notes'])
                    if appointment is not None:
                        request.cart.clear()
                        if request.user.is_authenticated():
                            messages.success(request, "Your order was successfully placed! Edit your order(s) below and information below.")
                            return HttpResponseRedirect(reverse('welcome'))

                        print("redirecting to the view with appointment %s" % appointment)
                        request.session['appointment'] = appointment
                        return HttpResponseRedirect(reverse('thankyou'))
                    else:
                        messages.error(request, "Your booking could not be completed. Please try again.")
                except ValidationError as error:
                    checkout_form.add_error(None, error)
            else:
                print checkout_form.errors
    return render(request, 'checkout.html', {'coupon_form': coupon_form,
                                             'login_form': remember_me_form,
                                             'checkout_form': checkout_form,
                                             'cart': request.cart})


def thank_you(request):
    appointment = request.session['appointment']
    print("in view appointment is: %s" % appointment)
    form = ContactForm()

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            send_mail('New Message received from %s' % form.cleaned_data['name'],
                      form.cleaned_data['message'], 'contact@blohaute.com',
                      ['ajsporinsky@gmail.com'], fail_silently=True)

            messages.success(request, 'Thank you. Your message has been sent successfully')
            form = ContactForm()
    return render(request, 'thankyou.html', {'contact_form': form, 'appointment': appointment})


def contact_view(request):
    if request.method == "GET":
        form = ContactForm()

        return render(request, 'contact.html', {'contact_form': form})

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            send_mail('New Message received from %s' % form.cleaned_data['name'],
                      form.cleaned_data['message'], 'contact@blohaute.com',
                      ['ajsporinsky@gmail.com'], fail_silently=True)

            messages.success(request, 'Thank you. Your message has been sent successfully')
            form = ContactForm()
    return render(request, 'contact.html', {'contact_form': form})


def upcoming_view(request):
    client = request.session['client']
    return HttpResponse({'upcoming': client.get_upcoming()})
