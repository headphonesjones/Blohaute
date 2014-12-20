from django.conf.urls import patterns, url
from django.contrib.auth.views import logout
from accounts import views
from django.views.generic.base import TemplateView

urlpatterns = patterns(
    '',
    url(r'^registration/', views.register, name='register'),
    url(r'^logout/', logout, {'next_page': '/'}, name='logout'),
    url(r'^login/', views.login, name='login'),
    url(r'^forgot_password/', views.forgot_password, name='forgot_password'),
    url(r'^forgot_success/', TemplateView.as_view(template_name="registration/forgot_success.html"), name='forgot_success'),
    url(r'^reset_password/', views.reset_forogtten_password, name='reset_password'),

    url(r'^welcome/', views.profile_view, name='welcome'),
    url(r'^delete/', views.UserDelete.as_view(), name='delete_user'),
    url(r'^reschedule/', TemplateView.as_view(template_name="registration/reschedule.html"), name='reschedule'),
    url(r'^cancel/', views.cancel_view, name='cancel')

)
