from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, \
    update_session_auth_hash, REDIRECT_FIELD_NAME
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import resolve_url
from django.utils.http import is_safe_url
from django.contrib.auth.decorators import login_required
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.utils.translation import ugettext as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.edit import DeleteView
from accounts.models import User
from accounts.forms import (RegistrationForm, AuthenticationRememberMeForm, PasswordUpdateForm,
                            EmailUpdateForm, PasswordResetForm, SetPasswordForm)
from booking.forms import AvailableServiceFormset, RescheduleForm
from booking.models import Treatment, GenericItem, Order
from booking.views import unavailable_days, available_times_for_day
from changuito.proxy import CartDoesNotExist


@sensitive_post_parameters()
@csrf_protect
def register(request):
    next_url = request.GET.get('next', None)
    if request.method == 'GET':
        form = RegistrationForm()
        return render(request, 'registration/registration_page.html', {'registration_form': form})

    if request.method == 'POST':

        # create a form instance and populate it with data from the request
        form = RegistrationForm(request.POST, )
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
            try:
                request.cart.replace(request.session.get('CART-ID'), new_user)
            except CartDoesNotExist:
                pass
            # store the user password for the length of the session
            client.user = new_user

            messages.info(request, 'Thanks for registering. You are now logged in.')

            # redirect user the profile page
            if next_url:
                return HttpResponseRedirect(next_url)
            return HttpResponseRedirect(reverse('welcome'))

        return render(request, 'registration/registration_page.html', {'registration_form': form, 'next': next_url})


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request):
    next_url = request.GET.get('next', None)
    form = AuthenticationRememberMeForm(data=request.POST or None)
    print "cart is empty %s" % request.cart.is_empty()
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
                print "cart is empty %s" % request.cart.is_empty()
                request.cart.replace(request.session.get('CART-ID'), user)
                if next_url:
                    return HttpResponseRedirect(next_url)
                return HttpResponseRedirect(reverse('welcome'))

            except ValidationError as e:
                form.add_error(None, e)
            except CartDoesNotExist:
                if next_url:
                    return HttpResponseRedirect(next_url)
                return HttpResponseRedirect(reverse('welcome'))


    return render(request, 'registration/login_page.html', {'login_form': form, 'next': next_url})


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login_register(request):
    login_form = AuthenticationRememberMeForm()
    registration_form = RegistrationForm()
    next_url = request.GET.get('next', reverse('schedule'))
    return render(request, 'registration/login_register.html',
                  {'login_form': login_form, 'registration_form': registration_form,
                   'next': next_url})

def logout(request, next_page=None,
           template_name='registration/logged_out.html',
           redirect_field_name=REDIRECT_FIELD_NAME,
           current_app=None, extra_context=None):
    """
    Logs out the user and displays 'You are logged out' message.
    """
    auth_logout(request)
    request.cart.clear()
    if next_page is not None:
        next_page = resolve_url(next_page)

    if (redirect_field_name in request.POST or
            redirect_field_name in request.GET):
        next_page = request.POST.get(redirect_field_name,
                                     request.GET.get(redirect_field_name))
        # Security check -- don't allow redirection to a different host.
        if not is_safe_url(url=next_page, host=request.get_host()):
            next_page = request.path

    if next_page:
        # Redirect to this page until the session has been cleared.
        return HttpResponseRedirect(next_page)

    current_site = get_current_site(request)
    context = {
        'site': current_site,
        'site_name': current_site.name,
        'title': _('Logged out')
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context, current_app=current_app)


@csrf_protect
def forgot_password(request):
    if request.method == 'POST':
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            client = request.session['client']
            try:
                client.send_reset_password_link(form.cleaned_data['email'], form.cleaned_data['first_name'])
                return HttpResponseRedirect(reverse('forgot_success'))
            except ValidationError as e:
                form.add_error(None, e)
    else:
        form = PasswordResetForm()
    return render(request, 'registration/forgot_password.html', {'form': form})


@csrf_protect
def reset_forogtten_password(request):
    if request.method == 'POST':
        form = SetPasswordForm(request.POST)
        if form.is_valid():
            client = request.session['client']
            try:
                client.reset_password(form.cleaned_data['key'], form.cleaned_data['new_password1'])
                form.save()
                messages.success(request, 'Your password has been updated successfully. Please login to continue')
                return HttpResponseRedirect(reverse('login'))
            except ValidationError as e:
                form.add_error(None, e)
    else:
        print request
        form = SetPasswordForm(initial={'key':request.GET['Key']})

    return render(request, 'registration/reset_password.html', {'password_form': form})


@csrf_protect
@login_required
def profile_view(request):
    CANCELLED_STATUS = 6
    password_form = PasswordUpdateForm(user=request.user, prefix='password')
    email_form = EmailUpdateForm(prefix='update_email')
    client = request.session['client']
    appointments = client.get_appointments()
    future_appointments = [appt for appt in appointments if appt.is_past() is False and appt.status is not CANCELLED_STATUS]
    past_appointments = [appt for appt in appointments if appt.is_past() and appt.status is not CANCELLED_STATUS]
    series = client.get_customer_series()
    service_formset = AvailableServiceFormset(series=series, prefix="services")

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
            service_formset = AvailableServiceFormset(series=series, prefix="services", data=request.POST)
            if service_formset.is_valid():
                request.session['order'] = Order()
                order = request.session['order']
                for form in service_formset:
                    quantity = form.cleaned_data['quantity']
                    if quantity > 0:
                        treatment = Treatment.objects.get(pk=form.cleaned_data['treatment_id'])
                        item = GenericItem(treatment, quantity=quantity)
                        item.source = form.series
                        order.items.append(item)
                return HttpResponseRedirect("%s?series=true" % reverse('schedule'))
            else:
                messages.error(request, "There was a problem scheduling your appointment. Please check the form and try again.")

    context = {
        'user': request.user,
        'password_form': password_form,
        'email_form': email_form,
        'future_appointments': future_appointments,
        'past_appointments': past_appointments,
        'service_formset': service_formset,
        'series': series
    }
    return render(request, 'welcome.html', context)


@login_required
@csrf_protect
def cancel_view(request, pk):
    if request.method == 'POST':
        client = request.session['client']
        try:
            appointment = client.get_appointment(pk)
            if appointment.customer_id != client.customer_id:  #quick security check
                raise Exception
            response = client.cancel_appointment(pk)
            print("cancel response on view is %s " % response)
            if response['IsSuccess'] is False:
                raise Exception
            return HttpResponseRedirect(reverse('welcome'))
        except:
            messages.error(request, "There was a problem canceling your appointment. If you have trouble, please call or email for assistance.")

    return render(request, 'appointment/appointment_cancel.html', {'appt_id': pk})


@login_required
@csrf_protect
def reschedule(request, pk):
    form = RescheduleForm()
    client = request.session['client']
    appointment = client.get_appointment(pk)
    request.session['reschedule_items'] = [GenericItem(treatment.treatment) for treatment in appointment.treatments]
    if request.method == 'POST':
        form = RescheduleForm(request.POST)
        if form.is_valid():
            # update the order / delete the old order and create a new one
            pass
    return render(request, 'appointment/reschedule.html', {'appt_id': pk, 'form':form, 'appointment': appointment})


def reschedule_days(request, pk):
    client = request.session['client']
    return unavailable_days(request, request.session['reschedule_items'])


def reschedule_times(request, pk):
    return available_times_for_day(request, request.session['reschedule_items'])


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
