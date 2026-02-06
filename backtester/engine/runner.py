import backtrader as bt
import pandas as pd
import yfinance as yf
import numpy as np
from backtester.models import StockHistory
from backtester.strategies.kd_strategy import Taiwan50KDStrategy
from backtester.strategies.optimized_strategies import TrendKDStrategy, MACDStrategy
import traceback

STRATEGY_MAP = {
    "default_kd": Taiwan50KDStrategy,
    "trend_kd": TrendKDStrategy,
    "macd": MACDStrategy,
}


def run_backtest_from_db(symbol, strategy_name="default_kd", params=None, is_api=False):
    if symbol.isdigit() and not symbol.endswith(".TW"):
        symbol = f"{symbol}.TW"

    p = params if params else {}

    # 1. 準備「給人看」的圖表數據 (Raw Data)
    queryset = StockHistory.objects.filter(symbol=symbol)
    start_date = p.get("start_date")
    end_date = p.get("end_date")

    if start_date:
        queryset = queryset.filter(date__gte=start_date)
    if end_date:
        queryset = queryset.filter(date__lte=end_date)

    data_list = list(queryset.values("date", "open", "high", "low", "close", "volume"))
    if not data_list:
        return {"error": "無數據，請先點擊「更新/重抓資料」"} if is_api else 0.0

    df_raw = pd.DataFrame(data_list)
    df_raw["date"] = pd.to_datetime(df_raw["date"])
    df_raw.set_index("date", inplace=True)
    df_raw.sort_index(inplace=True)
    df_raw = df_raw[~df_raw.index.duplicated(keep="last")]

    chart_prices = [round(float(c), 2) for c in df_raw["close"].tolist()]
    chart_dates = [d.strftime("%Y-%m-%d") for d in df_raw.index]

    # 2. 準備「給電腦算」的回測數據 (Adjusted Data)
    try:
        ticker = yf.Ticker(symbol)
        df_adj = ticker.history(start=start_date, end=end_date, auto_adjust=True)

        if df_adj.empty:
            raise ValueError("Yahoo 回傳空資料")

        # 防呆: 資料長度
        if len(df_adj) < 50:
            return (
                {
                    "error": f"資料過短 ({len(df_adj)}天)，無法計算指標 (MACD需要至少35天)"
                }
                if is_api
                else 0.0
            )

        # 清洗與防爆
        df_adj.index = df_adj.index.tz_localize(None)
        df_adj = df_adj[~df_adj.index.duplicated(keep="last")]
        df_adj.sort_index(inplace=True)
        df_adj.columns = [c.lower() for c in df_adj.columns]

        target_cols = ["open", "high", "low", "close", "volume"]
        for col in target_cols:
            if col not in df_adj.columns:
                df_adj[col] = 0.0
        df_adj = df_adj[target_cols].copy()

        df_adj["openinterest"] = 0
        df_adj = df_adj.fillna(method="ffill").fillna(method="bfill").dropna()
        df_adj = df_adj.astype(float)

        # 修復 2014 斷層 (Yahoo Bug)
        patch_date = pd.Timestamp("2014-01-02")
        if patch_date in df_adj.index:
            idx = df_adj.index.get_loc(patch_date)
            # 確保 idx 是整數且大於0
            if isinstance(idx, int) and idx > 0:
                if df_adj.iloc[idx - 1]["close"] > df_adj.iloc[idx]["close"] * 3:
                    mask = df_adj.index < patch_date
                    df_adj.loc[mask, ["open", "high", "low", "close"]] /= 4
                    df_adj.loc[mask, "volume"] *= 4
            # 如果 idx 是 slice 或 array (極少見)，則忽略不處理以避免報錯

        df_calc = df_adj

    except Exception as e:
        print(f"Fallback: {e}")
        # 如果 Yahoo 還原資料抓失敗，退回到使用 raw data，但可能會失真
        df_calc = df_raw.copy()
        df_calc["openinterest"] = 0
        if len(df_calc) < 35:
            return {"error": "資料不足"} if is_api else 0.0

    # 3. 執行回測
    cerebro = bt.Cerebro()
    init_cash = float(p.get("init_cash", 1000000.0))
    cerebro.broker.setcash(init_cash)
    cerebro.addsizer(bt.sizers.AllInSizer, percents=95)
    
    # 設定 0.2% 手續費 (含證交稅緩衝)
    cerebro.broker.setcommission(commission=0.002)
    
    cerebro.addobserver(bt.observers.Value)

    # 【新增】加入交易紀錄分析器
    cerebro.addanalyzer(bt.analyzers.Transactions, _name="tx")

    data_feed = bt.feeds.PandasData(dataname=df_calc)
    cerebro.adddata(data_feed)

    strat_class = STRATEGY_MAP.get(strategy_name, Taiwan50KDStrategy)
    valid_keys = strat_class.params._getkeys()
    strat_params = {
        k: int(v) for k, v in p.items() if k in valid_keys and str(v).isdigit()
    }
    cerebro.addstrategy(strat_class, **strat_params)

    try:
        strat_runs = cerebro.run()
        final_value = cerebro.broker.getvalue()

        if is_api:
            main_strat = strat_runs[0]
            equity_values = [
                round(v, 2)
                for v in main_strat.observers.value.get(ago=0, size=len(main_strat))
            ]

            # --- 處理交易紀錄 (Trade Log) ---
            txs = main_strat.analyzers.tx.get_analysis()
            trade_log = []

            for dt, tx_list in txs.items():
                # 這裡的 dt 是 datetime 物件
                ts = pd.Timestamp(dt)

                # 為了讓使用者不困惑，我們去 df_raw 找當天「原本的股價」顯示
                display_price = 0
                if ts in df_raw.index:
                    display_price = round(df_raw.loc[ts]["open"], 2)  # 假設開盤買進
                else:
                    # 萬一對不到日期，只好顯示計算用的還原價
                    display_price = round(tx_list[0][1], 2)

                for tx in tx_list:
                    amount = tx[0]  # 正數買入，負數賣出
                    price = tx[1]  # 這是引擎用的還原價

                    trade_log.append(
                        {
                            "date": ts.strftime("%Y-%m-%d"),
                            "action": "買入" if amount > 0 else "賣出",
                            "size": int(abs(amount)),
                            "price": display_price,  # 顯示給人看的價格
                            "cost": int(abs(amount) * price),  # 實際成本(用還原價算)
                        }
                    )

            # 按日期排序
            trade_log.sort(key=lambda x: x["date"])

            roi = ((final_value - init_cash) / init_cash) * 100

            return {
                "symbol": symbol,
                "start_date": start_date if start_date else chart_dates[0],
                "end_date": end_date if end_date else chart_dates[-1],
                "final_value": round(final_value, 2),
                "total_return_pct": round(roi, 2),
                "trade_log": trade_log,
                "chart_data": {
                    "dates": chart_dates,
                    "values": (
                        equity_values[-len(chart_dates) :]
                        if len(equity_values) > len(chart_dates)
                        else equity_values
                    ),
                    "prices": chart_prices,
                },
            }
        return final_value
    except Exception as e:
        traceback.print_exc()
        return {"error": f"回測失敗: {str(e)}"} if is_api else 0.0