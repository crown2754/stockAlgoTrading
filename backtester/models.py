from django.db import models
from django.contrib.auth.models import User


class BacktestStrategy(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    k_period = models.IntegerField(default=9)
    buy_threshold = models.IntegerField(default=20)
    sell_threshold = models.IntegerField(default=80)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class StockHistory(models.Model):
    symbol = models.CharField(max_length=10, db_index=True)  # 股票代號
    date = models.DateField()  # 日期
    open = models.FloatField()  # 開盤價
    high = models.FloatField()  # 最高價
    low = models.FloatField()  # 最低價
    close = models.FloatField()  # 收盤價
    volume = models.BigIntegerField()  # 成交量

    class Meta:
        unique_together = ("symbol", "date")  # 避免同一支股票在同一天重複儲存
        ordering = ["date"]

class PaperTrading(models.Model):
    strategy_name = models.CharField(max_length=50) # 例如: "MACD(11,45,9)"
    date = models.DateField()
    price = models.FloatField()           # 當日收盤價
    action = models.CharField(max_length=10) # BUY, SELL, HOLD, NONE
    shares = models.IntegerField(default=0)  # 持有股數
    cash = models.FloatField()            # 剩餘現金
    total_assets = models.FloatField()    # 總資產
    roi = models.FloatField()             # 報酬率 (%)

    class Meta:
        ordering = ['-date', '-roi'] # 預設按日期新到舊，報酬率高到低排序
        unique_together = ('strategy_name', 'date') # 確保同一策略同一天只有一筆紀錄

    def __str__(self):
        return f"{self.date} - {self.strategy_name}: {self.roi}%"