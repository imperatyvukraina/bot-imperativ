"""
Телеграм-бот для Заводу Імператив
===================================
Встановлення залежностей:
  pip install python-telegram-bot

Запуск:
  python bot_imperativ.py
"""
 
import logging
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)
from datetime import datetime

# ─── НАЛАШТУВАННЯ ────────────────────────────────────────────────────────────

import os
BOT_TOKEN = os.environ.get("BOT_TOKEN")
GROUP_CHAT_ID = -5183766443         # Твоя Telegram-група

VACANCIES = [
    "Оператор виробничої лінії",
]

# ─── СТАНИ РОЗМОВИ ───────────────────────────────────────────────────────────

NAME, PHONE, VACANCY, ABOUT = range(4)

# ─── ЛОГУВАННЯ ───────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ─── ВІДПРАВКА В ГРУПУ ───────────────────────────────────────────────────────

async def send_to_group(context: ContextTypes.DEFAULT_TYPE, data: dict, resume_file_id: str = None):
    text = (
        f"📋 <b>Нова заявка!</b>\n\n"
        f"👤 <b>Ім'я:</b> {data['name']}\n"
        f"📞 <b>Телефон:</b> {data['phone']}\n"
        f"💼 <b>Вакансія:</b> {data['vacancy']}\n"
        f"📝 <b>Про себе:</b> {data['about']}\n\n"
        f"🕐 {data['date']}"
    )
    await context.bot.send_message(
        chat_id=GROUP_CHAT_ID,
        text=text,
        parse_mode="HTML"
    )
    if resume_file_id:
        await context.bot.send_document(
            chat_id=GROUP_CHAT_ID,
            document=resume_file_id,
            caption=f"Резюме від {data['name']}"
        )

# ─── ОБРОБНИКИ РОЗМОВИ ───────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Привіт! Це бот Заводу Імператив.\n\n"
        "Ми раді, що ти розглядаєш роботу у нас.\n"
        "Я допоможу надіслати твою заявку — це займе лише 2 хвилини.\n\n"
        "Як тебе звати? Напиши своє ім'я та прізвище.\n"
        "Приклад: Іваненко Олексій",
        reply_markup=ReplyKeyboardRemove()
    )
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["name"] = update.message.text.strip()

    phone_button = KeyboardButton("Поділитись номером", request_contact=True)
    keyboard = ReplyKeyboardMarkup([[phone_button]], resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        f"Чудово, {context.user_data['name']}!\n\n"
        "Тепер поділись своїм номером телефону — натисни кнопку нижче, "
        "або напиши вручну.",
        reply_markup=keyboard
    )
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if update.message.contact:
        phone = update.message.contact.phone_number
        if not phone.startswith("+"):
            phone = "+" + phone
    else:
        phone = update.message.text.strip()

    context.user_data["phone"] = phone

    vacancy_buttons = [[v] for v in VACANCIES]
    keyboard = ReplyKeyboardMarkup(vacancy_buttons, resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "На яку посаду ти хочеш потрапити?",
        reply_markup=keyboard
    )
    return VACANCY

async def get_vacancy(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    vacancy = update.message.text.strip()
    if vacancy not in VACANCIES:
        await update.message.reply_text("Будь ласка, обери вакансію з кнопок вище.")
        return VACANCY

    context.user_data["vacancy"] = vacancy

    skip_button = ReplyKeyboardMarkup([["Пропустити"]], resize_keyboard=True, one_time_keyboard=True)

    await update.message.reply_text(
        "Розкажи трохи про себе: вік, де живеш, чи є досвід роботи на виробництві.\n\n"
        "Або прикріпи файл резюме (PDF або Word).\n\n"
        "Якщо нічого немає — натисни «Пропустити».",
        reply_markup=skip_button
    )
    return ABOUT

async def get_about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    resume_file_id = None

    if update.message.document:
        resume_file_id = update.message.document.file_id
        about_text = "Надіслав резюме (файл)"
    elif update.message.text and update.message.text.strip() == "Пропустити":
        about_text = "—"
    else:
        about_text = update.message.text.strip() if update.message.text else "—"

    data = {
        "name": context.user_data["name"],
        "phone": context.user_data["phone"],
        "vacancy": context.user_data["vacancy"],
        "about": about_text,
        "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
    }

    await send_to_group(context, data, resume_file_id)

    await update.message.reply_text(
        "Дякуємо! Твоя заявка прийнята.\n\n"
        "Наш HR-менеджер зв'яжеться з тобою найближчим часом.\n\n"
        "Гарного дня! 👋",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Заявку скасовано. Якщо захочеш подати знову — напиши /start",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ─── ЗАПУСК БОТА ─────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME:    [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            PHONE:   [
                MessageHandler(filters.CONTACT, get_phone),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone),
            ],
            VACANCY: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_vacancy)],
            ABOUT:   [
                MessageHandler(filters.Document.ALL, get_about),
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_about),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    logger.info("Бот запущено...")
    app.run_polling()

if __name__ == "__main__":
    main()
