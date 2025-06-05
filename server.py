import logging
from flask import Flask, request
from flask_cors import CORS
import mysql.connector
import json
import requests

"""
📄 Автор: Max Hunko
🔒 Код призначений лише для ознайомлення. Комерційне використання заборонене без дозволу автора.
"""
 
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='logs/app.log',
    filemode='a'
)
app = Flask(__name__)
CORS(app)

try:
    with open('settings.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError as e:
    logging.critical(f"Settings file settings.json not found: {e}")
    raise
except json.JSONDecodeError as e:
    logging.critical(f"Error reading settings file: {e}")
    raise

db_config = config['db_config']
bot_token = config['bot_token']
admins = config['admins']

def send_telegram_message(message):
    for admin in admins:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            params = {
                'chat_id': admin,
                'text': message,
                'parse_mode': 'HTML',
                'disable_web_page_preview': 'True'
            }
            response = requests.get(url, params=params, verify=False)
            if response.status_code == 200:
                logging.info(f"Message successfully sent to administrator {admin}")
            else:
                logging.error(f"Error sending message to administrator {admin}: {response.text}")
        except Exception as e:
            logging.error(f"Error sending message to Telegram: {e}")

@app.route('/submit', methods=['POST'])
def handle_data():
    try:
        data = request.get_json()

        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor()

        cursor.execute("SELECT MAX(pre_order_number) FROM orders")
        result = cursor.fetchone()
        last_order_number = result[0]

        if last_order_number is None:
            new_order_number = 1
        else:
            new_order_number = int(last_order_number) + 1

        sql = """
            INSERT INTO orders (pre_order_number, name, phone, quantity, comment, product, sku, url, status, np_address)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            new_order_number,
            data['name'],
            data['phone'],
            data['quantity'],
            data.get('comment', ''),
            data['product'],
            data['sku'],
            data['url'],
            'open',
            data.get('npAddress')
        )

        cursor.execute(sql, values)
        conn.commit()
        logging.info(f"Data successfully added to the database. New order number: {new_order_number}")


        cursor.close()
        conn.close()
        
        message = (
            f"🎉  <b>Нове пред-замовлення № {new_order_number}</b> 🎉 \n\n"
            f"👤 <b>Ім'я:</b> {data['name']}\n"
            f"📞 <b>Телефон:</b> {data['phone']}\n\n"
            f"📦 <b>Товар:</b> {data['product']}\n"
            f"📜 <b>{data['sku']}</b>\n"
            f"🔢 <b>Кількість:</b> {data['quantity']}\n\n"
            f"🏢 <b>Адреса Нової Пошти:</b> {data.get('npAddress', '---')}\n\n"
            f"💬 <b>Коментар:</b> {data.get('comment', '---')}\n\n"
            f"<a href=\"{data['url']}\">🔗 <b>Посилання</b></a>\n"
        )
        
        send_telegram_message(message)

        return '', 204
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return '', 500

if __name__ == '__main__':
    try:
        app.run(
            host='0.0.0.0',
            port=5001,
            ssl_context=(
                'fullchain.pem',
                '/privkey.pem'
            )
        )
    except Exception as e:
        logging.critical(f"Error starting application: {e}")