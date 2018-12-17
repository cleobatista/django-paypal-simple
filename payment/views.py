from django.views.generic import TemplateView, View
from django.http import HttpResponse, JsonResponse, Http404
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import User
from django.views.decorators.http import require_http_methods

from rest_framework.decorators import (
    api_view,
    permission_classes
)
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
api_view
from .models import (
    Product,
    Purchase,
    Coupon
)

from .forms import PurchaseForm

from .utils import create_json_paypal_body

import paypalrestsdk


class Create(TemplateView):
    template_name = 'index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['PAYPAL_ENVIRONMENT'] = settings.PAYPAL_ENVIRONMENT
        try:
            product = self.request.GET.get('product')
            context['product'] = Product.objects.get(path_name__iexact=product)
        except:
            raise Http404

        if 'coupon' in self.request.GET:
            try:
                coupon = self.request.GET.get('coupon')
                coupon_obj = Coupon.objects.get(code__iexact=coupon)
                if (
                    coupon_obj.product == context['product'] and
                    coupon_obj.expires_at > timezone.now()
                ):
                    context['coupon'] = coupon_obj
                    context['product'].discount = coupon_obj.discount * \
                        context['product'].price
                else:
                    context['errors'] = 'Cupom inválido para este produto'
            except:
                context['errors'] = 'Cupom inválido para este produto'

        if self.request.user.is_authenticated():
            last_purc = Purchase.objects.filter(email=self.request.user.email)
            if last_purc:
                form = PurchaseForm(instance=self.request.user,
                                    initial={'id_cpf': last_purc[0].id_cpf,
                                             'phone': last_purc[0].phone})
            else:
                form = PurchaseForm(instance=self.request.user)
        else:
            form = PurchaseForm()
        context['form'] = form

        return context

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name,
                      context=self.get_context_data())

    def post(self, request, *args, **kwargs):
        try:
            p = Product.objects.get(path_name=request.POST['product'])
        except:
            return HttpResponse("Product not found", status=404)
        if (
                request.POST['origin'] == 'pp' or
                request.POST['origin'] == 'without-paypal'
        ):
            form = PurchaseForm(request.POST)
            if not form.is_valid():
                import pdb;pdb.set_trace()
                return JsonResponse(form.errors, status=422)

        coupon_obj = Coupon.objects.filter(code=request.POST.get('coupon', False))
        pc = Purchase(product=p)

        if (
            coupon_obj.exists() and
            coupon_obj[0].product == p
        ):
            pc.coupon_used = coupon_obj.first()
            p.discount = pc.coupon_used.discount

        pc.save()

        ## if coupon used corresponds to product
        if (
                request.POST['origin'] == 'without-paypal' and
                coupon_obj.exists() and
                coupon_obj[0].product == p
        ):
            request.session['hash_session'] = pc.hash_session
            pc.first_name = form.cleaned_data['first_name']
            pc.last_name = form.cleaned_data['last_name']
            pc.id_cpf = form.cleaned_data['id_cpf']
            pc.email = form.cleaned_data['email']
            pc.phone = form.cleaned_data['phone']
            pc.completed = True
            pc.save()

            data = {'success': 'true'}
            return JsonResponse(data)

        body = create_json_paypal_body(product=p,
                                       purchase=pc,
                                       origin=request.POST['origin'])

        pc.log_request = body
        paypalrestsdk.configure({
            "mode": 'live' if settings.PAYPAL_ENVIRONMENT == 'production' else 'sandbox',
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_SECRET})
        payment = paypalrestsdk.Payment(body)
        if payment.create():
            pc.log_response = payment.to_dict()
            pc.payment_id = payment.id
            pc.save()
            request.session['hash_session'] = pc.hash_session
            appurl = [i['href'] for i in payment.links
                      if i['rel'] == 'approval_url'][0]
            data = {'id': payment.id, 'approvalUrl': appurl}
            return JsonResponse(data)
        else:
            return JsonResponse(payment.error)


class Execute(TemplateView):
    template_name = 'execute.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            p = self.request.session['hash_session']
            context['purchase'] = Purchase.objects.get(hash_session=p)
        except:
            raise Http404

        return context

    def post(self, request, *args, **kwargs):
        paypalrestsdk.configure({
            "mode": 'live' if settings.PAYPAL_ENVIRONMENT == 'production' else 'sandbox',  # sandbox or live
            "client_id": settings.PAYPAL_CLIENT_ID,
            "client_secret": settings.PAYPAL_SECRET})
        pc = Purchase.objects.get(hash_session=request.session['hash_session'])
        payment = paypalrestsdk.Payment.find(pc.payment_id)
        if payment.execute({"payer_id": request.POST['payer_id']}):
            pc.first_name = payment.payer.payer_info.first_name
            pc.last_name = payment.payer.payer_info.last_name
            pc.id_cpf = payment.payer.payer_info.tax_id
            pc.email = payment.payer.payer_info.email
            pc.phone = payment.payer.payer_info.phone
            pc.payment_id = payment.id
            pc.completed = True
            pc.log_execute = payment.to_dict()
            pc.save()

            ## Create user if not exists
            try:
                user, created = User.objects.get_or_create(
                    email=pc.email,
                    username="{0}{1}".format(pc.first_name, pc.last_name)
                    )
                if created:
                    user.first_name = pc.first_name,
                    user.last_name = pc.last_name,
                    user.save()
            except:
                pass
            return HttpResponse("Pagamento efetuado com sucesso")
        else:
            return JsonResponse(payment.error, status=500)

    def get(self, request, *args, **kwargs):
        try:
            pc = Purchase.objects.get(hash_session=
                                      request.session['hash_session'])
            if timezone.now() < pc.expires_session:
                return render(request, self.template_name,
                              context=self.get_context_data())
            else:
                raise ('expired session')
        except:
            return redirect(reverse("homepage:index"))


class Coupon_apply(View):
    def post(self, request, *args, **kwargs):
        try:
            coupon = Coupon.objects.get(code=request.POST['coupon'])
            product = Product.objects.get(path_name=request.POST['product'])
            if not (
                    coupon.product == product and
                    coupon.expires_at > timezone.now()
            ):
                raise ('invalid coupon')
            product.discount = product.price * coupon.discount
            data = {'price': product.price, "discount": product.discount}
            return JsonResponse(data)
        except Exception as error:
            return JsonResponse(error, status=422)

    def get(self, request, *args, **kwargs):
        return HttpResponse("Cannot GET", status=422)
