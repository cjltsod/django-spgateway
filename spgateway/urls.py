from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^return/$', views.SpgatewayReturnView.as_view(), name='spgateway_ReturnView'),
    url(r'^customer/$', views.SpgatewayCustomerView.as_view(), name='spgateway_CustomerView'),
    url(r'^notify/$', views.SpgatewayNotifyView.as_view(), name='spgateway_NotifyView'),
]
