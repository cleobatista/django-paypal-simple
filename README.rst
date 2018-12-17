=====
Django-Paypal-Simple
=====

Django-Paypal-Simple is a simple app to use in Django to implement Paypal payments. Both Express Checkout and Paypal Plus.

Detailed documentation is in the "docs" directory.

Quick start
-----------

1. Add "django-paypal-simple" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...
        'django-paypal-simple',
    ]

2. Include the polls URLconf in your project urls.py like this::

    path('payment/', include('payment.urls')),

3. Run `python manage.py migrate` to create the polls models.

4. Start the development server and visit http://127.0.0.1:8000/admin/
   to create a product (you'll need the Admin app enabled).

5. Pay attention in 'path name' in product, that's need to be unique.

6. Visit http://127.0.0.1:8000/payment/<path name> to view product page with both options to payment.

7. Some pendencies:
	- Build a coupon treatment in app
	- Send a mail after the bought.