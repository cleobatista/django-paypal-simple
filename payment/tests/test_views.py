from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.test import Client

from ..models import (
    Product,
    Purchase,
)


class PaymentViewTest(TestCase):
    fixtures = ['users01.json', 'payment_data.json']

    ## common use
    def test_payment_product(self):
        signup_client = Client()
        data = {"product": "marvelous product"}
        response = signup_client.post(reverse('payment:create'), data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content
                         .decode("UTF-8")
                         .startswith("PAY-"), True)

    ## product unexists
    def test_payment_product_unexists(self):
        signup_client = Client()
        data = {"product": "strange product"}
        response = signup_client.post(reverse('payment:create'), data)

        self.assertEqual(response.status_code, 404)

    def test_payment_invalid_cpf(self):
        signup_client = Client()
        data = {"product": "marvelous product"}
        response = signup_client.post(reverse('payment:create'), data)
        self.assertEqual(response.status_code, 422)


    def test_coupon_url(self):
        """test if the coupon code is showing a product"""


class CodeValidationTest(TestCase):
    fixtures = ['payment_data.json']

    def setUp(self):
        self._product = Product.objects.get(pk=2)
        self._purchase = Purchase.objects.create(product=self._product,
                                                 code='xpto')

    '''
    def tearDown(self):
        pass
    '''

    def test_code_non_permit(self):
        resp = self.client.post(reverse('payment:service-code'),
                                {'code': 'foobar'})
        self.assertEqual(resp.status_code, 403)

    def test_code_accepted(self):
        resp = self.client.post(reverse('payment:service-code'),
                                {'code': 'xpto'})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'redirect_to_blocks')
