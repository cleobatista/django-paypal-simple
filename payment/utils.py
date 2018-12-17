from django.contrib.sites.models import Site

def create_json_paypal_body(product, purchase, origin="ec"):
    data = {
        "intent": "sale",
        "payer": {
            "payment_method": "paypal"
        },
        "transactions": [
            {
                "amount": {
                    "total": str(product.price - product.discount),
                    "currency": "BRL",
                },
                "description": product.description,
                "payment_options": {
                    "allowed_payment_method": "INSTANT_FUNDING_SOURCE"
                },
                "invoice_number": str(purchase.invoice_number),
                "item_list": {
                    "items": [
                        {
                            "name": product.name,
                            "description": product.description,
                            "price": str(product.price),
                            "quantity": "1",
                            "sku": str(product.id),
                            "currency": "BRL"
                        },
                        {
                            "name": "discount",
                            "price": str(- product.discount),
                            "quantity": "1",
                            "sku": str(product.id),
                            "currency": "BRL"
                        }
                    ],
                }
            }
        ],
        "note_to_payer": "Contactusforanyquestionsonyourorder.",
        "redirect_urls": {
            "return_url": Site.objects.get_current().domain,
            "cancel_url": Site.objects.get_current().domain
        }
    }
    if origin == "pp":
        application_context = {"brand_name": "My_brand",
                               "shipping_preference": "NO_SHIPPING"}
        data['application_context'] = application_context
    return data
