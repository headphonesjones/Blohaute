import json
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from accounts.forms import RegistrationForm, AuthenticationRememberMeForm
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters


def register(request):
    if request.method == 'POST':

        # create a form instance and populate it with data from the request
        form = RegistrationForm(request.POST)

        if form.is_valid():
            new_user = form.save()
            new_user = authenticate(username=request.POST['username'],
                                    password=request.POST['password1'])

            auth_login(request, new_user)

            messages.info(request, 'Thanks for registering. You are now logged in.')

            #redirect to the user profile page by returning the new url via JSON
            return HttpResponse(json.dumps({'url': reverse('welcome')}),
                                content_type='application/json')

        return render(request, 'registration/registration.html', {'registration_form': form})


@sensitive_post_parameters()
@csrf_protect
@never_cache
def login(request):
    if request.method == 'POST':
        form = AuthenticationRememberMeForm(data=request.POST)
        if form.is_valid():
            if not form.cleaned_data.get('remember_me'):
                request.session.set_expiry(0)

            auth_login(request, form.get_user())

            return HttpResponse(json.dumps({'url': reverse('welcome')}),
                                content_type='application/json')

        else:
            return render(request, 'registration/login.html', {'login_form': form})
