import backtrader as bt


# 策略一：趨勢過濾 KD (只有在長期均線之上才做多)
class TrendKDStrategy(bt.Strategy):
    params = (("ma_period", 200), ("k_period", 9), ("d_period", 3))

    def __init__(self):
        self.kd = bt.indicators.Stochastic(self.data, period=self.params.k_period)
        self.ma = bt.indicators.SimpleMovingAverage(
            self.data, period=self.params.ma_period
        )

    def next(self):
        if not self.position:
            # 價格在均線之上 且 KD 金叉
            if self.data.close[0] > self.ma[0] and self.kd.percK[0] > self.kd.percD[0]:
                self.buy()
        elif self.kd.percK[0] < self.kd.percD[0] or self.data.close[0] < self.ma[0]:
            self.sell()


# 策略二：MACD 趨勢策略
class MACDStrategy(bt.Strategy):
    params = (
        ("m1", 12),
        ("m2", 26),
        ("m3", 9),
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            self.data,
            period_me1=self.params.m1,
            period_me2=self.params.m2,
            period_signal=self.params.m3,
        )

    def next(self):
        if not self.position:
            if self.macd.macd[0] > self.macd.signal[0]:  # 金叉
                self.buy()
        elif self.macd.macd[0] < self.macd.signal[0]:  # 死叉
            self.sell()
