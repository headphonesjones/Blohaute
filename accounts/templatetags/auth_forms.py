from django import template
from accounts.forms import RegistrationForm, AuthenticationRememberMeForm
register = template.Library()


@register.inclusion_tag('registration/registration.html')
def registration_form():
    form = RegistrationForm()
    return {'registration_form': form}


@register.inclusion_tag('registration/login.html')
def login_form():
    form = AuthenticationRememberMeForm()
    return {'login_form': form}
