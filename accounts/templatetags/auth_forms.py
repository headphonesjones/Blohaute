from django import template
from accounts.forms import RegistrationForm, AuthenticationRememberMeForm
register = template.Library()


@register.inclusion_tag('registration/registration.html', takes_context=True)
def registration_form(context):
    form = RegistrationForm()
    return {'registration_form': form}


@register.inclusion_tag('registration/login.html', takes_context=True)
def login_form(context):
    form = AuthenticationRememberMeForm()
    return {'login_form': form}
