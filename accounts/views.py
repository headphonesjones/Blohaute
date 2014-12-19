from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, \
    update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.edit import DeleteView
from changuito.models import Cart
from accounts.models import User
from accounts.forms import (RegistrationForm, AuthenticationRememberMeForm, PasswordUpdateForm,
                            EmailUpdateForm)
from booking.forms import AvailableServiceFormset
from booking.models import Treatment


@sensitive_post_parameters()
@csrf_protect
def register(request):
    if request.method == 'GET':
        form = RegistrationForm()
        return render(request, 'registration/registration_page.html', {'registration_form': form})

    if request.method == 'POST':

        # create a form instance and populate it with data from the request
        form = RegistrationForm(request.POST)
        if form.is_valid():

            client = request.session['client']
            new_user = form.save(commit=False)

            try:  # create a user on the API
                new_user.booker_id = client.create_user(new_user.email, request.POST['password1'],
                                                        new_user.first_name, new_user.last_name,
                                                        new_user.phone_number)['CustomerID']
                new_user.save()
            except ValidationError as error:
                form.add_error(None, error)
                return render(request, 'registration/registration_page.html',
                              {'registration_form': form})

            # login to the api
            client.login(new_user.email, request.POST['password1'])

            # authenticate and login the user locally
            new_user = authenticate(email=request.POST['email'],
                                    password=request.POST['password1'])
            auth_login(request, new_user)

            # store the user password for the length of the session
            client.user = new_user

            messages.info(request, 'Thanks for registering. You are now logged in.')

            # redirect user the profile page
            return HttpResponseRedirect(reverse('welcome'))

        return render(request, 'registration/registration_page.html', {'registration_form': form})


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request):
    form = AuthenticationRememberMeForm(data=request.POST or None)

    if request.method == 'POST':
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

    return render(request, 'registration/login_page.html', {'login_form': form})


@csrf_protect
@login_required
def profile_view(request):
    password_form = PasswordUpdateForm(user=request.user, prefix='password')
    email_form = EmailUpdateForm(prefix='update_email')
    client = request.session['client']
    appointments = client.get_appointments()
    series = client.get_customer_series()

    service_formset = AvailableServiceFormset(series=series, prefix="services", data=request.POST or None)

    if request.method == 'GET':
        pass

    if request.method == 'POST':
        # check if the password form is in the request
        if 'password-old_password' in request.POST:
            password_form = PasswordUpdateForm(user=request.user, prefix='password',
                                               data=request.POST)

            if password_form.is_valid():
                try:  # try to update password on API
                    client.update_password(
                        request.user.email,
                        password_form.cleaned_data['old_password'],
                        password_form.cleaned_data['new_password1'])
                    password_form.save()
                    update_session_auth_hash(request, password_form.user)
                    messages.success(request, 'Password updated successfully.')

                except ValidationError as error:
                    password_form.add_error(None, error)

        if 'update_email-email' in request.POST:
            email_form = EmailUpdateForm(request.POST, prefix='update_email')
            if email_form.is_valid():
                try:
                    client.update_email(email_form.cleaned_data['email'])
                    request.user.email = email_form.cleaned_data['email']
                    request.user.save()
                    messages.success(request, "Your account has been successfully updated.")
                except ValidationError as error:
                    messages.error(request, "There was a problem updating your account. Please check the form and try again.")
                    email_form.add_error(None, error)
            else:
                messages.error(request, "There was a problem updating your account. Please check the form and try again.")

        if 'services-TOTAL_FORMS' in request.POST:
            if service_formset.is_valid():
                cart = request.cart
                cart.clear()
                # cart.cart.mode = Cart.SCHEDULE
                schedule_items = []
                for form in service_formset:
                    quantity = form.cleaned_data['quantity']
                    if quantity > 0:
                        treatment = Treatment.objects.get(pk=form.cleaned_data['treatment_id'])
                        schedule_items.append({'treatment': treatment, quantity: 'quantity', 'source': form.series})
                        cart.add(treatment, treatment.price, quantity)

                return HttpResponseRedirect(reverse('checkout'))

            else:
                messages.error(request, "There was a problem scheduling your appointment. Please check the form and try again.")

    context = {
        'user': request.user,
        'password_form': password_form,
        'email_form': email_form,
        'appointments': appointments,
        'service_formset': service_formset
    }
    return render(request, 'welcome.html', context)


@login_required
@csrf_protect
def cancel_view(request):
    client = request.session['client']
    print(request.POST)
    client.cancel_appointment(request.POST['appointment_id'])
    return HttpResponseRedirect(reverse('welcome'))


class UserDelete(DeleteView):
    model = User
    success_url = reverse_lazy('home')
    template_name = 'registration/delete.html'

    def get_object(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        """
        Calls the delete() method on the fetched object and then
        redirects to the success URL.
        """
        self.object = self.get_object()
        success_url = self.get_success_url()

        client = request.session['client']
        try:
            client.delete_customer()
        except:
            print 'unable to delete customer'

        messages.success(request, "Your account has been successfully deleted.")

        self.object.delete()

        return HttpResponseRedirect(success_url)
