from django.apps import apps
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import generic
from django.views.decorators.csrf import csrf_exempt


from .helpers import decrypt_TradeInfo_TradeSha
from . import models

# Create your views here.


class SpgatewayMixin(object):
    OrderModel = apps.get_model(
        app_label=settings.SPGATEWAY_ORDERMODEL.rsplit('.', 1)[0],
        model_name=settings.SPGATEWAY_ORDERMODEL.rsplit('.', 1)[1],
    )

    @method_decorator(csrf_exempt)
    def dispatch(self, request, *args, **kwargs):
        return super(SpgatewayMixin, self).dispatch(request, *args, **kwargs)

    def get_TradeInfo(self, use_json=True):
        MerchantID = self.request.POST.get('MerchantID')
        TradeInfo_encrypted = self.request.POST.get('TradeInfo')
        TradeSha = self.request.POST.get('TradeSha', '')

        return decrypt_TradeInfo_TradeSha(
            HashKey=settings.SPGATEWAY_PROFILE[MerchantID]['HashKey'],
            HashIV=settings.SPGATEWAY_PROFILE[MerchantID]['HashIV'],
            TradeInfo=TradeInfo_encrypted,
            TradeSha=TradeSha,
            use_json=use_json,
        )

    def get_order(self, **kwargs):
        order_obj = None
        order_list = self.OrderModel.objects.filter(SpgatewaySlug=kwargs.get('slug'))
        if order_list:
            order_obj = order_list[0]
        if not order_obj:
            info_list = models.SpgatewayNotifyResponseInfo.objects.filter(MerchantOrderNo=kwargs.get('slug'))
            order_obj = info_list[0].Order if info_list else None
        if not order_obj:
            info_list = models.SpgatewayCustomerResponseInfo.objects.filter(MerchantOrderNo=kwargs.get('slug'))
            order_obj = info_list[0].Order if info_list else None
        if not order_obj:
            raise Http404('No matches the given query.')
        return order_obj

    def get_context_data(self, **kwargs):
        context = {
            'SpgatewayTradeInfo': self.get_TradeInfo(),
        }
        context.update(kwargs)
        return super(SpgatewayMixin, self).get_context_data(**context)

    def get_success_url(self):
        if hasattr(self, 'success_url') and self.success_url:
            return self.success_url.format(**self.object.__dict__)
        elif hasattr(self.object, 'get_absolute_url'):
            return self.object.get_absolute_url()
        else:
            raise ImproperlyConfigured(
                "No URL to redirect to. Provide a success_url.")


class SpgatewayReturnView(SpgatewayMixin, generic.View):
    model = None
    template_name = 'spgateway/response.html'

    def __init__(self, *args, **kwargs):
        self.model = self.OrderModel
        super(SpgatewayReturnView, self).__init__(*args, **kwargs)

    def get_object(self, queryset=None):
        return self.object

    def post(self, request, *args, **kwargs):
        self.request = request
        self.trade_info = self.get_TradeInfo()
        self.object = self.get_order(slug=self.trade_info.get('Result', {}).get('MerchantOrderNo'))

        self.send_notify()

        success_url = self.get_success_url()

        if hasattr(self, 'template_name'):
            result = render(
                self.request, self.template_name,
                {'success_url': success_url, 'TradeInfo': self.trade_info},
            )
        else:
            result = HttpResponseRedirect(success_url)

        return result

    def send_notify(self):
        if hasattr(self.object, 'spgateway_return'):
            self.object.spgateway_return(self.request, self.trade_info)


class SpgatewayResponseViewMixin(SpgatewayMixin):
    def get_base_model(self, trade_info=None):
        raise ImproperlyConfigured('get_base_model not defined')

    def get_additional_model(self, trade_info=None):
        raise ImproperlyConfigured('get_addtional_model not defined')

    def post(self, request, *args, **kwargs):
        self.request = request
        self.trade_info = self.get_TradeInfo()
        self.object = self.get_order(slug=self.trade_info.get('Result', {}).get('MerchantOrderNo'))

        base_model = self.get_base_model(self.trade_info)
        additional_model = self.get_additional_model(self.trade_info)

        object = base_model()
        additional_object = additional_model(Info=object)

        trade_info_result = self.trade_info.get('Result', {})
        trade_info_result_keys = trade_info_result.keys()
        for each_object in [object, additional_object]:
            for each_field in each_object._meta.get_fields():
                if each_field.name in trade_info_result_keys:
                    setattr(each_object, each_field.name, trade_info_result[each_field.name])

        object.Order = self.object
        object.save()
        additional_object.Info = object
        additional_object.save()

        status = self.trade_info['Status']
        if status != 'SUCCESS':
            if self.object.SpgatewaySlug == self.trade_info.get('Result', {}).get('MerchantOrderNo'):
                self.object.regenerate_slug()

        self.send_notify()

        success_url = self.get_success_url()

        if hasattr(self, 'template_name'):
            result = render(self.request, self.template_name, {'success_url': success_url, 'TradeInfo': self.trade_info})
        else:
            result = HttpResponseRedirect(success_url)

        return result


class SpgatewayNotifyView(SpgatewayResponseViewMixin, generic.View):
    template_name = 'spgateway/response.html'

    def get_base_model(self, trade_info=None):
        return models.SpgatewayNotifyResponseInfo

    def get_additional_model(self, trade_info=None):
        if trade_info is None:
            if self.trade_info:
                trade_info = self.trade_info
            else:
                trade_info = self.trade_info = self.get_TradeInfo()

        payment_type = trade_info.get('Result', {}).get('PaymentType')
        if payment_type == 'CREDIT':
            return models.SpgatewayNotifyResponseCredit
        elif payment_type == 'WEBATM':
            return models.SpgatewayNotifyResponseATM
        elif payment_type == 'VACC':
            return models.SpgatewayNotifyResponseATM
        elif payment_type == 'CVS':
            return models.SpgatewayNotifyResponseCVS
        elif payment_type == 'BARCODE':
            return models.SpgatewayNotifyResponseBarcode
        else:
            raise Exception('Unknown payment_type')

    def send_notify(self):
        if hasattr(self.object, 'spgateway_notify'):
            self.object.spgateway_notify(self.request, self.trade_info)


class SpgatewayCustomerView(SpgatewayResponseViewMixin, generic.View):
    def get_base_model(self, trade_info=None):
        return models.SpgatewayCustomerResponseInfo

    def get_additional_model(self, trade_info=None):
        if trade_info is None:
            if self.trade_info:
                trade_info = self.trade_info
            else:
                trade_info = self.trade_info = self.get_TradeInfo()

        payment_type = trade_info.get('Result', {}).get('PaymentType')
        if payment_type == 'VACC':
            return models.SpgatewayCustomerResponseVACC
        elif payment_type == 'CVS':
            return models.SpgatewayCustomerResponseCVS
        elif payment_type == 'BARCODE':
            return models.SpgatewayCustomerResponseBarcode
        else:
            raise Exception('Unknown payment_type')

    def send_notify(self):
        if hasattr(self.object, 'spgateway_customer'):
            self.object.spgateway_customer(self.request, self.trade_info)
