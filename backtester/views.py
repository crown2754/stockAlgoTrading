from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import yfinance as yf
from datetime import datetime
from .models import BacktestStrategy
from django.contrib.auth.models import User

# 1. 渲染首頁的 Function
def index(request):
    return render(request, 'backtester/index.html')

# 2. 抓取股票資訊的 API
class StockInfoAPIView(APIView):
    def get(self, request, symbol):
        if symbol.isdigit():
            symbol = f"{symbol}.TW"
            
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period='5d') # 使用 5d 確保能抓到資料
        
        if not hist.empty:
            last_row = hist.iloc[-1]
            data = {
                'symbol': symbol,
                'last_price': round(float(last_row['Close']), 2),
                'date': hist.index[-1].strftime('%Y-%m-%d'),
                'message': "Success"
            }
            return Response(data)
        return Response({'message': "No data found"}, status=status.HTTP_404_NOT_FOUND)

# 3. 儲存策略的 API
class SaveStrategyAPIView(APIView):
    def post(self, request):
        symbol = request.data.get('symbol')
        user = User.objects.first() # 暫時關聯至首位使用者
        
        if symbol:
            strategy = BacktestStrategy.objects.create(
                user=user,
                name=f"手動儲存 - {symbol}",
                buy_threshold=20,
                sell_threshold=80
            )
            return Response({"message": f"策略 {symbol} 已存入資料庫"}, status=status.HTTP_201_CREATED)
        return Response({"error": "資料不完整"}, status=status.HTTP_400_BAD_REQUEST)