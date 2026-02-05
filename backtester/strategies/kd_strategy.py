import backtrader as bt

class Taiwan50KDStrategy(bt.Strategy):
    params = (
        ('k_period', 9),
        ('d_period', 3),
        ('buy_threshold', 20),
        ('sell_threshold', 80),
    )

    def __init__(self):
        # 使用參數化的方式，方便以後做參數優化 (Optimization)
        self.stoch = bt.indicators.Stochastic(
            self.data,
            period=self.params.k_period,
            period_dfast=self.params.d_period,
            period_dslow=self.params.d_period
        )

    def next(self):
        if not self.position:
            if self.stoch.percK < self.params.buy_threshold:
                self.buy()
        elif self.stoch.percK > self.params.sell_threshold:
            self.sell()