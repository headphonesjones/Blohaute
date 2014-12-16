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


def process_remember_me(request):
    remember_me_form = AuthenticationRememberMeForm(data=request.POST or None, prefix='login')


@csrf_protect
def checkout(request):
    coupon_form = CouponForm(prefix='coupon')
    remember_me_form = AuthenticationRememberMeForm(prefix='login')
    checkout_form = CheckoutForm(prefix="checkout")

    if request.method == 'POST':
        if 'login-password' in request.POST:
            remember_me_form = AuthenticationRememberMeForm(data=request.POST or None, prefix='login')
            if remember_me_form.is_valid():
                if not remember_me_form.cleaned_data.get('remember_me'):
                    request.session.set_expiry(0)

                user = remember_me_form.get_user()
                client = request.session['client']
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
                pass

    return render(request, 'checkout.html', {'coupon_form': coupon_form, 'login_form': remember_me_form, 'checkout_form': checkout_form})


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
