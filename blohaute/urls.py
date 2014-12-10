from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import TemplateView

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'blohaute.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', TemplateView.as_view(template_name="index.html")),
    url(r'^about/', TemplateView.as_view(template_name="about.html")),
    url(r'^blowouts/', TemplateView.as_view(template_name="blowouts.html")),
    url(r'^contact/', TemplateView.as_view(template_name="contacts.html")),
    url(r'^services/', TemplateView.as_view(template_name="services.html")),
    url(r'^stylists/', TemplateView.as_view(template_name="stylists.html")),
    url(r'^partners/', TemplateView.as_view(template_name="partners.html")),
)
