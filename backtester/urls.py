from django.urls import path
from .views import StockInfoAPIView, index

urlpatterns = [
    path('', index, name='index'), 
    path('stock/<str:symbol>/', StockInfoAPIView.as_view(), name='stock-info'),
]