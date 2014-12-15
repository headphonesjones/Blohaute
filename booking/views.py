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
from booking.forms import AddToCartForm, QuickBookForm, ContactForm
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


# def unavailable_days(request):
#     client = request.session['client']
#     unavailable_days = client.get_unavailable_days_in_range()
#
#     response = "beforeShowDay: function(date) {" \
#                "    var day = date.getDate(); " \
#                "    var month = date.getMonth(); " \
#                "    var year = date.getFullYear();" \
#                "    var full = year + \"-\" + month + \"-\" + day;"
#                "    if ((day == 27 || day == 26) && date.getMonth()+1 == 9 && date.getFullYear() == 2014) { " \
#                "return {0: false}} else {return {0: true}}}"
#     return HttpResponse(response)

@csrf_protect
def checkout(request):
    form = AuthenticationRememberMeForm(data=request.POST or None, prefix='login')

    if request.method == 'POST':
        if ('login-password') in request.POST:

            if form.is_valid():
                if not form.cleaned_data.get('remember_me'):
                    request.session.set_expiry(0)

                user = form.get_user()
                client = request.session['client']
                try:
                    client.login(user.email, request.POST['password'])
                    client.user = user
                    auth_login(request, form.get_user())
                    return HttpResponseRedirect(reverse('welcome'))

                except ValidationError as e:
                    form.add_error(None, e)


    return render(request, 'checkout.html', {'login_form': form})


def contact_view(request):
    if request.method == "GET":
        form = ContactForm()

        return render(request, 'contact.html', {'contact_form': form})

    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            #send email
            send_mail('New Message recieved from %s' % form.cleaned_data['name'],
                      form.cleaned_data['message'], 'contact@blohaute.com',
                      ['ajsporinsky@gmail.com'], fail_silently=True)

            messages.success(request, 'Thank you. Your message has been sent successfully')
            form = ContactForm()
    return render(request, 'contact.html', {'contact_form': form})


def upcoming_view(request):
    client = request.session['client']
    return HttpResponse({'upcoming': client.get_upcoming()})
