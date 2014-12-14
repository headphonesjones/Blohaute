from django import template
from booking.models import Treatment
register = template.Library()


@register.inclusion_tag('booking/service_menu.html')
def service_menu():
    treatments = Treatment.objects.all()
    return {'treatments': treatments}
