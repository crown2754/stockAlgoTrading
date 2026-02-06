import yfinance as yf
import pandas as pd

# 設定顯示所有行與列，避免被省略
pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)


def investigate_0050_source():
    print("========== 正在連線 Yahoo Finance 偵測原始數據 ==========")
    symbol = "0050.TW"

    # 我們針對這兩個關鍵的時間點進行查核
    # 1. 2013-2014 (你說的雪崩點)
    # 2. 2024-12 (最近的真實拆股點)

    # 測試 A: 強制抓取「不調整」的資料 (auto_adjust=False)
    # 理論上：2013年應該要看到 50-60 元，2024/12 應該要看到 190 -> 48
    print("\n【測試 A】抓取 auto_adjust=False (應為原始股價)")
    try:
        ticker = yf.Ticker(symbol)
        # 這裡特別加上 actions=True 看看有沒有 dividend/split 資訊
        df_raw = ticker.history(
            start="2013-11-20", end="2014-01-10", auto_adjust=False, actions=True
        )

        if df_raw.empty:
            print("❌ 抓不到資料！")
        else:
            print(df_raw[["Close", "Volume", "Dividends", "Stock Splits"]])

            # 簡單判斷
            first_price = df_raw.iloc[0]["Close"]
            if first_price < 20:
                print("\n⚠️ 警告：就算設了 auto_adjust=False，Yahoo 還是回傳了 14 元！")
                print(
                    "   這代表 Yahoo 的 API 源頭已經被汙染/調整過了，我們必須換個方法抓。"
                )
            else:
                print(f"\n✅ 正常：抓到的價格是 {first_price} 元 (符合當時歷史行情)。")

    except Exception as e:
        print(f"發生錯誤: {e}")

    # 測試 B: 檢查 2024 年拆股當下的狀況
    print("\n\n【測試 B】檢查 2024/12 拆股當週 (auto_adjust=False)")
    try:
        df_split = ticker.history(
            start="2024-11-25", end="2024-12-10", auto_adjust=False, actions=True
        )
        print(df_split[["Close", "Stock Splits"]])
    except Exception as e:
        print(f"發生錯誤: {e}")


if __name__ == "__main__":
    investigate_0050_source()
