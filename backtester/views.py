from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import yfinance as yf
import pandas as pd
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db.models import Max

# 匯入你的資料庫模型與回測引擎
from .models import BacktestStrategy, StockHistory, PaperTrading
from .engine.runner import run_backtest_from_db


def index(request):
    return render(request, "backtester/index.html")


class StockInfoAPIView(APIView):
    def get(self, request, symbol):
        if symbol.isdigit() and not symbol.endswith(".TW"):
            symbol = f"{symbol}.TW"
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="5d")
            if not hist.empty:
                last_row = hist.iloc[-1]
                return Response(
                    {
                        "symbol": symbol,
                        "last_price": round(float(last_row["Close"]), 2),
                        "date": hist.index[-1].strftime("%Y-%m-%d"),
                    }
                )
            return Response({"error": "No data"}, status=404)
        except Exception as e:
            return Response({"error": str(e)}, status=500)


class SaveStrategyAPIView(APIView):
    def post(self, request):
        symbol = request.data.get("symbol")
        user = User.objects.first()
        if symbol:
            BacktestStrategy.objects.create(
                user=user,
                name=f"手動儲存-{symbol}",
                buy_threshold=20,
                sell_threshold=80,
            )
            return Response({"message": "策略已儲存"}, status=201)
        return Response({"error": "資料不全"}, status=400)


@method_decorator(csrf_exempt, name="dispatch")
class RunBacktestAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        try:
            symbol = request.data.get("symbol", "0050")
            strategy = request.data.get("strategy", "default_kd")
            custom_params = request.data.get("params", {})

            # 呼叫回測引擎
            result = run_backtest_from_db(
                symbol, strategy_name=strategy, params=custom_params, is_api=True
            )
            return Response(result)
        except Exception as e:
            return Response({"error": f"回測失敗: {str(e)}"}, status=500)


# 【核心修正】強效資料修復 (忽略時區差異)
@method_decorator(csrf_exempt, name="dispatch")
class UpdateStockDataAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        symbol = request.data.get("symbol", "0050")
        if symbol.isdigit() and not symbol.endswith(".TW"):
            symbol = f"{symbol}.TW"
        try:
            print(f"正在重抓 {symbol} ...")
            StockHistory.objects.filter(symbol=symbol).delete()

            ticker = yf.Ticker(symbol)
            # 抓取不還原的資料 (actions=False) 避免 Yahoo 自動還原導致混亂
            df = ticker.history(period="max", auto_adjust=False, actions=False)

            if df.empty:
                return Response({"error": "無法取得歷史資料"}, status=404)

            # 【修復補丁】針對 0050.TW
            if "0050" in symbol:
                print("執行 0050 資料強效修復...")

                # 轉成純日期 (date) 進行比對，避開時區 bug
                dates = df.index.date
                patch_start = pd.Timestamp("2014-01-01").date()
                patch_end = pd.Timestamp("2024-12-02").date()  # 拆股日

                # 找出 2014/1/1 ~ 2024/12/02 之間的資料
                # 邏輯：這段期間 Yahoo 給的是「已經拆股過(除以4)」的價格
                # 但我們為了顯示正確的歷史K線，需要把它「乘回 4 倍」還原成當時的真實價格
                mask = (dates >= patch_start) & (dates < patch_end)

                if mask.any():
                    df.loc[mask, ["Open", "High", "Low", "Close"]] *= 4
                    df.loc[mask, "Volume"] /= 4
                    print(f"已修復 {mask.sum()} 筆資料 (還原為真實 190 元股價)")

            history_list = [
                StockHistory(
                    symbol=symbol,
                    date=index.date(),
                    open=row["Open"],
                    high=row["High"],
                    low=row["Low"],
                    close=row["Close"],
                    volume=row["Volume"],
                )
                for index, row in df.iterrows()
            ]
            StockHistory.objects.bulk_create(history_list)

            return Response(
                {"message": f"{symbol} 資料已修復並更新！", "count": len(history_list)}
            )
        except Exception as e:
            return Response({"error": f"更新失敗: {str(e)}"}, status=500)


# 【新增】策略競技場排行榜 API (讓前端抓取 Top 10 資料)
class PaperTradingLeaderboardAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        # 1. 找出資料庫中「最新」的日期
        latest_date = PaperTrading.objects.aggregate(Max("date"))["date__max"]

        if not latest_date:
            return Response(
                {"error": "目前沒有模擬交易紀錄，請先執行監控程式"}, status=200
            )

        # 2. 撈出該日期的所有策略表現 (即時排行榜)
        rankings = PaperTrading.objects.filter(date=latest_date).order_by("-roi")

        data = []
        for rank in rankings:
            data.append(
                {
                    "strategy": rank.strategy_name,
                    "assets": rank.total_assets,
                    "roi": rank.roi,
                    "action": rank.action,
                    "shares": rank.shares,
                }
            )

        return Response({"date": latest_date, "rankings": data})
