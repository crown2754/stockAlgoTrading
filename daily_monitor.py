# daily_monitor.py
import yfinance as yf
import pandas as pd
import datetime
import schedule
from utils.emailer import send_signal_email  # 匯入剛剛寫的寄信功能

# 設定你的「冠軍參數」
FAST_EMA = 14
SLOW_EMA = 40
SIGNAL_EMA = 9
SYMBOL = "0050.TW"

def calculate_macd(df):
    """手動計算 MACD (不依賴 TA-Lib，純 Pandas 實作)"""
    # 1. 計算快線與慢線 (EMA)
    ema_fast = df['Close'].ewm(span=FAST_EMA, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=SLOW_EMA, adjust=False).mean()
    
    # 2. 計算 DIF (快 - 慢)
    df['dif'] = ema_fast - ema_slow
    
    # 3. 計算 MACD 訊號線 (DIF 的 EMA)
    df['macd_signal'] = df['dif'].ewm(span=SIGNAL_EMA, adjust=False).mean()
    
    # 4. 計算柱狀圖 (OSC)
    df['osc'] = df['dif'] - df['macd_signal']
    return df

def run_daily_scan():
    print(f"🕵️‍♂️ 正在掃描 {SYMBOL} 的最新訊號...")
    
    # 1. 抓取資料 (抓最近 100 天就夠算指標了)
    # auto_adjust=True 很重要，我們要用「還原股價」算指標才準
    df = yf.Ticker(SYMBOL).history(period="100d", auto_adjust=True)
    
    if df.empty:
        print("❌ 抓不到資料，請檢查網路")
        return

    # 2. 計算指標
    df = calculate_macd(df)
    
    # 3. 取得最後兩天的資料來比對交叉
    # today = 今天收盤 (或最新盤中)
    # yesterday = 昨天收盤
    today = df.iloc[-1]
    yesterday = df.iloc[-2]
    
    curr_price = round(today['Close'], 2)
    date_str = df.index[-1].strftime('%Y-%m-%d')

    print(f"📅 日期: {date_str} | 收盤價: {curr_price}")
    print(f"📊 今日 DIF: {today['dif']:.2f} | 訊號線: {today['macd_signal']:.2f}")
    print(f"📊 昨日 DIF: {yesterday['dif']:.2f} | 訊號線: {yesterday['macd_signal']:.2f}")

    # 4. 判斷訊號 (黃金交叉 / 死亡交叉)
    signal_type = None
    
    # 黃金交叉：昨天 DIF < 訊號線，且 今天 DIF > 訊號線
    if yesterday['dif'] < yesterday['macd_signal'] and today['dif'] > today['macd_signal']:
        signal_type = "BUY"
    
    # 死亡交叉：昨天 DIF > 訊號線，且 今天 DIF < 訊號線
    elif yesterday['dif'] > yesterday['macd_signal'] and today['dif'] < today['macd_signal']:
        signal_type = "SELL"

    # 5. 發送通知
    if signal_type == "BUY":
        subject = f"🚀【買進訊號】{SYMBOL} 出現黃金交叉！"
        content = (
            f"監控標的: {SYMBOL}\n"
            f"日期: {date_str}\n"
            f"收盤價: {curr_price}\n\n"
            f"📈 技術指標 (MACD {FAST_EMA}-{SLOW_EMA}-{SIGNAL_EMA}):\n"
            f"DIF 向上突破訊號線，確認轉強！\n"
            f"建議動作: 分批佈局或買入。"
        )
        send_signal_email(subject, content)
        
    elif signal_type == "SELL":
        subject = f"📉【賣出訊號】{SYMBOL} 出現死亡交叉！"
        content = (
            f"監控標的: {SYMBOL}\n"
            f"日期: {date_str}\n"
            f"收盤價: {curr_price}\n\n"
            f"📉 技術指標 (MACD {FAST_EMA}-{SLOW_EMA}-{SIGNAL_EMA}):\n"
            f"DIF 向下跌破訊號線，趨勢轉弱！\n"
            f"建議動作: 獲利了結或停損觀望。"
        )
        send_signal_email(subject, content)
    else:
        print("😴 今日無特殊訊號，趨勢延續中...")

if __name__ == "__main__":
    print("機器人啟動中... 每天 13:40 自動掃描")
    
    # 設定每天下午 1:40 執行
    # schedule.every().day.at("13:40").do(run_daily_scan)
    schedule.every().day.at("13:40").do(run_daily_scan)
    
    while True:
        schedule.run_pending()
        time.sleep(60) # 每分鐘檢查一次時間