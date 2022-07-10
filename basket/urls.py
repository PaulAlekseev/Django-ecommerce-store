from django.urls import path

from . import views


app_name = 'basket'
urlpatterns = [
    path('', views.BasketView.as_view(), name='summary'),
    path('/add', views.basket_add, name='basket_add'),
]