from django import forms
from django.conf import settings


class SpgatewayForm(forms.Form):
    MerchantID = forms.CharField(max_length=15, widget=forms.HiddenInput())
    TradeInfo = forms.CharField(widget=forms.HiddenInput())
    TradeSha = forms.CharField(widget=forms.HiddenInput())
    Version = forms.CharField(max_length=5, initial='1.4', widget=forms.HiddenInput())
    action = 'https://ccore.spgateway.com/MPG/mpg_gateway' if settings.DEBUG else 'https://core.spgateway.com/MPG/mpg_gateway'
