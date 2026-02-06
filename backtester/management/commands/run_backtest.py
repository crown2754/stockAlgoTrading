from django.core.management.base import BaseCommand
from backtester.engine.runner import run_backtest_from_db


class Command(BaseCommand):
    help = "執行回測並選擇策略"

    def add_arguments(self, parser):
        parser.add_argument("symbol", type=str)
        parser.add_argument(
            "--strategy",
            type=str,
            default="default_kd",
            help="可選: default_kd, trend_kd, macd",
        )

    def handle(self, *args, **options):
        symbol = options["symbol"]
        strat = options["strategy"]

        if symbol.isdigit() and not symbol.endswith(".TW"):
            symbol = f"{symbol}.TW"
            
        self.stdout.write(f"正在以 {strat} 策略執行 {symbol} 回測...")
        final_value = run_backtest_from_db(symbol, strategy_name=strat)

        if final_value == 0:
            self.stdout.write(
                self.style.ERROR(f"回測失敗，請確認資料庫是否有 {symbol} 的數據")
            )
        else:
            # 現在可以安全地使用 :.2f 了
            self.stdout.write(self.style.SUCCESS(f"最終資產: {final_value:.2f}"))
