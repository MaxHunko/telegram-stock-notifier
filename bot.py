import json
from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
    ConversationHandler
)
import mysql.connector
from telegram.ext import ConversationHandler
import subprocess

"""
📄 Автор: Max Hunko
🔒 Код призначений лише для ознайомлення. Комерційне використання заборонене без дозволу автора.
"""
 
LOG_FILE = "logs/server_restart.log"
WAITING_ORDER_NUMBER = 1

with open("settings.json", "r") as file:
    settings = json.load(file)

db_config = settings["db_config"]
BOT_TOKEN = settings["bot_token"]
ADMIN_IDS = settings["admins"]

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("У вас немає доступу до цього бота.")
        return

    keyboard = [
        [KeyboardButton("📦 Актуальні пред-замовлення")],
        [KeyboardButton("✅️ Пред-замовлення в наявності")],
        [KeyboardButton("🔍 Перевірити наявність")],
        [KeyboardButton("🏁 Закрити пред-замовлення")],
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    await update.message.reply_text("Ласкаво просимо до CRM. Виберіть дію:", reply_markup=reply_markup)


async def send_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("У вас немає доступу до логів.")
        return

    try:
        with open(LOG_FILE, "r", encoding="utf-8") as log_file:
            logs = log_file.readlines()[-20:]
            log_text = "".join(logs) if logs else "Логи порожні."
        
        await update.message.reply_text(f"```\n{log_text}\n```", parse_mode="MarkdownV2")
    except FileNotFoundError:
        await update.message.reply_text("Файл логів не знайдено.")
    except Exception as e:
        await update.message.reply_text(f"Помилка при читанні логів: {e}")


async def view_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # 🔒

async def in_stock_orders(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # 🔒

async def process_close_order_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    order_id = query.data.split(":")[1]
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("UPDATE orders SET status = 'closed' WHERE pre_order_number = %s", (order_id,))
    conn.commit()
    cursor.close()
    conn.close()

    await query.edit_message_text(f"Пред-замовлення № {order_id} успішно закрито!")


async def close_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    cursor.execute("SELECT pre_order_number FROM orders WHERE status = 'open'")
    orders = cursor.fetchall()

    if not orders:
        await update.message.reply_text("Немає пред-замовлень для закриття.")
        cursor.close()
        conn.close()
        return ConversationHandler.END

    context.user_data['open_orders'] = [order[0] for order in orders]

    await update.message.reply_text("Введіть номер пред-замовлення для закриття:")
    cursor.close()
    conn.close()

    return WAITING_ORDER_NUMBER


async def process_close_order(update: Update, context: ContextTypes.DEFAULT_TYPE):

    # 🔒

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^📦 Актуальні пред-замовлення$"), view_orders))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^✅️ Пред-замовлення в наявності$"), in_stock_orders))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^🔍 Перевірити наявність$"), check_availability))
    application.add_handler(CallbackQueryHandler(process_close_order_callback, pattern="^close_order:"))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^logs$"), send_logs))

    close_order_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("^🏁 Закрити пред-замовлення$"), close_order)],
        states={
            WAITING_ORDER_NUMBER: [
                MessageHandler(
                    filters.Regex("^(📦 Актуальні пред-замовлення|✅️ Пред-замовлення в наявності|🔍 Перевірити наявність|🏁 Закрити пред-замовлення)$"),
                    process_close_order
                ),
                MessageHandler(filters.TEXT & ~filters.COMMAND, process_close_order),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(close_order_handler)

    
    application.run_polling()

if __name__ == "__main__":
    main()
