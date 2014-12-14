from django import template
from booking.models import Treatment
register = template.Library()


@register.inclusion_tag('booking/treatment_slider.html')
def treatment_slider():
    treatments = Treatment.objects.all()
    return {'treatments': treatments}
