from django.conf.urls import patterns, url, include
from django.contrib.auth.views import logout
from accounts import views
from django.views.generic.base import TemplateView

urlpatterns = patterns(
    '',
    url(r'^registration/', views.register, name='register'),
    url(r'^logout/', views.logout, {'next_page': '/'}, name='logout'),
    url(r'^login/', views.login, name='login'),
    url(r'^forgot_password/', views.forgot_password, name='forgot_password'),
    url(r'^forgot_success/', TemplateView.as_view(template_name="registration/forgot_success.html"), name='forgot_success'),
    url(r'^reset_password/', views.reset_forogtten_password, name='reset_password'),

    url(r'^welcome/', views.profile_view, name='welcome'),
    url(r'^delete/', views.UserDelete.as_view(), name='delete_user'),
    url(r'^appointments/(?P<pk>\d+)/cancel/$', views.cancel_view, name='cancel'),
    url(r'^appointments/(?P<pk>\d+)/reschedule/$', views.reschedule, name='reschedule'),
    url(r'^appointments/(?P<pk>\d+)/reschedule/days/$', views.reschedule_days, name='reschedule_days'),
    url(r'^appointments/(?P<pk>\d+)/reschedule/times/$', views.reschedule_times, name='reschedule_times'),
)