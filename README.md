# 0050 Algo Trading Platform

這是一個基於 **Django** 與 **Backtrader** 開發的量化交易回測平台。目前專案處於開發初期，專注於建置可擴展的系統架構，並實作台灣股市（以 0050 為主）的技術指標策略。

## 🚀 核心架構

- **Framework:** [Django 5.x](https://www.djangoproject.com/)
- **Backtesting Engine:** [Backtrader](https://www.backtrader.com/)
- **Data Source:** [yfinance](https://github.com/ranaroussi/yfinance) (Yahoo Finance API)

## 🛠️ 開發環境配置

專案已進行客製化配置，預設使用 **9999** 埠進行開發：

1. **安裝依賴項目**

   ```bash
   pip install -r requirements.txt
   ```

2. **資料庫遷移**

   ```bash
   python manage.py migrate
   ```

3. **啟動開發伺服器**
   ```bash
   python manage.py dev
   ```

## 📈 目前開發進度

- [x] Django 專案腳手架建立
- [x] Backtrader 框架整合
- [x] 自定義 Management Command (`dev`) 實作，固定 Port 9999
- [x] 模組化 KD 策略類別定義 (`Taiwan50KDStrategy`)

## 🏗️ 專案結構

- `backtester/engine/`: 核心回測引擎封裝
- `backtester/strategies/`: 交易策略集（如：KD, RSI, MA）
- `backtester/management/commands/`: 自定義 Django 指令集

---

_本專案僅供學術研究與程式開發練習，不構成任何投資建議。_
