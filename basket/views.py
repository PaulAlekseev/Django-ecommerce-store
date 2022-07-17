from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views import generic
from django.db.models import Sum, Q

from .basket import Basket
from store.models import Product

import json


class BasketView(generic.list.ListView):
    template_name = 'basket/basket.html'
    context_object_name = 'Products'

    def get_queryset(self):
        basket = Basket(self.request)
        return basket

    def get_context_data(self):
        context = super().get_context_data()
        context['Total_price'] = sum(item['total'] for item in context['Products'])
        return context

    def post(self, request, *args, **kwargs):
        basket = Basket(request) 
        data = request.POST
        product_id = int(data['productid'])

        basket.add(product_id=product_id)

        return HttpResponse('1')
    
    def patch(self, request, *args, **kwargs):
        basket = Basket(request)
        data = json.loads(request.body)
        product_id = data['product_id']
        responce_data = {}
        current_amount = basket.basket[str(product_id)]['amount']
        required_amount = int(data['product_amount'])

        product = Product.objects.filter(id=product_id).annotate(
                    overall_amount=Sum('storeproduct__amount', filter=Q(id__exact=product_id))
            )[0]

        difference = required_amount - current_amount
        if product.overall_amount:
            if product.overall_amount >= required_amount and required_amount >= 0:
                basket.update_item(product_id, required_amount)
                responce_data['agreement'] = True
                responce_data['total_product'] = required_amount * product.price
                responce_data['total'] = int(data['total_price']) + difference * product.price
            else:
                responce_data['agreement'] = False
                responce_data['amount'] = current_amount
        else:
            responce_data['agreement'] = 'Out of stock'

        response = JsonResponse(responce_data)
        return response

    def delete(self, request, *args, **kwargs):
        basket = Basket(request)
        data = json.loads(request.body)
        response_data = {}
        product_id = data['product_id']
        total_price = data['total_price']
        current_amount = basket.basket[str(product_id)]['amount']
        
        product = Product.objects.get(id=product_id)

        response_data['total'] = str(int(total_price) - product.price * current_amount)
        
        basket.delete_product(product_id)

        responce = JsonResponse(response_data)
        return responce


