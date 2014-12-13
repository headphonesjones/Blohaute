from django.conf.urls import patterns, include, url
from django.contrib import admin
from django.views.generic.base import TemplateView

urlpatterns = patterns(
    '',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^account/', include('accounts.urls')),
    url(r'^$', TemplateView.as_view(template_name="index.html"), name='home'),
    url(r'^about/', TemplateView.as_view(template_name="about.html"), name='about'),
    url(r'^blowouts/', TemplateView.as_view(template_name="blowouts.html"), name='blowouts'),
    url(r'^braids/', TemplateView.as_view(template_name="braids.html"), name='braids'),
    url(r'^upstyles/', TemplateView.as_view(template_name="upstyles.html"), name='upstyles'),
    url(r'^contact/', TemplateView.as_view(template_name="contact.html"), name='contact'),
    url(r'^services/', TemplateView.as_view(template_name="services.html"), name='services'),
    url(r'^stylists/', TemplateView.as_view(template_name="stylists.html"), name='stylists'),
    url(r'^partners/', TemplateView.as_view(template_name="partners.html"), name='partners'),
    url(r'^cart/', TemplateView.as_view(template_name="cart.html"), name='cart'),
    url(r'^book/', TemplateView.as_view(template_name="book.html"), name='book'),
    url(r'^checkout/', TemplateView.as_view(template_name="checkout.html"), name='checkout'),
    url(r'^password_lost/', TemplateView.as_view(template_name="password.html"), name='password'),
    #url(r'^password_change/', TemplateView.as_view(template_name="passwordchange.html"), name='passwordchange'),
)
