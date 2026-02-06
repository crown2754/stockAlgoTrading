# utils/paper_trader.py
import json
import os
from datetime import datetime

# 設定檔案儲存位置
DATA_FILE = "paper_wallets.json"

# 設定初始口袋 (名稱: 本金)
INITIAL_POCKETS = {
    "微型戶 (1K)": 1000,
    "小資戶 (1W)": 10000,
    "標準戶 (10W)": 100000,
    "進階戶 (50W)": 500000,
    "大戶 (100W)": 1000000,
}


class PaperTrader:
    def __init__(self):
        self.wallets = self._load_data()

    def _load_data(self):
        """讀取或初始化帳本"""
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass  # 讀取失敗則重置

        # 初始化錢包結構
        wallets = {}
        for name, capital in INITIAL_POCKETS.items():
            wallets[name] = {
                "init_capital": capital,  # 初始本金
                "cash": capital,  # 目前現金
                "shares": 0,  # 持有股數
                "total_assets": capital,  # 總資產 (現金+股票)
                "roi": 0.0,  # 報酬率
                "history": [],  # 每日淨值紀錄
            }
        return wallets

    def _save_data(self):
        """儲存帳本"""
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.wallets, f, ensure_ascii=False, indent=4)

    def execute(self, date_str, price, signal_type):
        """
        執行模擬交易與結算
        signal_type: 'BUY', 'SELL', 'HOLD' (無訊號)
        """
        report_lines = []

        for name, wallet in self.wallets.items():
            cash = wallet["cash"]
            shares = wallet["shares"]

            # --- 買進邏輯 ---
            if signal_type == "BUY" and cash > price:
                # 計算最多能買幾股 (預留 0.5% 當手續費緩衝)
                max_shares = int((cash / price) * 0.995)

                if max_shares > 0:
                    cost = max_shares * price
                    # 手續費 (0.1425%, 最低 1 元)
                    fee = max(1, int(cost * 0.001425))

                    if cash >= (cost + fee):
                        wallet["cash"] -= cost + fee
                        wallet["shares"] += max_shares
                        action_msg = f"買進 {max_shares} 股"
                    else:
                        action_msg = "資金不足"
                else:
                    action_msg = "買不起 1 股"

            # --- 賣出邏輯 ---
            elif signal_type == "SELL" and shares > 0:
                revenue = shares * price
                # 手續費 (0.1425%, 最低 1 元)
                fee = max(1, int(revenue * 0.001425))
                # 證交稅 (0.1% ETF)
                tax = int(revenue * 0.001)

                wallet["cash"] += revenue - fee - tax
                wallet["shares"] = 0
                action_msg = f"賣出 {shares} 股"

            # --- 無動作 ---
            else:
                action_msg = "續抱" if shares > 0 else "空手"

            # --- 每日結算 ---
            # 更新總資產市值
            market_value = wallet["shares"] * price
            wallet["total_assets"] = wallet["cash"] + market_value

            # 計算報酬率
            roi = (
                (wallet["total_assets"] - wallet["init_capital"])
                / wallet["init_capital"]
            ) * 100
            wallet["roi"] = round(roi, 2)

            # 寫入歷史紀錄 (只留最近 5 筆避免檔案爆炸，或可全留)
            record = {
                "date": date_str,
                "price": price,
                "assets": int(wallet["total_assets"]),
                "action": action_msg,
            }
            wallet["history"].append(record)

            # 準備報表文字
            symbol = "🔺" if roi > 0 else "🔻" if roi < 0 else "▫️"
            report_lines.append(
                f"{name}: ${int(wallet['total_assets']):,} ({symbol}{roi}%) | {action_msg}"
            )

        self._save_data()
        return "\n".join(report_lines)


# 測試用
if __name__ == "__main__":
    trader = PaperTrader()
    print(trader.execute("2026-02-06", 71.9, "HOLD"))
