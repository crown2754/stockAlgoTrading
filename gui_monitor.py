import tkinter as tk
from tkinter import scrolledtext
import threading
import time
import schedule
import yfinance as yf
import pandas as pd
from datetime import datetime

# 匯入工具
from utils.emailer import send_signal_email
from utils.paper_trader import PaperTrader

# 匯入 Top 10 監控邏輯 (請確保 monitor_top10.py 在同一層目錄)
import monitor_top10 

# ================= 設定區 =================
SYMBOL = "0050.TW"
FAST_EMA = 14
SLOW_EMA = 40
SIGNAL_EMA = 9
# ==========================================

class StockMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("0050 量化戰情室 (個人口袋 + 策略競技場)")
        self.root.geometry("700x550") # 加大視窗
        
        self.is_running = False
        self.monitor_thread = None

        # --- 介面佈局 ---
        # 1. 標題
        tk.Label(root, text=f"戰情監控中心：{SYMBOL}", font=("Microsoft JhengHei", 14, "bold")).pack(pady=10)

        # 2. 記錄顯示區
        self.log_area = scrolledtext.ScrolledText(root, width=80, height=20, state='disabled', font=("Consolas", 9))
        self.log_area.pack(padx=10, pady=5)

        # 3. 按鈕區 (分兩排)
        
        # 第一排：個人監控
        frame_personal = tk.LabelFrame(root, text="個人口袋監控 (MACD 14,40,9)", padx=5, pady=5)
        frame_personal.pack(pady=5, fill="x", padx=10)
        
        self.btn_scan_now = tk.Button(frame_personal, text="🔍 立即掃描個人帳戶", command=self.run_personal_scan, bg="#17a2b8", fg="white")
        self.btn_scan_now.pack(side=tk.LEFT, padx=5)

        self.btn_start = tk.Button(frame_personal, text="▶ 啟動每日排程 (13:40)", command=self.start_schedule, bg="#28a745", fg="white")
        self.btn_start.pack(side=tk.LEFT, padx=5)

        self.btn_stop = tk.Button(frame_personal, text="⏹ 停止排程", command=self.stop_schedule, bg="#dc3545", fg="white", state='disabled')
        self.btn_stop.pack(side=tk.LEFT, padx=5)

        # 第二排：競技場
        frame_arena = tk.LabelFrame(root, text="策略競技場 (Top 10 排行榜)", padx=5, pady=5)
        frame_arena.pack(pady=5, fill="x", padx=10)

        self.btn_run_top10 = tk.Button(frame_arena, text="🏆 執行 Top 10 競技場更新 (寫入資料庫)", command=self.run_top10_scan, bg="#6610f2", fg="white")
        self.btn_run_top10.pack(side=tk.LEFT, padx=5, fill="x", expand=True)

        # 4. 狀態列
        self.lbl_status = tk.Label(root, text="狀態：待機中", bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.lbl_status.pack(side=tk.BOTTOM, fill=tk.X)

        self.log("系統就緒。請選擇操作...")
        
        self.start_schedule()

    def log(self, msg):
        timestamp = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{timestamp}] {msg}\n"
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, full_msg)
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
        print(full_msg.strip())

    # ==================== 功能邏輯 ====================

    def calculate_macd(self, df):
        ema_fast = df['Close'].ewm(span=FAST_EMA, adjust=False).mean()
        ema_slow = df['Close'].ewm(span=SLOW_EMA, adjust=False).mean()
        df['dif'] = ema_fast - ema_slow
        df['macd_signal'] = df['dif'].ewm(span=SIGNAL_EMA, adjust=False).mean()
        return df

    def scan_logic(self):
        """個人口袋掃描邏輯"""
        self.log(f"開始執行個人口袋掃描...")
        try:
            ticker = yf.Ticker(SYMBOL)
            df_adj = ticker.history(period="100d", auto_adjust=True)
            df_raw = ticker.history(period="1d", auto_adjust=False)

            if df_adj.empty or df_raw.empty:
                self.log("❌ 錯誤：抓不到資料")
                return

            df_adj = self.calculate_macd(df_adj)
            today = df_adj.iloc[-1]
            yesterday = df_adj.iloc[-2]
            
            real_price = round(df_raw['Close'].iloc[-1], 2) 
            date_str = df_adj.index[-1].strftime('%Y-%m-%d')

            self.log(f"日期: {date_str} | 現價: {real_price}")
            
            signal_type = "HOLD"
            signal_msg = "無特殊訊號"
            
            if yesterday['dif'] < yesterday['macd_signal'] and today['dif'] > today['macd_signal']:
                signal_type = "BUY"
                signal_msg = "🚀 黃金交叉 (買進)"
            elif yesterday['dif'] > yesterday['macd_signal'] and today['dif'] < today['macd_signal']:
                signal_type = "SELL"
                signal_msg = "📉 死亡交叉 (賣出)"

            # 執行記帳
            trader = PaperTrader()
            wallet_report = trader.execute(date_str, real_price, signal_type)
            
            self.log(f"訊號: {signal_type} | 記帳完成")

            # 寄信
            subject = f"✅ {SYMBOL} 個人監控與帳務回報"
            if signal_type != "HOLD":
                subject = f"【{signal_type}】{SYMBOL} 訊號觸發！"

            content = (
                f"📅 日期: {date_str}\n"
                f"💰 收盤: {real_price}\n"
                f"📊 指標: DIF {today['dif']:.2f} | MACD {today['macd_signal']:.2f}\n"
                f"📢 訊號: {signal_msg}\n"
                f"--------------------------------\n"
                f"💼【五個口袋模擬績效】\n"
                f"{wallet_report}\n"
                f"--------------------------------\n"
                f"個人監控機器人報告完畢。"
            )
            send_signal_email(subject, content)
            self.log(f"📧 個人報表已發送")

        except Exception as e:
            self.log(f"❌ 錯誤: {e}")

    # ==================== 按鈕事件 ====================

    def run_personal_scan(self):
        self.btn_scan_now.config(state='disabled')
        threading.Thread(target=self._run_personal_thread).start()

    def _run_personal_thread(self):
        self.scan_logic()
        self.btn_scan_now.config(state='normal')

    def run_top10_scan(self):
        """執行 Top 10 競技場更新"""
        self.btn_run_top10.config(state='disabled')
        threading.Thread(target=self._run_top10_thread).start()

    def _run_top10_thread(self):
        self.log("🏆 正在啟動 Top 10 策略競技場更新...")
        self.log("這會寫入資料庫並更新網頁排行榜，請稍候...")
        try:
            # 呼叫 monitor_top10.py 裡面的函式
            monitor_top10.run_simulation()
            self.log("✅ Top 10 更新完成！請查看網頁或信箱。")
        except Exception as e:
            self.log(f"❌ Top 10 更新失敗: {e}")
        finally:
            self.btn_run_top10.config(state='normal')

    # ==================== 排程邏輯 ====================

    def start_schedule(self):
        if self.is_running: return
        self.is_running = True
        self.btn_start.config(state='disabled')
        self.btn_stop.config(state='normal')
        self.lbl_status.config(text="狀態：排程監控中 (每天 13:40 執行)", fg="green")
        
        schedule.clear()
        # 每天下午 1:40 同時跑兩件事：個人掃描 & Top 10 更新
        schedule.every().day.at("13:40").do(self.scan_logic)
        schedule.every().day.at("13:41").do(self.run_top10_scan) # 晚一分鐘跑 Top 10
        
        self.log("排程已啟動，等待下午 1:40 觸發...")
        self.monitor_thread = threading.Thread(target=self._schedule_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def stop_schedule(self):
        self.is_running = False
        self.btn_start.config(state='normal')
        self.btn_stop.config(state='disabled')
        self.lbl_status.config(text="狀態：已停止", fg="red")
        self.log("排程已停止")

    def _schedule_loop(self):
        while self.is_running:
            schedule.run_pending()
            time.sleep(1)

if __name__ == "__main__":
    root = tk.Tk()
    app = StockMonitorApp(root)
    root.mainloop()