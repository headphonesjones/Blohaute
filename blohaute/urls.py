from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import TemplateView
from booking.views import (TreatmentList, TreatmentDetail, contact_view, package_checkout, schedule,
                           payment, available_times_for_day, unavailable_days, add_treatment_to_cart)

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^account/', include('accounts.urls')),
    url(r'^$', TemplateView.as_view(template_name="index.html"), name='home'),
    url(r'^about/', TemplateView.as_view(template_name="about.html"), name='about'),
    url(r'^contact/', contact_view, name='contact'),
    url(r'^stylists/', TemplateView.as_view(template_name="stylists.html"), name='stylists'),
    url(r'^partners/', TemplateView.as_view(template_name="partners.html"), name='partners'),

    url(r'^cart/', include('changuito.urls')),
    url(r'^schedule/', schedule, name='schedule'),
    url(r'^payment/', payment, name='payment'),

    url(r'^styles/', TemplateView.as_view(template_name="styles.html"), name='styles'),
    url(r'^book/', TreatmentList.as_view(template_name="services.html"), name='book'),
    url(r'^timesforday/', available_times_for_day, name='timesforday'),
    url(r'^unavailable_days/', unavailable_days, name='unavailable_days'),

    url(r'^(?P<slug>\w+)/$', TreatmentDetail.as_view(), name='treatment_detail'),
    url(r'^(?P<slug>\w+)/add/$', add_treatment_to_cart, name='treatment_book'),
    url(r'^(?P<slug>\w+)/package/(?P<pk>\d+)/checkout/$', package_checkout, name='package_checkout'),
)
