from django.db import models
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator
)
from django.core import mail

import uuid
import hashlib


def create_uuid():
    return uuid.uuid4().hex[:8].lower()


class Product(models.Model):
    name = models.CharField(max_length=128)
    shipping = models.DecimalField(max_digits=6, decimal_places=2,
                                   default=0.00)
    description = models.TextField(max_length=256, null=True, blank=True)
    path_name = models.CharField(max_length=128, unique=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    discount = models.DecimalField(max_digits=6, decimal_places=2,
                                   default=0.00)
    active = models.BooleanField(default=True)


class Coupon(models.Model):
    code = models.CharField(max_length=128, unique=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    product = models.ForeignKey(Product)
    discount = models.DecimalField(max_digits=6, decimal_places=2,
                                   default=0.00,
                                   validators=[
                                       MaxValueValidator(1.00),
                                       MinValueValidator(0.00)
                                   ]
                                   )


class Purchase(models.Model):
    first_name = models.CharField(max_length=128, null=True, blank=True)
    last_name = models.CharField(max_length=128, null=True, blank=True)
    id_cpf = models.CharField(max_length=11, null=True, blank=True)
    email = models.EmailField(max_length=256, null=True, blank=True)
    phone = models.CharField(max_length=15, null=True, blank=True)
    product = models.ForeignKey(Product)
    purchased_at = models.DateTimeField(auto_now_add=True)
    payment_id = models.CharField(max_length=528, null=True, blank=True)
    hash_session = models.CharField(max_length=256, null=True, blank=True)
    expires_session = models.DateTimeField()
    completed = models.BooleanField(default=False)
    log_request = models.TextField(null=True, blank=True)
    log_response = models.TextField(null=True, blank=True)
    log_execute = models.TextField(null=True, blank=True)
    invoice_number = models.CharField(max_length=10, default=create_uuid,
                                      unique=True)
    coupon_used = models.ForeignKey(Coupon, blank=True, null=True)

    def save(self, *args, **kwargs):
        """
        Saves the expires_session with 30 minutes to finalize the sale,
        Creates a hash session to identify user when the payment is done
        Creates a invoice_number
        """
        from django.utils import timezone as tm
        if not self.hash_session:
            self.hash_session = hashlib.sha256(str(uuid.uuid4())
                                       .encode("utf-8")) \
                                       .hexdigest()
        self.expires_session = tm.now() + tm.timedelta(minutes=30)
        super().save(*args, **kwargs)
