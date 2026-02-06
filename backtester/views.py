from rest_framework.views import APIView
from rest_framework.response import Response
import yfinance as yf
from .serializers import StockDataSerializer
from datetime import datetime
from django.shortcuts import render

class StockInfoAPIView(APIView):
    def get(self, request, symbol):
        # 自動處理代號：如果是純數字，自動補上 .TW
        if symbol.isdigit():
            symbol = f"{symbol}.TW"
            
        ticker = yf.Ticker(symbol)
        # 改用 5d 確保至少能抓到最近一個交易日的資料
        hist = ticker.history(period='5d')
        
        if not hist.empty:
            last_row = hist.iloc[-1]
            data = {
                'symbol': symbol,
                'last_price': round(float(last_row['Close']), 2),
                'date': hist.index[-1].strftime('%Y-%m-%d'),
                'message': "Success"
            }
        else:
            data = {'symbol': symbol, 'last_price': 0, 'date': "", 'message': "Symbol not found or no data"}

        serializer = StockDataSerializer(data)
        return Response(serializer.data)
    
def index(request):
    return render(request, 'backtester/index.html')