from django.contrib import messages
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.generic.base import View
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from booking.forms import AddToCartForm, ContactForm, PaymentForm, CouponForm, QuickBookForm, ScheduleServiceForm
from booking.models import Treatment, Package, Order, GenericItem
import json


class TreatmentList(ListView):
    model = Treatment


def add_treatment_to_cart(request, slug):
    if request.method == 'POST':
        form = QuickBookForm(request.POST)
        if form.is_valid():
            treatment = form.cleaned_data['treatment']
            cart = request.cart
            cart.add(treatment, treatment.price, 1)
            return HttpResponseRedirect(reverse('cart'))
    return HttpResponseRedirect(reverse('treatment_detail', args=[slug]))


class TreatmentDetail(DetailView):
    model = Treatment
    form = None

    def post(self, request, *args, **kwargs):
        self.form = AddToCartForm(request.POST, treatment=self.get_object())

        if self.form.is_valid():
            package = self.form.cleaned_data['package']
            membership = self.form.cleaned_data['membership']
            if package:
                return HttpResponseRedirect(reverse('package_checkout', args=[kwargs['slug'], package.pk]))
            if membership:
                pass
        return super(TreatmentDetail, self).get(self, request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = {}
        if self.form is None:
            self.form = AddToCartForm(treatment=self.object,)
        context['add_to_cart_form'] = self.form
        return super(TreatmentDetail, self).get_context_data(**context)


def unavailable_days(request, services_requested=None):
    if services_requested is None:
        services_requested = request.session['order'].items
    print services_requested
    client = request.session['client']
    unavailable_days = client.get_unavailable_warm_period(services_requested)
    unavailable_days = [[date.year, date.month - 1, date.day] for date in unavailable_days]
    return HttpResponse(json.dumps(unavailable_days))


def available_times_for_day(request, services_requested=None):
    time_slots = [True]
    if services_requested is None:
        services_requested = request.session['order'].items

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


@csrf_protect
def schedule(request):
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('login_register'))  # if there's no user, ask them to login or register
    series = False
    if request.GET.get('series', None):
        series = True

    schedule_form = ScheduleServiceForm(data=request.POST)
    if request.method == 'GET':
        if series:
            order = request.session['order']
        else:  # use the cart
            if request.cart.is_empty():
                return HttpResponseRedirect(reverse('book'))  # if there's nothing in the cart, go to book
            order = Order()
            order.items = get_services_from_cart(request)
            request.session['order'] = order
        schedule_form = ScheduleServiceForm()

    if request.method == 'POST':
        order = request.session['order']
        print request
        client = request.session['client']
        if schedule_form.is_valid():
            data = schedule_form.cleaned_data
            order.itinerary = client.get_itinerary_for_slot_multiple(order.items, data['date'], data['time'])
            order.address = data['address']
            order.city = data['city']
            order.state = data['state']
            order.zip_code = data['zip_code']
            # request.session['order'].notes = data['notes']
            return HttpResponseRedirect(reverse('payment'))

    return render(request, 'booking/schedule.html', {'schedule_form': schedule_form, 'series': series})


class PaymentView(View):
    coupon_form = CouponForm(prefix='coupon')
    payment_form = PaymentForm(prefix='payment')
    order = None
    client = None

    def get(self, request, *args, **kwargs):
        self.get_order(request)
        self.client = request.session['client']
        return render(request, 'booking/payment.html', {'coupon_form': self.coupon_form,
                                                        'payment_form': self.payment_form,
                                                        'order': self.order})

    def post(self, request, *args, **kwargs):
        self.get_order(request)
        self.client = request.session['client']
        if 'coupon-coupon_code' in request.POST:
            self.process_coupon_form(request)
        else:
            results = self.process_payment_form(request)
            if results:
                return results
        return render(request, 'booking/payment.html', {'coupon_form': self.coupon_form,
                                                        'payment_form': self.payment_form,
                                                        'order': self.order})

    def get_order(self, request):
        self.order = request.session['order']

    def process_coupon_form(self, request):
        self.coupon_form = CouponForm(data=request.POST, prefix='coupon')
        if self.coupon_form.is_valid():
            try:
                coupon_code = self.coupon_form.cleaned_data.get('coupon_code')
                coupon_data = self.client.check_coupon_code(coupon_code)
                self.order.discount_text = coupon_data['description']
                self.order.discount_amount = coupon_data['amount']
            except ValidationError as error:
                self.coupon_form.add_error(None, error)

    def process_payment_form(self, request):
        self.payment_form = PaymentForm(data=request.POST, prefix='payment')
        if self.payment_form.is_valid():
            data = self.payment_form.cleaned_data
            try:
                payment_item = self.client.get_booker_credit_card_payment_item(data['billing_zip_code'],
                                                                          data['card_code'],
                                                                          data['card_number'],
                                                                          data['expiry_date'].month,
                                                                          data['expiry_date'].year,
                                                                          data['name_on_card'])
                coupon_code = self.coupon_form.cleaned_data.get('coupon_code')
                if not coupon_code:
                    coupon_code = ''
                appointment = self.client.book_appointment(
                    self.order.itinerary, request.user.first_name, request.user.last_name, self.order.address,
                    self.order.city, self.order.state, self.order.zip_code, request.user.email,
                    request.user.phone_number, payment_item, None, coupon_code)

                if appointment is not None:

                    request.cart.clear()
                    request.session['order'] = None
                    messages.success(request, "Your order was successfully placed! Edit your order(s) below and information below.")
                    return HttpResponseRedirect(reverse('welcome'))
                else:
                    messages.error(request, "Your booking could not be completed. Please try again.")
            except ValidationError as error:
                self.payment_form.add_error(None, error)


class PackagePaymentView(PaymentView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            return HttpResponseRedirect("%s?next=%s" % (reverse('login_register'), reverse('package_checkout', args=[self.kwargs['slug'], self.kwargs['pk']])))  # if there's no user, ask them to login or register
        return super(PackagePaymentView, self).get(request, args, kwargs)

    def get_order(self, request):
        self.package = Package.objects.get(pk=self.kwargs['pk'])
        
        self.order = request.session.get('order', None)
        if not self.order or (self.order and (len(self.order.items) != 1 or self.order.items[0].product != self.package)):
            request.session['order'] = Order()
            self.order = request.session['order']
            self.order.items = [GenericItem(product=self.package, quantity=1)]

    def process_payment_form(self, request):
        self.payment_form = PaymentForm(data=request.POST, prefix='payment')
        if self.payment_form.is_valid():
            data = self.payment_form.cleaned_data
            try:
                result = self.client.buy_series(self.package.booker_id, 
                                       data['card_number'],
                                       data['name_on_card'],
                                       data['expiry_date'].year,
                                       data['expiry_date'].month,
                                       data['card_code'],
                                       data['billing_zip_code'])
                if result['IsSuccess']:
                    request.session['order'] = None
                    messages.success(request, "Your order was successfully placed! You can schedule your appointments below.")
                    return HttpResponseRedirect(reverse('welcome'))
                else:
                    self.payment_form.add_error(None, "There was an unknown error completing your order. Please try again.")

            except Exception as error:
                print error
        else:
            print self.payment_form.errors


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
