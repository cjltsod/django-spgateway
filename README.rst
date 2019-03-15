====================
Spgateway for Django
====================

Write Django and your store as usual, and let ``django-spgateway`` handle your transactions with Spgateway

Requirements
------------
- Python 3.7
- Django 2.1
- pycrypto 2.6.1
- We only tested on environment as below

Installation
------------

1. Install using pip or pipenv:

   ``pip install django-spgageway``

   Alternatively, you can install download or clone this repo and call ``pip install -e .``.

2. Add to INSTALLED_APPS in your ``settings.py``:

   ``'spgateway',``

3. Add settings in your ``settings.py``:

   .. code:: Python

    SPGATEWAY_PROFILE = {
        'YOUR_MerchantID': {
            'MerchantID': 'YOUR_MerchantID',
            'HashKey': 'YOUR_HashKey',
            'HashIV': 'YOUR_HashIV',
        },
    }
    SPGATEWAY_MERCHANTID = 'YOUR_MerchantID'
    SPGATEWAY_ORDERMODEL = 'yourapp.Order'


4. Add urlpattern into your ``urls.py``:

   ``path('spgateway/', include('spgateway.urls')),`` for Django 2

   ``url(r'^spgateway/', include('spgateway.urls')),`` for Django 1

5. Import ``from spgateway.models import SpgatewayOrderMixin`` and inherit from it with your order model.

6. Run ``python manage.py makemigrations`` and ``python manage.py migrate`` as usual.

7. Get form from your order by calling ``generate_credit_form`` in view:

   ``credit_form = order_object.generate_credit_form(request)``

   And use it in your template:

   .. code:: Django

    <form action="{{ credit_form.action }}" method="POST">
        {{ credit_form.as_p }}
        <input type="submit">
    </form>

8. Add ``SpgatewaySameSiteCookieMiddleware`` before ``SessionMiddleware`` to avoid SameSite cookie while return from payment gateway:

   .. code:: Python

    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'spgateway.middleware.SpgatewaySameSiteCookieMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        ...
    ]

Example model
-------------

   .. code:: Python

    from spgateway.models import SpgatewayOrderMixin

    class Order(SpgatewayOrderMixin, models.Model):
        total = models.IntegerField(default=0, verbose_name='Total Price')
        user = models.ForeignKey(User, verbose_name='Order by user')
        is_paid = models.BooleanField(default=False)

        # Add this parameter to let django-spgateway know which field is amount of price
        SpgatewayAmtFieldName = 'total'

        # Add this parameter to let django-spgateway set item description
        SpgatewayItemDesc = 'Items descriptions'

        # Add this method to let django-spgateway retrieve email
        def get_SpgatewayEmail(self, **kwargs):
            return self.user.email

        # Add this method let django-spgateway call when notify from Spgateway server
        # Change your order with this method
        def spgateway_notify(self, request, trade_info):
            status = trade_info['Status']
            status_msg = trade_info['Message']

            if status == 'SUCCESS':
                self.is_paid = True
                self.save()
            else:
                # TODO: Handle error

        # Add this method let django-spgateway call when client return from Spgateway server
        # Never trust data from client. Display messages only
        def spgateway_return(self, request, trade_info):
            status = trade_info['Status']
            status_msg = trade_info['Message']

            if status == 'SUCCESS':
                # TODO: Display success message to user
            else:
                # TODO: Display error message to user

        # django-spgateway will call this method to redirect user after user return from Spgateway server
        def get_absolute_url(self):
            return reverse('ORDER_DETAIL_VIEW_NAME_HERE')


Bugs and suggestions
--------------------

If you have found a bug or if you have a request for additional functionality, please use the issue tracker on GitHub.

https://github.com/cjltsod/django-spgateway/issues


License
-------

You can use this under MIT. See `LICENSE
<LICENSE>`_ file for details.

Author
------

Developed and maintained by `CJLTSOD <https://about.me/cjltsod/>`_.

Thanks to everybody that has contributed pull requests, ideas, issues, comments and kind words.

Please see AUTHORS.rst for a list of contributors.
