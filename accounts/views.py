from django.core.urlresolvers import reverse, reverse_lazy
from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, \
    update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.utils.translation import ugettext, ugettext_lazy as _
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.edit import DeleteView

from accounts.models import User
from accounts.forms import RegistrationForm, AuthenticationRememberMeForm, PasswordUpdateForm
from booking.service import BookerCustomerClient


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

            client = BookerCustomerClient()
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
            access_token = client.login(new_user.email, request.POST['password1'])

            # authenticate and login the user locally
            new_user = authenticate(email=request.POST['email'],
                                    password=request.POST['password1'])
            auth_login(request, new_user)

            # store the user password for the length of the session
            request.session['client'] = client
            client.customer_password = request.POST['password1']
            client.user = new_user

            messages.info(request, 'Thanks for registering. You are now logged in.')

            # redirect user the profile page
            return HttpResponseRedirect(reverse('welcome'))

        return render(request, 'registration/registration_page.html', {'registration_form': form})


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request):
    if request.method == 'GET':
        form = AuthenticationRememberMeForm()

    if request.method == 'POST':
        form = AuthenticationRememberMeForm(data=request.POST)
        print form.is_valid()
        if form.is_valid():
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)

            auth_login(request, form.get_user())

            user = form.get_user()
            client = BookerCustomerClient()
            access_token = client.login(user.email, request.POST['password'])
            request.session['client'] = client
            client.customer_password = request.POST['password']
            if access_token is None:

                form.add_error(
                    None, ValidationError('Invalid username or password', 'login_failure')
                )
                auth_logout(request)
                return render(request, 'registration/login_page.html', {'login_form': form})
            else:
                user.save()
                client.user = user
            return HttpResponseRedirect(reverse('welcome'))

        else:  # form is invalid
            return render(request, 'registration/login_page.html', {'login_form': form})

    return render(request, 'registration/login_page.html', {'login_form': form})


@csrf_protect
@login_required
def profile_view(request):
    password_form = PasswordUpdateForm(user=request.user, prefix='password')

    if request.method == 'GET':
        pass

    if request.method == 'POST':
        # check if the password form is in the request
        if 'password-old_password' in request.POST:
            password_form = PasswordUpdateForm(user=request.user, prefix='password',
                                               data=request.POST)

            if password_form.is_valid():
                client = request.session['client']

                try:  # try to update password on API
                    client.update_password(
                        request.user.email,
                        password_form.cleaned_data['old_password'],
                        password_form.cleaned_data['new_password1'])

                except ValidationError as error:
                    password_form.add_error(None, error)

                password_form.save()
                update_session_auth_hash(request, password_form.user)
                messages.success(request, 'Password updated successfully.')
                client.customer_password = password_form.cleaned_data['new_password1']

    context = {
        'user': request.user,
        'password_form': password_form
    }
    return render(request, 'welcome.html', context)


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
