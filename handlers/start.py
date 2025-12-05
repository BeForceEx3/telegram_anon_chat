from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import ADMIN_ID

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id == ADMIN_ID:
        keyboard = [[InlineKeyboardButton("📊 Статистика", callback_data='stats')],
                    [InlineKeyboardButton("🔄 Перезагрузить данные", callback_data='reload')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('🔧 <b>Админ-панель</b>\n\n✅ Бот запущен!\n📱 Все сообщения доступны.', 
                                       parse_mode='HTML', reply_markup=reply_markup)
    else:
        keyboard = [[InlineKeyboardButton("🔍 Найти партнера", callback_data='find')],
                    [InlineKeyboardButton("ℹ️ Помощь", callback_data='help')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            '👻 <b>Добро пожаловать в Анонимный Чат!</b>\n\n'
            '✨ <i>Пиши анонимно с незнакомцами!</i>\n\n'
            '👇 Нажми кнопку ниже чтобы начать!', parse_mode='HTML', 
            reply_markup=reply_markup)
