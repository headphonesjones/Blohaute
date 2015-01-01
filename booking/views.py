from django.contrib import messages
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from booking.forms import AddToCartForm, ContactForm, CheckoutForm, CheckoutScheduleForm, CouponForm, QuickBookForm
from booking.models import Treatment, Package, Order
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
        services_requested = get_services_from_cart(request)
    client = request.session['client']
    unavailable_days = client.get_unavailable_warm_period(services_requested)
    unavailable_days = [[date.year, date.month - 1, date.day] for date in unavailable_days]
    return HttpResponse(json.dumps(unavailable_days))


def check_coupon(request):
    coupon_code = request.GET['coupon_code']
    if coupon_code:
        try:
            client = request.session['client']
            coupon_data = client.check_coupon_code(coupon_code)
            order = request.session['order']
            order.discount_text = coupon_data['description']
            order.discount_amount = coupon_data['amount']
            return HttpResponse(json.dumps(coupon_data))
        except ValidationError:
            return HttpResponseNotFound(json.dumps({'description': 'No matching coupon was found'}))


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
        print 'cart is empty at checkout'
        return HttpResponseRedirect(reverse('book'))  # if there's nothing in the cart, go to book
    if not request.user.is_authenticated():
        return HttpResponseRedirect(reverse('login_register'))  # if there's no user, ask them to login or register

    coupon_form = CouponForm(prefix='coupon')
    checkout_form = CheckoutScheduleForm(prefix="checkout",
                                         payment_required=request.cart.cart.needs_payment())

    client = request.session['client']
    order = Order()
    order.items = get_services_from_cart(request)
    request.session['order'] = order

    if request.method == 'POST':
        if 'checkout-address' in request.POST:
            checkout_form = CheckoutScheduleForm(data=request.POST or None, prefix='checkout',
                                                 payment_required=request.cart.cart.needs_payment())
            if checkout_form.is_valid():
                data = checkout_form.cleaned_data
                try:
                    itinerary = client.get_itinerary_for_slot_multiple(order.items,
                                                                       data['date'], data['time'])
                    print("itin is %s" % itinerary)
                    # get payment method
                    payment_item = client.get_booker_credit_card_payment_item(data['billing_zip_code'],
                                                                              data['card_code'],
                                                                              data['card_number'],
                                                                              data['expiry_date'].month,
                                                                              data['expiry_date'].year,
                                                                              data['name_on_card'])
                    for item in order.items:
                        print("item is %r %s" % (item, item.series_id))
                        # if item.series_id:
                        #     payment_items.append(client.get_booker_series_payment_item(item.series_id))
                        # else:
                        # # BOOKER DOES NOT ACCEPT SERIES AS PAYMENT - Waiting on feedback, but CC for now
                    appointment = client.book_appointment(itinerary, request.user.first_name, request.user.last_name, data['address'],
                                                          data['city'], data['state'], data['zip_code'],
                                                          request.user.email, request.user.phone_number, payment_item,
                                                          data['notes'])
                    if appointment is not None:

                        request.cart.clear()
                        messages.success(request, "Your order was successfully placed! Edit your order(s) below and information below.")
                        return HttpResponseRedirect(reverse('welcome'))
                    else:
                        messages.error(request, "Your booking could not be completed. Please try again.")
                except ValidationError as error:
                    checkout_form.add_error(None, error)
            else:
                print checkout_form.errors
    return render(request, 'checkout.html', {'coupon_form': coupon_form,
                                             'checkout_form': checkout_form,
                                             'order': order})


def package_checkout(request, slug, pk):
    if not request.user.is_authenticated():
        return HttpResponseRedirect("%s?next=%s" % (reverse('login_register'), reverse('package_checkout', args=[slug, pk])))  # if there's no user, ask them to login or register

    package = Package.objects.get(pk=pk)
    coupon_form = CouponForm(prefix='coupon')
    checkout_form = CheckoutForm(prefix="checkout", payment_required=True)
    client = request.session['client']

    if request.method == 'POST':
        print 'request method was post'
        if 'coupon-coupon_code' in request.POST:
            print 'coupon'
            coupon_form = CouponForm(data=request.POST or None, prefix='coupon')
            if coupon_form.is_valid():
                coupon = coupon_form.cleaned_data.get('coupon_code')
                client = request.session['client']
                print('coupon is %s' % coupon)
                # find out if its good or not and do stuff?  Get and print value?  Whatever

        else:
            checkout_form = CheckoutForm(data=request.POST or None, prefix='checkout',
                                         payment_required=True)
            print("in form")
            print("valid: %s" % checkout_form.is_valid())
            if checkout_form.is_valid():
                data = checkout_form.cleaned_data
                try:
                    # get payment method
                    payment_item = client.get_booker_credit_card_payment_item(data['billing_zip_code'],
                                                                              data['card_code'],
                                                                              data['card_number'],
                                                                              data['expiry_date'].month,
                                                                              data['expiry_date'].year,
                                                                              data['name_on_card'])

                    #make the payment create the series

                    messages.success(request, "Your order was successfully placed! Edit your order(s) below and information below.")
                    return HttpResponseRedirect(reverse('welcome'))
                except ValidationError as error:
                    checkout_form.add_error(None, error)
            else:
                print checkout_form.errors

    return render(request, 'package_checkout.html', {'coupon_form': coupon_form,
                                                     'checkout_form': checkout_form,
                                                     'item': package})


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
