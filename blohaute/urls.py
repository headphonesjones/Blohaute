from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import TemplateView
from booking.views import (TreatmentList, TreatmentDetail, contact_view, schedule, PackagePaymentView,
                           PaymentView, available_times_for_day, add_treatment_to_cart,
                           AppointmentList, TimeSlotList, CreateAppointment, CancelAppointment, AvailableStylistList)
from accounts.views import UserProfile, ObtainAuthToken, ForgotPassword, RegisterUser

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^account/', include('accounts.urls')),
    url(r'^$', TemplateView.as_view(template_name="index.html"), name='home'),
    url(r'^about/', TemplateView.as_view(template_name="about.html"), name='about'),
    url(r'^contact/', contact_view, name='contact'),
    url(r'^stylists/', TemplateView.as_view(template_name="stylists.html"), name='stylists'),
    url(r'^products/', TemplateView.as_view(template_name="products.html"), name='products'),

    url(r'^cart/', include('changuito.urls')),
    url(r'^schedule/', schedule, name='schedule'),
    url(r'^payment/', PaymentView.as_view(), name='payment'),

    url(r'^styles/', TemplateView.as_view(template_name="styles.html"), name='styles'),
    url(r'^book/', TreatmentList.as_view(template_name="services.html"), name='book'),
    url(r'^timesforday/', available_times_for_day, name='timesforday'),

    url(r'^(?P<slug>\w+)/$', TreatmentDetail.as_view(), name='treatment_detail'),
    url(r'^(?P<slug>\w+)/add/$', add_treatment_to_cart, name='treatment_book'),
    url(r'^(?P<slug>\w+)/package/(?P<pk>\d+)/checkout/$', PackagePaymentView.as_view(), name='package_checkout'),

    url(r'^api/auth/login/$', ObtainAuthToken.as_view()),
    url(r'^api/auth/forgot_password/$', ForgotPassword.as_view()),
    url(r'^api/auth/register/$', RegisterUser.as_view()),
    url(r'^api/profile/$', UserProfile.as_view()),
    url(r'^api/appointments/$', AppointmentList.as_view()),
    url(r'^api/appointments/book/$', CreateAppointment.as_view()),
    url(r'^api/appointments/(?P<booker_id>\d+)/cancel/$', CancelAppointment.as_view()),
    url(r'^api/availability/(?P<booker_id>\d+)/(?P<year>\d+)/(?P<month>\d+)/(?P<day>\d+)/$', TimeSlotList.as_view()),
    url(r'^api/availability/stylists/$', AvailableStylistList.as_view(), name="available_stylists")

)
