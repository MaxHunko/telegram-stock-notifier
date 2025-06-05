import json
import pymysql
import requests
import os
from datetime import datetime

"""
📄 Автор: Max Hunko
🔒 Код призначений лише для ознайомлення. Комерційне використання заборонене без дозволу автора.
"""
 
with open('settings.json', 'r') as f:
    settings = json.load(f)

BASE_URL = settings["api"]["url"]
LOGIN = settings["api"]["username"]
PASSWORD = settings["api"]["password"]
TOKEN = None
TELEGRAM_BOT_TOKEN = settings["bot_token"]
ADMIN_IDS = settings["admins"]


def log_message(message):
    os.makedirs("logs", exist_ok=True)

    timestamp = datetime.now().strftime("[%d.%m.%Y - %H:%M:%S] =>")

    with open("logs/check.txt", "a", encoding="utf-8") as log_file:
        log_file.write(f"{timestamp} {message}\n")

    print(f"{timestamp} {message}")


def send_telegram_message(admin_id, message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": admin_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        log_message(f"Message sent to admin {admin_id}")
    else:
        log_message(f"Error sending message to admin {admin_id}: {response.text}")


def authenticate():
    global TOKEN
    url = f"{BASE_URL}api/auth/"
    payload = {"login": LOGIN, "password": PASSWORD}
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200 and response.json().get("status") == "OK":
        TOKEN = response.json()["response"]["token"]
        log_message("Authorization successful")
    else:
        log_message(f"Authorization error: {response.status_code} - {response.json()}")


def get_open_items(connection):
    query = """
    SELECT id, sku, name, phone, quantity, comment, product, url, np_address
    FROM orders
    WHERE status = 'open' AND checked = 0;
    """
    with connection.cursor() as cursor:
        cursor.execute(query)
        return cursor.fetchall()


def update_item_status(connection, item_id, confirmed_stock):
    
    # 🔒


def main():
    db_settings = settings["db_config"]

    connection = pymysql.connect(
        host=db_settings["host"],
        user=db_settings["user"],
        password=db_settings["password"],
        database=db_settings["database"],
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor
    )

    try:
        authenticate()
        if not TOKEN:
            log_message("Failed to get token. Aborting.")
            return

        items = get_open_items(connection)
        if not items:
            log_message("No orders to check.")
            return

        skus = [item["sku"].replace("Артикул: ", "") for item in items]

        stock_status = check_stock_bulk(skus)

        for item in items:
            item_id = item["id"]
            sku = item["sku"].replace("Артикул: ", "")

            if stock_status.get(sku):
                log_message(f"Item {sku} in stock. Updating status.")
                update_item_status(connection, item_id, "Yes")

                message = (
                    f"✅ <b>Пред-замовлення в наявності</b>: {item_id} \n\n"
                    f"👤 <b>Ім'я:</b> {item.get('name', 'Невідомо')}\n"
                    f"📞 <b>Телефон:</b> {item.get('phone', 'Невідомо')}\n\n"
                    f"📦 <b>Товар:</b> {item.get('product', '---')}\n"
                    f"📜 <b>Артикул:</b> {sku}\n"
                    f"🔢 <b>Кількість:</b> {item.get('quantity', '0')}\n"
                    f"🏢 <b>Адреса Нової Пошти:</b> {item.get('np_address', '---')}\n\n"
                )

                if item.get('comment'):
                    message += f"💬 <b>Коментар:</b> {item['comment']}\n\n"

                message += (
                    f"<a href=\"{item.get('url', '#')}\">🔗 <b>Посилання</b></a>\n"
                    f"🔍 <b>Наявність:</b> {'Так 🟢' if stock_status.get(sku) else 'Ні 🔴'}\n"
                )
                for admin_id in ADMIN_IDS:
                    send_telegram_message(admin_id, message)
            else:
                log_message(f"Item {sku} is out of stock.")

    except Exception as e:
        log_message(f"Runtime error: {str(e)}")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
