import os
import django
import pandas as pd
import yfinance as yf
import datetime
from utils.emailer import send_signal_email

# ==========================================
# 1. 設定 Django 環境 (讓腳本能存取資料庫)
# ==========================================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quant_platform.settings') # 請確認你的專案名稱
django.setup()

from backtester.models import PaperTrading

# ==========================================
# 2. 設定參數與標的
# ==========================================
SYMBOL = "0050.TW"
INIT_CAPITAL = 1000000 # 統一用 100 萬起跑

# 你的 Top 10 參數 (快, 慢, 訊號) - 來自之前的暴力搜索結果
TOP_STRATEGIES = [
    (11, 45, 9), (5, 35, 9), (14, 45, 9), (14, 40, 9), (8, 25, 9),
    (5, 45, 9), (8, 40, 9), (11, 40, 9), (20, 45, 9), (17, 35, 9)
]

def calculate_macd(df, fast, slow, signal):
    """計算 MACD 指標"""
    ema_fast = df['Close'].ewm(span=fast, adjust=False).mean()
    ema_slow = df['Close'].ewm(span=slow, adjust=False).mean()
    dif = ema_fast - ema_slow
    macd_signal = dif.ewm(span=signal, adjust=False).mean()
    return dif, macd_signal

def run_simulation():
    print(f"🚀 啟動 Top 10 策略競技場監控 ({datetime.date.today()})...")
    
    # 1. 抓取資料 (一次抓完給所有策略用)
    try:
        ticker = yf.Ticker(SYMBOL)
        # 用來算指標 (還原價)
        df_adj = ticker.history(period="100d", auto_adjust=True)
        # 用來記帳 (原始價)
        df_raw = ticker.history(period="1d", auto_adjust=False)
        
        if df_adj.empty: 
            print("❌ 抓不到資料"); return

        today_price = round(df_raw['Close'].iloc[-1], 2)
        today_date = df_adj.index[-1].date()
        print(f"📅 資料日期: {today_date} | 收盤價: {today_price}")

    except Exception as e:
        print(f"❌ 資料錯誤: {e}"); return

    # 2. 迴圈執行 10 個策略
    report_list = []
    
    for (fast, slow, sig) in TOP_STRATEGIES:
        strat_name = f"MACD({fast},{slow},{sig})"
        
        # --- A. 讀取或是初始化帳戶 ---
        # 嘗試找這個策略「上一筆」的交易紀錄
        last_record = PaperTrading.objects.filter(strategy_name=strat_name).order_by('-date').first()
        
        if last_record:
            current_cash = last_record.cash
            current_shares = last_record.shares
        else:
            # 第一次跑，初始化
            current_cash = INIT_CAPITAL
            current_shares = 0
            
        # --- B. 計算指標 ---
        dif, macd = calculate_macd(df_adj, fast, slow, sig)
        curr_dif = dif.iloc[-1]
        curr_macd = macd.iloc[-1]
        prev_dif = dif.iloc[-2]
        prev_macd = macd.iloc[-2]
        
        # --- C. 判斷訊號 & 模擬交易 ---
        action = "HOLD"
        
        # 黃金交叉 (買進)
        if prev_dif < prev_macd and curr_dif > curr_macd:
            if current_cash > today_price:
                # 梭哈模式 (預留 0.5% 手續費空間)
                buy_shares = int((current_cash / today_price) * 0.995)
                
                if buy_shares > 0:
                    cost = buy_shares * today_price
                    # 手續費低消 20 元 (概算)
                    fee = max(20, int(cost * 0.001425))
                    
                    if current_cash >= (cost + fee):
                        current_shares += buy_shares
                        current_cash -= (cost + fee)
                        action = "BUY"
        
        # 死亡交叉 (賣出)
        elif prev_dif > prev_macd and curr_dif < curr_macd:
            if current_shares > 0:
                revenue = current_shares * today_price
                fee = max(20, int(revenue * 0.001425))
                tax = int(revenue * 0.001)
                
                current_cash += (revenue - fee - tax)
                current_shares = 0
                action = "SELL"

        # --- D. 結算與存檔 ---
        total_assets = current_cash + (current_shares * today_price)
        roi = round(((total_assets - INIT_CAPITAL) / INIT_CAPITAL) * 100, 2)
        
        # 存入資料庫 (update_or_create 避免重複跑導致重複新增)
        PaperTrading.objects.update_or_create(
            strategy_name=strat_name,
            date=today_date,
            defaults={
                'price': today_price,
                'action': action,
                'shares': current_shares,
                'cash': current_cash,
                'total_assets': total_assets,
                'roi': roi
            }
        )
        
        # 加入報表列表 (用來寄信)
        icon = "🔴" if action == "BUY" else "🟢" if action == "SELL" else "⚪"
        if action == "HOLD" and current_shares > 0: icon = "🔵" # 持倉中
        
        report_list.append({
            "name": strat_name,
            "roi": roi,
            "action": f"{icon} {action}",
            "assets": total_assets
        })

    # 3. 整理報表並寄信
    # 按 ROI 排序
    report_list.sort(key=lambda x: x['roi'], reverse=True)
    
    email_body = f"📅 日期: {today_date} | 現價: {today_price}\n\n🏆 Top 10 策略績效排行榜\n" + "-"*35 + "\n"
    for rank, item in enumerate(report_list):
        email_body += f"#{rank+1} {item['name']}: {item['roi']}% | {item['action']}\n"
    
    email_body += "-"*35 + "\n🔴買進 🟢賣出 🔵續抱 ⚪空手"
    
    print(email_body)
    
    # 寄出信件
    try:
        send_signal_email(f"🔥 {SYMBOL} 策略競技場日報", email_body)
        print("✅ 監控完成，資料已寫入 DB，信件已發送")
    except Exception as e:
        print(f"⚠️ 資料已寫入 DB，但寄信失敗: {e}")

if __name__ == '__main__':
    run_simulation()