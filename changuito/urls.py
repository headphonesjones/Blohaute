from django.conf.urls import patterns, url
from django.contrib.auth.views import logout
from changuito import views
urlpatterns = patterns(
    '',
    url(r'^$', views.shopping_cart, name='cart'),
    url(r'remove_item/$', views.remove_cart_item, name='remove_cart_item'),
    url(r'update_quantity/$', views.update_quanity, name='update_quantity')
)
