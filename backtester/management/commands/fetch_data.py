import yfinance as yf
from django.core.management.base import BaseCommand
from backtester.models import StockHistory


class Command(BaseCommand):
    help = "抓取指定股票過去十年的歷史數據"

    def add_arguments(self, parser):
        parser.add_argument("symbol", type=str)

    def handle(self, *args, **options):
        symbol = options["symbol"]
        if symbol.isdigit():
            symbol = f"{symbol}.TW"

        self.stdout.write(f"正在從 Yahoo Finance 抓取 {symbol} 十年數據...")
        ticker = yf.Ticker(symbol)
        df = ticker.history(period="10y")  # 抓取 10 年

        records = []
        for date, row in df.iterrows():
            records.append(
                StockHistory(
                    symbol=symbol,
                    date=date.date(),
                    open=row["Open"],
                    high=row["High"],
                    low=row["Low"],
                    close=row["Close"],
                    volume=row["Volume"],
                )
            )

        # 使用批量建立提高寫入效率
        StockHistory.objects.bulk_create(records, ignore_conflicts=True)
        self.stdout.write(self.style.SUCCESS(f"成功儲存 {len(records)} 筆紀錄"))
