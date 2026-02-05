from django.urls import path
from .views import StockInfoAPIView, SaveStrategyAPIView, index

urlpatterns = [
    path('', index, name='index'), # 首頁
    path('stock/<str:symbol>/', StockInfoAPIView.as_view(), name='stock-info'), # 抓取資料 API
    path('api/save/', SaveStrategyAPIView.as_view(), name='save-strategy'), # 儲存策略 API
]