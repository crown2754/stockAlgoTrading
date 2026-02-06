import itertools
import pandas as pd
import yfinance as yf
import backtrader as bt


# 簡易版策略
class QuickMACD(bt.Strategy):
    params = (
        ("m1", 12),
        ("m2", 26),
        ("m3", 9),
    )

    def __init__(self):
        self.macd = bt.indicators.MACD(
            self.data.close,
            period_me1=self.params.m1,
            period_me2=self.params.m2,
            period_signal=self.params.m3,
        )
        self.crossover = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

    def next(self):
        if not self.position:
            if self.crossover > 0:
                self.buy()  # Sizer 會控制買入量
        elif self.crossover < 0:
            self.close()


def optimize_macd(symbol="0050.TW", start="2020-01-01", end="2026-02-06"):
    print(f"正在為 {symbol} 進行參數最佳化搜索 (含風險評估 MDD)...")
    print("這可能需要 30~60 秒，請耐心等待...")

    # 1. 抓取資料
    try:
        df = yf.Ticker(symbol).history(start=start, end=end, auto_adjust=True)
        if df.empty:
            print("❌ 抓不到資料")
            return

        # 資料清洗
        df.index = df.index.tz_localize(None)
        df.columns = [c.lower() for c in df.columns]
        df["openinterest"] = 0
        df = df[df["volume"] > 0]

    except Exception as e:
        print(f"資料抓取錯誤: {e}")
        return

    # 2. 設定參數範圍 (你可以自行微調)
    # 快線 (Fast): 5 到 20 (間隔 3)
    fast_range = range(5, 21, 3)
    # 慢線 (Slow): 20 到 60 (間隔 5)
    slow_range = range(20, 61, 5)
    # 訊號線 (Signal): 固定 9
    signal_val = 9

    results = []

    # 3. 暴力迴圈
    for fast in fast_range:
        for slow in slow_range:
            if fast >= slow:
                continue

            cerebro = bt.Cerebro()
            cerebro.broker.setcash(1000000)
            cerebro.broker.setcommission(commission=0.002)
            cerebro.addsizer(bt.sizers.AllInSizer, percents=95)

            # 【關鍵新增】加入 DrawDown 分析器，計算最大虧損
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")

            data = bt.feeds.PandasData(dataname=df)
            cerebro.adddata(data)

            cerebro.addstrategy(QuickMACD, m1=fast, m2=slow, m3=signal_val)

            # 執行回測並獲取結果
            strats = cerebro.run()
            strat = strats[0]

            final_val = cerebro.broker.getvalue()

            # 從分析器提取 MDD (Max Drawdown)
            # 這代表資產從最高點滑落的最大幅度
            mdd = strat.analyzers.drawdown.get_analysis()["max"]["drawdown"]

            profit = final_val - 1000000
            roi = (profit / 1000000) * 100

            results.append(
                {
                    "params": f"({fast}, {slow}, {signal_val})",
                    "roi": round(roi, 2),
                    "final_value": int(final_val),
                    "mdd": round(mdd, 2),  # 保存 MDD
                }
            )

    # 4. 排序並顯示結果
    # 這裡我們依然用 ROI 排序，但你可以觀察 MDD 欄位
    sorted_results = sorted(results, key=lambda x: x["roi"], reverse=True)

    print("\n========== 🏆 0050 最佳參數排行榜 (含最大虧損MDD) ==========")
    print(f"回測區間: {start} ~ {end}")
    print("-" * 80)
    print(
        f"{'排名':<5} {'MACD參數':<15} {'總報酬率':<12} {'最大虧損(MDD)':<15} {'最終資產'}"
    )
    print("-" * 80)

    for i, res in enumerate(sorted_results[:15]):  # 顯示前 15 名
        # 如果 MDD 超過 30%，用驚嘆號標示風險
        risk_mark = "⚠️" if res["mdd"] > 30 else "  "
        print(
            f"#{i+1:<4} {res['params']:<15} {res['roi']}%        {res['mdd']}% {risk_mark}        ${res['final_value']:,}"
        )


if __name__ == "__main__":
    optimize_macd()
