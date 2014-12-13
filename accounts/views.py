import json
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from accounts.forms import RegistrationForm, AuthenticationRememberMeForm
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.views.decorators.cache import never_cache
from django.contrib import messages
from django.forms import ValidationError
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.detail import DetailView
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
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

            try:
                new_user.id = client.create_user(new_user.email, request.POST['password1'],
                                                 new_user.first_name, new_user.last_name,
                                                 new_user.phone_number)['CustomerID']

            except ValidationError as error:
                form.add_error(None, error)
                return render(request, 'registration/registration_page.html', {'registration_form': form})

            #login to the api
            login_result = client.login(new_user.email, request.POST['password1'])
            new_user.access_token = login_result
            new_user.save()

            new_user = authenticate(email=request.POST['email'],
                                    password=request.POST['password1'])

            auth_login(request, new_user)

            messages.info(request, 'Thanks for registering. You are now logged in.')

            #redirect to the user profile page by returning the new url via JSON
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
            print 'form is valid'
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)

            auth_login(request, form.get_user())

            user = form.get_user()
            client = BookerCustomerClient(token=user.access_token)
            access_token = client.login(user.email, request.POST['password'])

            if access_token is None:

                form.add_error(
                    None, ValidationError('Invalid username or password', 'login_failure')
                )
                auth_logout(request)
                return render(request, 'registration/login_page.html', {'login_form': form})
            else:
                user.access_token = access_token
                user.save()
            return HttpResponseRedirect(reverse('welcome'))

        else: # form is invalid
            print form.errors
            return render(request, 'registration/login_page.html', {'login_form': form})

    return render(request, 'registration/login_page.html', {'login_form': form})


class ProfileView(DetailView):
    model = User

    def get_object(self):
        return self.request.user

    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(ProfileView, self).dispatch(*args, **kwargs)
