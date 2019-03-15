import time

from django.conf import settings
from django.urls import reverse_lazy
from django.utils.http import http_date

SPGATEWAY_DEFAULT_SAMESITE_COOKIE_NAME = 'spgateway_sessionid'


def spgateway_session_key_plain_encrypt_decrypt_function(session_key):
    return session_key


class SpgatewaySameSiteCookieMiddleware(object):
    def __init__(self, get_response):
        self.get_response = get_response
        self.return_url_set = set()
        self.encrypt_function = getattr(
            settings, 'SPGATEWAY_ANTISAMESITE_ENCRYPT_FUNCTION',
            spgateway_session_key_plain_encrypt_decrypt_function,
        )
        self.decrypt_function = getattr(
            settings, 'SPGATEWAY_ANTISAMESITE_DECRYPT_FUNCTION',
            spgateway_session_key_plain_encrypt_decrypt_function,
        )

        for shop_id, shop in settings.SPGATEWAY_PROFILE.items():
            return_url = shop.get('ReturnURL')
            if return_url:
                self.return_url_set.add(return_url)

        if not self.return_url_set:
            self.return_url_set.add(reverse_lazy('spgateway_ReturnView'))

    def __call__(self, request):

        response = self.get_response(request)

        if hasattr(settings, 'SESSION_COOKIE_SAMESITE') and settings.SESSION_COOKIE_SAMESITE:
            if request.path in self.return_url_set:
                antisamesite_session_cookie_name = getattr(
                    settings, 'SPGATEWAY_ANTISAMESITE_COOKIE_NAME',
                    SPGATEWAY_DEFAULT_SAMESITE_COOKIE_NAME,
                )
                encrypted_session_key = request.COOKIES.get(antisamesite_session_cookie_name)
                if encrypted_session_key:
                    session_key = self.decrypt_function(encrypted_session_key)
                    max_age = request.session.get_expiry_age()
                    expires_time = time.time() + max_age
                    expires = http_date(expires_time)

                    response.set_cookie(
                        settings.SESSION_COOKIE_NAME,
                        session_key, max_age=max_age,
                        expires=expires, domain=settings.SESSION_COOKIE_DOMAIN,
                        path=settings.SESSION_COOKIE_PATH,
                        secure=settings.SESSION_COOKIE_SECURE or None,
                        httponly=settings.SESSION_COOKIE_HTTPONLY or None,
                        samesite=settings.SESSION_COOKIE_SAMESITE,
                    )
                    response.delete_cookie(antisamesite_session_cookie_name)
            elif request.session.session_key:
                encrypted_session_key = self.encrypt_function(request.session.session_key)

                response.set_cookie(
                    key=getattr(settings, 'SPGATEWAY_ANTISAMSITE_COOKIE_NAME', SPGATEWAY_DEFAULT_SAMESITE_COOKIE_NAME),
                    value=encrypted_session_key
                )

        return response
