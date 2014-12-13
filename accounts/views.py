from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout, \
    update_session_auth_hash
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.forms import ValidationError
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.contrib.auth.decorators import login_required
from booking.service import BookerCustomerClient
from accounts.forms import RegistrationForm, AuthenticationRememberMeForm, PasswordUpdateForm


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
                new_user.id = client.create_user(new_user.email, request.POST['password1'],
                                                 new_user.first_name, new_user.last_name,
                                                 new_user.phone_number)['CustomerID']
                new_user.save()
            except ValidationError as error:
                form.add_error(None, error)
                return render(request, 'registration/registration_page.html',
                              {'registration_form': form})

            #login to the api
            client.login(new_user.email, request.POST['password1'])

            #authenticate and login the user locally
            new_user = authenticate(email=request.POST['email'],
                                    password=request.POST['password1'])
            auth_login(request, new_user)

            #store the user password for the length of the session
            request.session['password'] = request.POST['password1']
            request.session['client'] = client

            messages.info(request, 'Thanks for registering. You are now logged in.')

            #redirect user the profile page
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
            request.session['password'] = request.POST['password']
            request.session['client'] = client
            if access_token is None:

                form.add_error(
                    None, ValidationError('Invalid username or password', 'login_failure')
                )
                auth_logout(request)
                return render(request, 'registration/login_page.html', {'login_form': form})
            else:
                request.session['access_token'] = access_token
                user.save()
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
        #check if the password form is in the request
        if 'password-old_password' in request.POST:
            password_form = PasswordUpdateForm(user=request.user, prefix='password',
                                               data=request.POST)

            if password_form.is_valid():
                client = request.session['client']

                try:  # try to update password on API
                    client.update_password(
                        request.user.id,
                        request.user.email,
                        password_form.cleaned_data['old_password'],
                        password_form.cleaned_data['new_password1'])

                except ValidationError as error:
                    password_form.add_error(None, error)

                password_form.save()
                update_session_auth_hash(request, password_form.user)
                messages.success(request, 'Password updated successfully.')

    context = {
        'user': request.user,
        'password_form': password_form
    }
    return render(request, 'welcome.html', context)
