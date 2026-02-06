import smtplib
from email.mime.text import MIMEText
from email.header import Header

# ================= 自架 SMTP 設定區 =================
# 1. 伺服器位置 (IP 或 Domain)
SMTP_SERVER = "mail.gkgary.com"

# 2. 連接埠 (Port)
# - 587: 通常用於 TLS (最常見)
# - 465: 通常用於 SSL (舊式標準，但仍常用)
# - 25:  通常無加密 (內部網路或測試用)
SMTP_PORT = 25

# 3. 帳號密碼
MY_EMAIL = "service@gkgary.com"  # 寄件帳號
MY_PASSWORD = "gkGary@1234"  # 你的 SMTP 密碼
TO_EMAIL = "crown2754@gmail.com"  # 你要收信的信箱

# 4. 加密模式 (重要！)
# True = 使用 STARTTLS (對應 Port 587/25)
# False = 使用 SSL (對應 Port 465) 或 不加密
USE_TLS = False
# =================================================


def send_signal_email(subject, content):
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = Header(subject, "utf-8")
    msg["From"] = MY_EMAIL
    msg["To"] = TO_EMAIL

    try:
        # 判斷連線模式
        if SMTP_PORT == 465:
            # SSL 模式 (常見於 Port 465)
            server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        else:
            # 一般模式 (常見於 Port 587 或 25)
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)

            # 如果是 587，通常需要啟動 TLS 加密
            if USE_TLS:
                server.starttls()

        # 登入 (如果你的 SMTP 不需要驗證，可以把這兩行註解掉)
        if MY_EMAIL and MY_PASSWORD:
            server.login(MY_EMAIL, MY_PASSWORD)

        # 發送
        server.send_message(msg)
        server.quit()
        print(f"✅ [自架SMTP] 信件已發送至 {TO_EMAIL}")

    except Exception as e:
        print(f"❌ 寄信失敗: {e}")
        # 如果失敗，印出更詳細的錯誤建議
        if "Authentication" in str(e):
            print("💡 提示: 請檢查帳號密碼是否正確，或伺服器是否允許該 IP 連線。")
        elif "refused" in str(e):
            print("💡 提示: 連線被拒，請檢查 Port 是否正確，或防火牆是否擋住了。")


if __name__ == "__main__":
    send_signal_email(
        "SMTP 測試信",
        "恭喜！你的自架 SMTP Server 串接成功！\n這是一封來自 Python 機器人的自動通知。",
    )
