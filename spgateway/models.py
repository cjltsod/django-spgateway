from django.conf import settings
from django.db import models
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse

import uuid

from .helpers import generate_TradeInfo_TradeSha
from .forms import SpgatewayForm


# Create your models here.
class SpgatewayResponseMixin(object):
    Status = models.CharField(max_length=10, verbose_name='回傳狀態')
    Message = models.CharField(max_length=50, verbose_name='回傳訊息')
    Result = models.TextField(verbose_name='回傳參數')


class SpgatewayNotifyResponseInfo(SpgatewayResponseMixin, models.Model):
    Order = models.ForeignKey(settings.SPGATEWAY_ORDERMODEL, verbose_name='訂單')
    MerchantID = models.CharField(max_length=15, verbose_name='商店代號')
    Amt = models.IntegerField(max_length=10, verbose_name='交易金額')
    TradeNo = models.CharField(max_length=20, verbose_name='智付通交易序號')
    MerchantOrderNo = models.CharField(max_length=20, verbose_name='商店訂單編號')
    PaymentType = models.CharField(max_length=10, verbose_name='支付方式')
    RespondType = models.CharField(max_length=10, verbose_name='回傳格式')
    PayTime = models.DateTimeField(verbose_name='支付完成時間')
    IP = models.CharField(max_length=15, verbose_name='交易 IP')
    EscrowBank = models.CharField(max_length=10, verbose_name='履保銀行')


class SpgatewayNotifyResponseCredit(models.Model):
    Info = models.ForeignKey(SpgatewayNotifyResponseInfo, on_delete=models.CASCADE)
    RespondCode = models.CharField(max_length=5, verbose_name='金融機構回應碼')
    Auth = models.CharField(max_length=6, verbose_name='授權碼')
    Card6No = models.CharField(max_length=6, verbose_name='卡號前六碼')
    Card4No = models.CharField(max_length=4, verbose_name='卡號末四碼')
    Inst = models.IntegerField(max_length=10, verbose_name='分期-期別')
    InstFirst = models.IntegerField(max_length=10, verbose_name='分期-首期金額')
    InstEach = models.IntegerField(max_length=10, verbose_name='分期-每期金額')
    ECI = models.CharField(max_length=2, verbose_name='ECI 值')
    TokenUseStatus = models.IntegerField(max_length=1, verbose_name='信用卡快速結帳使用狀態')
    RedAmt = models.IntegerField(max_length=5, null=True, verbose_name='紅利折抵後實際金額')


class SpgatewayNotifyResponseATM(models.Model):
    Info = models.ForeignKey(SpgatewayNotifyResponseInfo, on_delete=models.CASCADE)
    PayBankCode = models.CharField(max_length=10, verbose_name='付款人金融機構代碼')
    PayerAccount5Code = models.CharField(max_length=5, verbose_name='付款人金融機構帳號末五碼')


class SpgatewayNotifyResponseCVS(models.Model):
    Info = models.ForeignKey(SpgatewayNotifyResponseInfo, on_delete=models.CASCADE)
    CodeNo = models.CharField(max_length=30, verbose_name='繳費代碼')


class SpgatewayNotifyResponseBarcode(models.Model):
    Info = models.ForeignKey(SpgatewayNotifyResponseInfo, on_delete=models.CASCADE)
    Barcode_1 = models.CharField(max_length=20, verbose_name='第一段條碼')
    Barcode_2 = models.CharField(max_length=20, verbose_name='第二段條碼')
    Barcode_3 = models.CharField(max_length=20, verbose_name='第三段條碼')
    PayStore = models.CharField(max_length=8, verbose_name='繳費超商')


class SpgatewayCustomerResponseInfo(SpgatewayResponseMixin, models.Model):
    MerchantID = models.CharField(max_length=15, verbose_name='商店代號')
    Amt = models.IntegerField(max_length=10, verbose_name='交易金額')
    TradeNo = models.CharField(max_length=20, verbose_name='智付通交易序號')
    MerchantOrderNo = models.CharField(max_length=20, verbose_name='商店訂單編號')
    PaymentType = models.CharField(max_length=10, verbose_name='支付方式')
    ExpireDate = models.DateTimeField(verbose_name='繳費截止日期')


class SpgatewayCustomerResponseVACC(models.Model):
    Info = models.ForeignKey(SpgatewayCustomerResponseInfo, on_delete=models.CASCADE)
    BankCode = models.CharField(max_length=10, verbose_name='金融機構代碼')
    CodeNo = models.CharField(max_length=30, verbose_name='繳費代碼')


class SpgatewayCustomerResponseCVS(models.Model):
    Info = models.ForeignKey(SpgatewayCustomerResponseInfo, on_delete=models.CASCADE)
    CodeNo = models.CharField(max_length=30, verbose_name='繳費代碼')


class SpgatewayCustomerResponseBarcode(models.Model):
    Info = models.ForeignKey(SpgatewayCustomerResponseInfo, on_delete=models.CASCADE)
    Barcode_1 = models.CharField(max_length=20, verbose_name='第一段條碼')
    Barcode_2 = models.CharField(max_length=20, verbose_name='第二段條碼')
    Barcode_3 = models.CharField(max_length=20, verbose_name='第三段條碼')


def generate_slug():
    hex = uuid.uuid4().hex
    hex = hex.replace('-', '')
    return hex[:20]


class SpgatewayOrderMixin(models.Model):
    SpgatewaySlug = models.SlugField(max_length=20, null=True, unique=True)

    SpgatewayMerchantID = None
    SpgatewayAmt = None
    SpgatewayItemDesc = None
    SpgatewayEmail = None
    SpgatewayClientBackURL = None
    SpgatewayNotifyURL = None
    SpgatewayReturnURL = None
    SpgatewayCustomerURL = None
    SpgatewayLoginType = None
    SpgatewayInstFlag = None
    SpgatewayCreditRed = None

    SpgatewayMerchantIDFieldName = None
    SpgatewayAmtFieldName = None
    SpgatewayItemDescFieldName = None
    SpgatewayEmailFieldName = None
    SpgatewayClientBackURLFieldName = None
    SpgatewayNotifyURLFieldName = None
    SpgatewayReturnURLFieldName = None
    SpgatewayCustomerURLFieldName = None
    SpgatewayLoginTypeFieldName = None
    SpgatewayInstFlagFieldName = None
    SpgatewayCreditRedFieldName = None

    class Meta:
        abstract = True

    def save(self, **kwargs):
        if self.SpgatewaySlug in (None, ''):
            self.SpgatewaySlug = generate_slug()
        super(SpgatewayOrderMixin, self).save(**kwargs)

    def get_SpgatewayMerchantID(self, **kwargs):
        if 'MerchantID' in kwargs.keys():
            return kwargs['MerchantID']
        if 'MerchantIDFieldName' in kwargs.keys():
            return getattr(self, kwargs['MerchantIDFieldName'])
        if self.SpgatewayMerchantID is not None:
            return self.SpgatewayMerchantID
        if self.SpgatewayMerchantIDFieldName is not None:
            return getattr(self, self.SpgatewayMerchantIDFieldName)
        if 'MerchantProfile' in kwargs.keys():
            if 'MerchantID' in kwargs['MerchantProfile'].keys():
                return kwargs['MerchantProfile']['MerchantID']
            if 'MerchantIDFieldName' in kwargs['MerchantProfile'].keys():
                return getattr(self, kwargs['MerchantProfile']['MerchantIDFieldName'])

    def get_SpgatewayAmt(self, **kwargs):
        for each_profile in (kwargs, kwargs.get('MerchantProfile', dict())):
            if 'Amt' in each_profile.keys():
                return each_profile['Amt']
            if 'AmtFieldName' in each_profile.keys():
                return getattr(self, each_profile['AmtFieldName'])
        if self.SpgatewayAmt is not None:
            return self.SpgatewayAmt
        if self.SpgatewayAmtFieldName is not None:
            return getattr(self, self.SpgatewayAmtFieldName)
        raise ImproperlyConfigured('SpgatewayAmtFieldName not offered')

    def get_SpgatewayItemDesc(self, **kwargs):
        for each_profile in (kwargs, kwargs.get('MerchantProfile', dict())):
            if 'ItemDesc' in each_profile.keys():
                return each_profile['ItemDesc']
            if 'ItemDescFieldName' in each_profile.keys():
                return getattr(self, each_profile['ItemDescFieldName'])
        if self.SpgatewayItemDesc is not None:
            return self.SpgatewayItemDesc
        if self.SpgatewayItemDescFieldName is not None:
            return getattr(self, self.SpgatewayItemDescFieldName)
        raise ImproperlyConfigured('SpgatewayItemDescFieldName not offered')

    def get_SpgatewayEmail(self, **kwargs):
        for each_profile in (kwargs, kwargs.get('MerchantProfile', dict())):
            if 'Email' in each_profile.keys():
                return each_profile['Email']
            if 'EmailFieldName' in each_profile.keys():
                return getattr(self, each_profile['EmailFieldName'])
        if self.SpgatewayEmail is not None:
            return self.SpgatewayEmail
        if self.SpgatewayEmailFieldName is not None:
            return getattr(self, self.SpgatewayEmailFieldName)
        raise ImproperlyConfigured('SpgatewayEmailFieldName not offered')

    def get_SpgatewayClientBackURL(self, **kwargs):
        for each_profile in (kwargs, kwargs.get('MerchantProfile', dict())):
            if 'ClientBackURL' in each_profile.keys():
                return each_profile['ClientBackURL']
            if 'ClientBackURLFieldName' in each_profile.keys():
                return getattr(self, each_profile['ClientBackURLFieldName'])
        if self.SpgatewayClientBackURL is not None:
            return self.SpgatewayClientBackURL
        if self.SpgatewayClientBackURLFieldName is not None:
            return getattr(self, self.SpgatewayClientBackURLFieldName)
        if hasattr(self, 'get_absolute_url'):
            return self.get_absolute_url()
        return None

    def get_SpgatewayNotifyURL(self, **kwargs):
        print(kwargs)
        for each_profile in (kwargs, kwargs.get('MerchantProfile', dict())):
            if 'NotifyURL' in each_profile.keys():
                return each_profile['NotifyURL']
            if 'NotifyURLFieldName' in each_profile.keys():
                return getattr(self, each_profile['NotifyURLFieldName'])
        if self.SpgatewayNotifyURL is not None:
            return self.SpgatewayNotifyURL
        if self.SpgatewayNotifyURLFieldName is not None:
            return getattr(self, self.SpgatewayNotifyURLFieldName)

        return reverse('spgateway_NotifyView')

    def get_SpgatewayReturnURL(self, **kwargs):
        print(kwargs)
        for each_profile in (kwargs, kwargs.get('MerchantProfile', dict())):
            if 'ReturnURL' in each_profile.keys():
                return each_profile['ReturnURL']
            if 'ReturnURLFieldName' in each_profile.keys():
                return getattr(self, each_profile['ReturnURLFieldName'])
        if self.SpgatewayReturnURL is not None:
            return self.SpgatewayReturnURL
        if self.SpgatewayReturnURLFieldName is not None:
            return getattr(self, self.SpgatewayReturnURLFieldName)
        return reverse('spgateway_ReturnView')

    def get_SpgatewayCustomerURL(self, **kwargs):
        for each_profile in (kwargs, kwargs.get('MerchantProfile', dict())):
            if 'CustomerURL' in each_profile.keys():
                return each_profile['CustomerURL']
            if 'CustomerURLFieldName' in each_profile.keys():
                return getattr(self, each_profile['CustomerURLFieldName'])
        if self.SpgatewayCustomerURL is not None:
            return self.SpgatewayCustomerURL
        if self.SpgatewayCustomerURLFieldName is not None:
            return getattr(self, self.SpgatewayCustomerURLFieldName)
        if hasattr(self, 'get_absolute_url'):
            return self.get_absolute_url()
        return reverse('spgateway_CustomerView')

    def get_SpgatewayLoginType(self, **kwargs):
        for each_profile in (kwargs, kwargs.get('MerchantProfile', dict())):
            if 'LoginType' in each_profile.keys():
                return each_profile['LoginType']
            if 'LoginTypeFieldName' in each_profile.keys():
                return getattr(self, each_profile['LoginTypeFieldName'])
        if self.SpgatewayLoginType is not None:
            return self.SpgatewayLoginType
        if self.SpgatewayLoginTypeFieldName is not None:
            return getattr(self, self.SpgatewayLoginTypeFieldName)
        return None

    def get_SpgatewayInstFlag(self, **kwargs):
        for each_profile in (kwargs, kwargs.get('MerchantProfile', dict())):
            if 'InstFlag' in each_profile.keys():
                return each_profile['InstFlag']
            if 'InstFlagFieldName' in each_profile.keys():
                return getattr(self, each_profile['InstFlagFieldName'])
        if self.SpgatewayInstFlag is not None:
            return self.SpgatewayInstFlag
        if self.SpgatewayInstFlagFieldName is not None:
            return getattr(self, self.SpgatewayInstFlagFieldName)
        return None

    def get_SpgatewayCreditRed(self, **kwargs):
        for each_profile in (kwargs, kwargs.get('MerchantProfile', dict())):
            if 'CreditRed' in each_profile.keys():
                return each_profile['CreditRed']
            if 'CreditRedFieldName' in each_profile.keys():
                return getattr(self, each_profile['CreditRedFieldName'])
        if self.SpgatewayCreditRed is not None:
            return self.SpgatewayCreditRed
        if self.SpgatewayCreditRedFieldName is not None:
            return getattr(self, self.SpgatewayCreditRedFieldName)
        return None

    def _generate_new_kwargs(self, **kwargs):
        merchant_id = kwargs.get('MerchantID', settings.SPGATEWAY_MERCHANTID)
        merchant_profile = settings.SPGATEWAY_PROFILE[merchant_id]

        new_kwargs = dict(
            MerchantID=merchant_id,
            MerchantProfile=merchant_profile,
        )
        new_kwargs.update(kwargs)
        return new_kwargs

    def generate_form(self, **kwargs):
        new_kwargs = self._generate_new_kwargs(**kwargs)

        default_kwargs = dict(
            MerchantID=new_kwargs['MerchantID'],
            HashIV=new_kwargs['MerchantProfile']['HashIV'],
            HashKey=new_kwargs['MerchantProfile']['HashKey'],
            Amt=self.get_SpgatewayAmt(**new_kwargs),
            ItemDesc=self.get_SpgatewayItemDesc(**new_kwargs),
            Email=self.get_SpgatewayEmail(**new_kwargs),
            LoginType=self.get_SpgatewayLoginType(**new_kwargs),
            ClientBackURL=self.get_SpgatewayClientBackURL(**new_kwargs),
            MerchantOrderNo=self.SpgatewaySlug,
            NotifyURL=self.get_SpgatewayNotifyURL(**new_kwargs),
        )
        tradeinfo_kwargs = default_kwargs.copy()
        tradeinfo_kwargs.update(kwargs)

        TradeInfo, TradeSha, warnings = generate_TradeInfo_TradeSha(**tradeinfo_kwargs)

        form_initial_dict = dict(
            MerchantID=new_kwargs['MerchantID'],
            TradeInfo=TradeInfo,
            TradeSha=TradeSha,
        )

        return SpgatewayForm(initial=form_initial_dict)

    def generate_credit_form(self, **kwargs):
        kwargs = self._generate_new_kwargs(**kwargs)

        default_kwargs = dict(
            CREDIT=True,
            InstFlag=self.get_SpgatewayInstFlag(**kwargs),
            CreditRed=self.get_SpgatewayCreditRed(**kwargs),
            ReturnURL=self.get_SpgatewayReturnURL(**kwargs),
        )
        new_kwargs = default_kwargs.copy()
        new_kwargs.update(kwargs)
        return self.generate_form(**new_kwargs)

    def generate_webatm_form(self, **kwargs):
        kwargs = self._generate_new_kwargs(**kwargs)

        default_kwargs = dict(
            WEBATM=True,
            ReturnURL=self.get_SpgatewayReturnURL(**kwargs),
        )
        new_kwargs = default_kwargs.copy()
        new_kwargs.update(kwargs)
        return self.generate_form(**kwargs)

    def generate_cvs_form(self, **kwargs):
        kwargs = self._generate_new_kwargs(**kwargs)

        default_kwargs = dict(
            CVS=True,
            CustomerURL=self.get_SpgatewayCustomerURL(**kwargs),
        )
        new_kwargs = default_kwargs.copy()
        new_kwargs.update(kwargs)
        return self.generate_form(**kwargs)

    def generate_vacc_form(self, **kwargs):
        kwargs = self._generate_new_kwargs(**kwargs)

        default_kwargs = dict(
            VACC=True,
            CustomerURL=self.get_SpgatewayCustomerURL(**kwargs),
        )
        new_kwargs = default_kwargs.copy()
        new_kwargs.update(kwargs)
        return self.generate_form(**kwargs)

    def generate_barcode_form(self, **kwargs):
        kwargs = self._generate_new_kwargs(**kwargs)

        default_kwargs = dict(
            BARCODE=True,
            CustomerURL=self.get_SpgatewayCustomerURL(**kwargs),
        )
        new_kwargs = default_kwargs.copy()
        new_kwargs.update(kwargs)
        return self.generate_form(**kwargs)
