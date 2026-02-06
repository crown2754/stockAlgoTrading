from django.urls import path
from .views import (
    index,
    StockInfoAPIView,
    SaveStrategyAPIView,
    RunBacktestAPIView,
    UpdateStockDataAPIView,
    PaperTradingLeaderboardAPIView,  # 新增這個 View
)

urlpatterns = [
    path("", index, name="index"),
    path("stock/<str:symbol>/", StockInfoAPIView.as_view(), name="stock-info"),
    path("api/save/", SaveStrategyAPIView.as_view(), name="save-strategy"),
    path("api/run-backtest/", RunBacktestAPIView.as_view(), name="run-backtest"),
    path("api/update-stock/", UpdateStockDataAPIView.as_view(), name="update-stock"),
    
    # 新增排行榜 API 路徑
    path("api/leaderboard/", PaperTradingLeaderboardAPIView.as_view(), name="leaderboard"),
]