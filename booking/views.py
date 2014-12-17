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
from booking.models import Treatment
from accounts.forms import AuthenticationRememberMeForm
from datetime import datetime
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


def available_times_for_day(request):
    time_slots = [True]
    if request.cart.is_empty():
        return HttpResponseRedirect(reverse('cart'))  # if there's nothing in the cart, go back to it
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
    services_requested = []
    for item in request.cart:
        if isinstance(item.product, Treatment):
            services_requested.append(item)
    return services_requested


@csrf_protect
def checkout(request):
    if request.cart.is_empty():
        return HttpResponseRedirect(reverse('book'))  # if there's nothing in the cart, go back to it

    coupon_form = CouponForm(prefix='coupon')
    remember_me_form = AuthenticationRememberMeForm(prefix='login')
    checkout_form = CheckoutForm(prefix="checkout")

    services_requested = get_services_from_cart(request)

    client = request.session['client']
    unavailable_days = client.get_unavailable_warm_period(services_requested)
    result = []
    date_array = []
    for day in unavailable_days:
        print(day)
        day = datetime.strptime(day, "%Y-%m-%d")
        date_array.append(day.year)
        date_array.append(day.month-1)
        date_array.append(day.day)
        result.append(date_array)
        date_array = []

    unavailable_days = result

    if request.method == 'POST':
        if 'login-password' in request.POST:
            remember_me_form = AuthenticationRememberMeForm(data=request.POST or None, prefix='login')
            if remember_me_form.is_valid():
                if not remember_me_form.cleaned_data.get('remember_me'):
                    request.session.set_expiry(0)

                user = remember_me_form.get_user()
                try:
                    client.login(user.email, remember_me_form.cleaned_data.get('password'))
                    client.user = user
                    auth_login(request, remember_me_form.get_user())
                    return HttpResponseRedirect(reverse('welcome'))  # change this to o ther logic

                except ValidationError as e:
                    remember_me_form.add_error(None, e)

        if 'coupon-coupon_code' in request.POST:
            coupon_form = CouponForm(data=request.POST or None, prefix='coupon')
            if coupon_form.is_valid():
                coupon = coupon_form.cleaned_data.get('coupon_code')
                client = request.session['client']
                print('coupon is %s' % coupon)
                # find out if its good or not and do stuff?  Get and print value?  Whatever

        if 'checkout-first_name' in request.POST:
            checkout_form = CheckoutForm(data=request.POST or None, prefix='checkout')
            if checkout_form.is_valid():

                data = checkout_form.cleaned_data

                client.book_appointment(itinerary,
                                        data['first_name'],
                                        data['last_name'],
                                        data['address'],
                                        data['city'],
                                        data['state'],
                                        data['zip_code'],
                                        data['email_address'],
                                        data['phone_number'],
                                        data['card_number'],
                                        data['name_on_card'],
                                        data['expiry_date'].year,
                                        data['expiry_date'].month,
                                        data['card_code'],
                                        data['billing_zip_code'],
                                        data['notes'])

    return render(request, 'checkout.html', {'coupon_form': coupon_form,
                                             'login_form': remember_me_form,
                                             'checkout_form': checkout_form,
                                             'cart': request.cart,
                                             'unavailable_days': unavailable_days})


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
