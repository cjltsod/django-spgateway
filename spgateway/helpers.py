import logging


class Warnings(object):
    def __init__(self, logger=None):
        self.warnings = list()
        self.logger = logger or logging

    def warning(self, message):
        self.warnings.append(message)
        self.logger.warning(message)

    def __bool__(self):
        if self.warnings:
            return True
        else:
            return False


def decrypt_TradeInfo_TradeSha(
    HashKey,
    HashIV,
    TradeInfo,
    TradeSha=None,
    use_json=True,
):
    from Crypto.Cipher import AES
    from Crypto.Hash import SHA256
    from urllib.parse import parse_qs
    import codecs
    import json

    def removepadding(message, blocksize=32):
        if message[-1] < blocksize:
            return message[:(-1 * ord(message[-1:])):]
        return message

    aes_obj = AES.new(HashKey, AES.MODE_CBC, HashIV)

    if TradeSha:
        hash = SHA256.new()
        hash.update('HashKey={}&{}&HashIV={}'.format(HashKey, TradeInfo, HashIV).encode())
        TradeSha_verify = hash.hexdigest().upper()
        if TradeSha != TradeSha_verify:
            raise Exception('TradeSha not match')

    TradeInfo_decrypted = removepadding(aes_obj.decrypt(codecs.decode(TradeInfo, 'hex_codec'))).decode()

    if use_json:
        TradeInfo_dict = json.loads(TradeInfo_decrypted)
    else:
        TradeInfo_dict = parse_qs(TradeInfo_decrypted)

    return TradeInfo_dict


def generate_TradeInfo_TradeSha(
    HashKey,                # HashKey
    HashIV,                 # HashIV
    MerchantID,             # 商店代號　　　　　　    智付通商店代號
                            ##################################################################################################
    MerchantOrderNo,        # 商店訂單編號　　　　    商店自訂訂單編號，限英、數字、”_ ” 格式。
    Amt,                    # 訂單金額　　　　　　    純數字不含符號 幣別:新台幣
    ItemDesc,               # 商品資訊　　　　　　    限制長度為 50 字
    Email=None,             # 付款人電子信箱
    LoginType=False,        # 智付通會員　　　　　    1=須要登入智付通會員 0=不須登入智付通會員
                            ##################################################################################################
    RespondType='JSON',     # 回傳格式　　　　　　    JSON 或是 String
    TimeStamp=None,         # 時間戳記　　　　　　    自從 Unix 纪元
    Version='1.4',          # 串接程式版本
    LangType='zh-tw',       # 語系　　　　　　　　    英文版參數為 en 繁體中文版參數為 zh-tw
                            # 　　　　　　　　　　    當未提供此參數或此參數數值錯誤時，將預設為繁體中文版
                            ##################################################################################################
    EmailModify=None,       # 不須登入智付通會員　    1=可修改(預設) 0=不可修改
    OrderComment=None,      # 商店備註　　　　　　    限制長度為 300 字 若有提供此參數，將會於 MPG 頁面呈現 商店備註內容
    TradeLimit=None,        # 交易限制秒數　　　　    秒數下限為 60 秒 上限為 900 秒 若未帶此參數，或是為 0 時，會視作為不啟用交易限制秒數。
    ExpireDate=None,        # 繳費有效期限　　　　    (適用於非即時交易) 格式為 date('Ymd') ，例:20140620
                            # 　　　　　　　　　　    此參數若為空值，系統預設為 7 天。自取 號時間起算至第 7 天 23:59:59。
                            ##################################################################################################
    ReturnURL=None,         # 支付完成返回商店網址    若為空值，交易完成後，消費者將停留在智付通付款或取號完成頁面
    NotifyURL=None,         # 支付通知網址
    CustomerURL=None,       # 商店取號網址　　　　    此參數若為空值，則會顯示取號結果在智付通頁面。
    ClientBackURL=None,     # 支付取消返回商店網址    此參數若為空值時，則無返回鈕。
                            ##################################################################################################
    CREDIT=None,            # 信用卡一次付清啟用　    設定是否啟用信用卡一次付清支付方式 1=啟用 0或者未有此參數=不啟用
    InstFlag=None,          # 信用卡分期付款啟用　    此欄位值=1 時，即代表開啟所有分期期別
                            # 　　　　　　　　　　    同時開啟多期別時，將此參數用","分隔，例如:3,6,12，代表開啟分 3、6、12期的功能
                            # 　　　　　　　　　　    此欄位值=0或無值時，即代表不開啟分期
    CreditRed=None,         # 信用卡紅利啟用　　　    1=啟用 0或者未有此參數=不啟用
    UNIONPAY=None,          # 信用卡銀聯卡啟用　　    1=啟用 0或者未有此參數=不啟用
    WEBATM=None,            # ＷＥＢＡＴＭ啟用　　    1=啟用 0或者未有此參數=不啟用
    VACC=None,              # ＡＴＭ轉帳啟用　　　    1=啟用 0或者未有此參數=不啟用
    CVS=None,               # 超商代碼繳費啟用　　    1=啟用 0或者未有此參數=不啟用 訂單金額小於30元或超過2萬元仍不會顯示此支付方式
    BARCODE=None,           # 超商條碼繳費啟用　　    1=啟用 0或者未有此參數=不啟用 訂單金額小於20元或超過4萬元仍不會顯示此支付方式
                            ##################################################################################################
    order_list=None,
    request=None,
    *args,
    **kwargs
):
    from Crypto.Cipher import AES
    from Crypto.Hash import SHA256
    from email.utils import parseaddr
    from urllib.parse import urlencode
    import datetime
    import re
    import time

    warnings = Warnings()

    def addpadding(message, blocksize=32):
        pad = blocksize - (len(message) % blocksize)
        return message + chr(pad) * pad

    if not isinstance(MerchantID, str):
        warnings.warning('MerchantID is not string')
        MerchantID = str(MerchantID)

    if not isinstance(MerchantOrderNo, str):
        MerchantOrderNo = str(MerchantOrderNo)
    if not re.match('^[A-Za-z0-9_]*$', MerchantOrderNo):
        warnings.warning('MerchantOrderNo only accept string contains only letters, numbers, and underscores. Bypass then')

    if not isinstance(Amt, int):
        warnings.warning('Amt is not integer')
        Amt = int(Amt)

    if not isinstance(ItemDesc, str):
        ItemDesc = str(ItemDesc)
        if len(ItemDesc) > 50:
            warnings.warning('Length of ItemDesc should be less than 50. Bypass then')

    if Email is not None:
        parsed_email = parseaddr(Email)[-1]
        if '@' in parsed_email and parsed_email != Email:
            warnings.warning('Email is not legal. Bypass then')
    else:
        warnings.warning('Email is not optional field. Bypass then')

    if LoginType is not None:
        LoginType = 1 if LoginType else 0
    else:
        warnings.warning('LoginType is not optional field. Bypass then')

    if RespondType not in ('JSON', 'String'):
        warnings.warning('RespondType should be \'JSON\' or \'String\'')

    if TimeStamp is None:
        TimeStamp = int(time.time())
    elif isinstance(TimeStamp, datetime.datetime):
        TimeStamp = int(TimeStamp.timestamp())
    elif isinstance(TimeStamp, int) or isinstance(TimeStamp, float):
        TimeStamp = int(datetime.datetime.fromtimestamp(TimeStamp).timestamp())
    elif isinstance(TimeStamp, str):
        warnings.warning('Unable to parse TimeStamp by . Bypass then')
    else:
        warnings.warning('TimeStamp not str, time, or datetime. Bypass then.')

    if Version != '1.4':
        warnings.warning('Version is not current version, which is 1.4')

    if LangType:
        if LangType not in ('en', 'zh-tw'):
            warnings.warning('LangType is not set to en or zh-tw. Service provider may use zh-tw instead. By pass then.')

    if TradeLimit is not None:
        if isinstance(TradeLimit, int):
            warnings.warning('TradeLimit is not integer. By pass then.')
        elif TradeLimit < 60:
            warnings.warning('TradeLimit is less than 60. Service provider may use 60 instead. By pass then.')
        elif TradeLimit > 900:
            warnings.warning('TradeLimit is greater than 900. Service provider may use 900 instead. By pass then.')

    if ExpireDate is not None:
        if isinstance(ExpireDate, datetime.datetime) or isinstance(ExpireDate, time):
            ExpireDate = ExpireDate.strftime('%Y%m%d')

    if EmailModify is not None:
        EmailModify = 1 if EmailModify else 0
    if OrderComment is not None:
        OrderComment = str(OrderComment) if OrderComment else None
    if CREDIT is not None:
        CREDIT = 1 if CREDIT else 0

    if InstFlag is not None:
        if InstFlag is True:
            InstFlag = '1'
        elif InstFlag is False:
            InstFlag = '0'
        elif isinstance(InstFlag, list):
            InstFlag = ','.join(InstFlag)

    if CreditRed is not None:
        CreditRed = 1 if CreditRed else 0
    if UNIONPAY is not None:
        UNIONPAY = 1 if UNIONPAY else 0
    if WEBATM is not None:
        WEBATM = 1 if WEBATM else 0
    if VACC is not None:
        VACC = 1 if VACC else 0
    if CVS is not None:
        CVS = 1 if CVS else 0
        if CVS:
            if Amt < 30 or Amt > 20000:
                warnings.warning('Service provider may not display CVS due to Amt is not between 30 and 20000')
    if BARCODE is not None:
        BARCODE = 1 if BARCODE else 0
        if BARCODE:
            if Amt < 20 or Amt > 40000:
                warnings.warning('Service provider may not display BARCODE due to Amt is not between 20 and 40000')

    if request:
        if ReturnURL and not ReturnURL.startswith('http://') and not ReturnURL.startswith('https://'):
            ReturnURL = request.build_absolute_uri(str(ReturnURL))
        if NotifyURL and not NotifyURL.startswith('http://') and not NotifyURL.startswith('https://'):
            NotifyURL = request.build_absolute_uri(str(NotifyURL))
        if CustomerURL and not CustomerURL.startswith('http://') and not CustomerURL.startswith('https://'):
            CustomerURL = request.build_absolute_uri(str(CustomerURL))
        if ClientBackURL and not ClientBackURL.startswith('http://') and not ClientBackURL.startswith('https://'):
            ClientBackURL = request.build_absolute_uri(str(ClientBackURL))

    if order_list is None:
        order_list = list()

    original_order_list = (
        'MerchantID',
        'RespondType',
        'TimeStamp',
        'Version',
        'LangType',
        'MerchantOrderNo',
        'Amt',
        'ItemDesc',
        'TradeLimit',
        'ExpireDate',
        'ReturnURL',
        'NotifyURL',
        'CustomerURL',
        'ClientBackURL',
        'Email',
        'EmailModify',
        'LoginType',
        'OrderComment',
        'CREDIT',
        'InstFlag',
        'CreditRed',
        'UNIONPAY',
        'WEBATM',
        'VACC',
        'CVS',
        'BARCODE',
    )

    aes_obj = AES.new(HashKey, AES.MODE_CBC, HashIV)
    message = dict(
        MerchantID=MerchantID,
        MerchantOrderNo=MerchantOrderNo,
        Amt=Amt,
        ItemDesc=ItemDesc,
        Email=Email,
        RespondType=RespondType,
        TimeStamp=TimeStamp,
        Version=Version,
        LangType=LangType,
        TradeLimit=TradeLimit,
        ExpireDate=ExpireDate,
        ReturnURL=ReturnURL,
        NotifyURL=NotifyURL,
        CustomerURL=CustomerURL,
        ClientBackURL=ClientBackURL,
        EmailModify=EmailModify,
        LoginType=LoginType,
        OrderComment=OrderComment,
        CREDIT=CREDIT,
        InstFlag=InstFlag,
        CreditRed=CreditRed,
        UNIONPAY=UNIONPAY,
        WEBATM=WEBATM,
        VACC=VACC,
        CVS=CVS,
        BARCODE=BARCODE,
    )

    message_list = list()

    for each_key in order_list:
        value = message.get(each_key)
        if value is not None:
            message_list.append((each_key, value))
    for each_key in original_order_list:
        value = message.get(each_key)
        if each_key not in order_list and value is not None:
            message_list.append((each_key, value))

    from collections import OrderedDict

    ordered_message = OrderedDict(message_list)

    message_str = addpadding(urlencode(ordered_message))
    TradeInfo = aes_obj.encrypt(message_str).hex()

    hash = SHA256.new()
    hash.update('HashKey={}&{}&HashIV={}'.format(HashKey, TradeInfo, HashIV).encode())
    TradeSha = hash.hexdigest().upper()

    return TradeInfo, TradeSha, warnings
