from django.conf.urls import patterns, url
from django.contrib.auth.views import logout
from accounts import views
from django.views.generic.base import TemplateView

urlpatterns = patterns(
    '',
    url(r'^registration/', views.register, name='register'),
    url(r'^logout/', logout, {'next_page': '/'}, name='logout'),
    url(r'^login/', views.login, name='login'),
    url(r'^welcome/', views.profile_view, name='welcome'),
    url(r'^delete/', views.UserDelete.as_view(), name='delete_user'),
    url(r'^reschedule/', TemplateView.as_view(template_name="registration/reschedule.html"), name='reschedule'),
)
