from django.contrib import admin

from .models import (
    Product,
    Coupon,
    Purchase
    )

admin.site.register(Product)
admin.site.register(Coupon)
admin.site.register(Purchase)
