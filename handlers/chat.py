from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import DATA_PATH, ADMIN_ID
from utils.storage import load_data, save_data
import time

user_partners: dict[int, int] = {}
waiting_since: dict[int, float] = {}

def reload_data():
    global user_partners
    partners, _ = load_data(DATA_PATH)
    user_partners = partners

async def find_partner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id if query else update.effective_user.id
    
    if user_id == ADMIN_ID:
        await (query.edit_message_text if query else update.message.reply_text)('🔧 Админ не участвует в чатах.')
        return
    
    reload_data()
    
    # Удаляем из предыдущего чата
    if user_id in user_partners:
        partner_id = user_partners.pop(user_id, None)
        if partner_id:
            user_partners.pop(partner_id, None)
    
    # Очередь ожидания
    waiting_users = [uid for uid, pid in user_partners.items() if pid is None and uid != user_id]
    
    if waiting_users:
        partner_id = waiting_users[0]
        user_partners[user_id] = partner_id
        user_partners[partner_id] = user_id
        save_data(DATA_PATH, user_partners, {})
        
        keyboard = [[InlineKeyboardButton("❌ Завершить чат", callback_data='stop')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await (query.edit_message_text if query else update.message.reply_text)(
            '✅ <b>Партнёр найден!</b>\n\n✨ Теперь можете общаться!', 
            parse_mode='HTML', reply_markup=reply_markup)
        await context.bot.send_message(partner_id, 
            '✅ <b>Партнёр найден!</b>\n\n✨ Теперь можете общаться!', 
            parse_mode='HTML', reply_markup=reply_markup)
    else:
        user_partners[user_id] = None
        waiting_since[user_id] = time.time()
        save_data(DATA_PATH, user_partners, {})
        await (query.edit_message_text if query else update.message.reply_text)('⏳ <b>Ищем партнёра...</b>\n\n⏰ Пожалуйста подождите.')

async def stop_chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    
    if user_id in user_partners:
        partner_id = user_partners.pop(user_id, None)
        if partner_id and partner_id in user_partners:
            user_partners.pop(partner_id, None)
            save_data(DATA_PATH, user_partners, {})
            await context.bot.send_message(partner_id, '❌ <b>Партнёр отключился</b>', parse_mode='HTML')
        
        keyboard = [[InlineKeyboardButton("🔍 Новый поиск", callback_data='find')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text('❌ <b>Чат завершён</b>\n\n🔍 Найти нового партнёра?', 
                                     parse_mode='HTML', reply_markup=reply_markup)
