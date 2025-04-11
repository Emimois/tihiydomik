#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler
import os

# Этапы диалога
NAME, PHONE, SERVICE, DESCRIPTION, PHOTO = range(5)

# Токен и ID менеджера
TOKEN = '8183788727:AAFweQjQaLH7YoR1DNyijdwmumA5HZzepBQ'
MANAGER_CHAT_ID = 990020148  # замени на свой Telegram ID

# Словарь: user_id -> статус
request_status = {}

# Клавиатура с услугами
service_keyboard = ReplyKeyboardMarkup([
    ['🛠 Ремонт под ключ', '🔇 Шумоизоляция'],
    ['🚿 Сантехнические работы', '🪵 Укладка полов'],
    ['💡 Электрика', '❓ Другое']
], one_time_keyboard=True, resize_keyboard=True)

def start(update: Update, context: CallbackContext) -> int:
    welcome = (
        "👋 Привет! Я бот команды *«Тихий дом»* — помогаем с ремонтом квартир в Москве и области.\n\n"
        "🔧 *Наши услуги:*\n"
        "• 🛠 Ремонт под ключ\n"
        "• 🔇 Шумоизоляция\n"
        "• 💡 Электрика и сантехника\n"
        "• 🪵 Укладка полов и отделка\n\n"
        "Давайте начнём! Как вас зовут?"
    )
    update.message.reply_text(welcome, parse_mode='Markdown')
    return NAME

def get_name(update: Update, context: CallbackContext) -> int:
    context.user_data['name'] = update.message.text
    update.message.reply_text(f"Отлично, {context.user_data['name']}! 📞 Напишите ваш номер телефона.")
    return PHONE

def get_phone(update: Update, context: CallbackContext) -> int:
    context.user_data['phone'] = update.message.text
    update.message.reply_text("💬 Выберите подходящую услугу или напишите свою:", reply_markup=service_keyboard)
    return SERVICE

def get_service(update: Update, context: CallbackContext) -> int:
    context.user_data['service'] = update.message.text
    update.message.reply_text(f"{context.user_data['name']}, ✍️ Расскажите подробнее о задаче.")
    return DESCRIPTION

def get_description(update: Update, context: CallbackContext) -> int:
    context.user_data['description'] = update.message.text
    update.message.reply_text(
        "📷 Пришлите фото текущего состояния или примеры. Если нет фото — напишите *Пропустить*", parse_mode='Markdown'
    )
    return PHOTO

def get_photo(update: Update, context: CallbackContext) -> int:
    photo = update.message.photo[-1].file_id if update.message.photo else None
    context.user_data['photo'] = photo
    user_id = update.message.from_user.id

    request_status[user_id] = "🕒 Ожидает обработки"

    msg = (
        f"📥 Новая заявка:\n\n"
        f"👤 Имя: {context.user_data['name']}\n"
        f"🆔 ID клиента: {user_id}\n"
        f"📞 Телефон: {context.user_data['phone']}\n"
        f"🧰 Услуга: {context.user_data['service']}\n"
        f"📝 Описание: {context.user_data['description']}\n"
        f"📌 Статус: {request_status[user_id]}"
    )
    context.bot.send_message(chat_id=MANAGER_CHAT_ID, text=msg)
    if photo:
        context.bot.send_photo(chat_id=MANAGER_CHAT_ID, photo=photo)

    update.message.reply_text(
        "✅ Спасибо за заявку! Мы скоро свяжемся с вами.\n\n"
        "🔥 *Акция:* замер бесплатно + скидка 10% при заказе ремонта под ключ!", parse_mode='Markdown'
    )
    return ConversationHandler.END

def skip_photo(update: Update, context: CallbackContext) -> int:
    return get_photo(update, context)

def cancel(update: Update, context: CallbackContext) -> int:
    update.message.reply_text("❌ Заявка отменена. Напишите /start, чтобы начать заново.")
    return ConversationHandler.END

def faq(update: Update, context: CallbackContext):
    update.message.reply_text(
        "❓ Часто задаваемые вопросы:\n\n"
        "• ⏳ Сколько длится ремонт? — от 7 до 30 дней\n"
        "• 📄 Работаем по договору? — Да, официально\n"
        "• 🛠 Можно частично? — Да\n"
        "• ✅ Гарантия? — 6 месяцев", parse_mode='Markdown'
    )

def check_status(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    status = request_status.get(user_id, "😔 Заявка не найдена.")
    update.message.reply_text(f"📍 Текущий статус вашей заявки:\n{status}")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, get_name)],
            PHONE: [MessageHandler(Filters.text & ~Filters.command, get_phone)],
            SERVICE: [MessageHandler(Filters.text & ~Filters.command, get_service)],
            DESCRIPTION: [MessageHandler(Filters.text & ~Filters.command, get_description)],
            PHOTO: [
                MessageHandler(Filters.photo, get_photo),
                MessageHandler(Filters.text & ~Filters.command, skip_photo)
            ],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler('faq', faq))
    dp.add_handler(CommandHandler('status', check_status))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()

