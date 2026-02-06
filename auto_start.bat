@echo off
:: 切換到你的專案資料夾 (確保路徑正確)
cd /d C:\stockAlgoTrading

:: 執行程式
python gui_monitor.py

:: 如果你想看錯誤訊息，可以把下面這行 'exit' 拿掉，改寫成 'pause'
exit