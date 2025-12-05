from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import DATAPATH, ADMIN_ID  # ✅ ИСПРАВЛЕНО: ADMINID → ADMIN_ID
from utils.storage import loaddata, savedata
import time

userpartners = {}
waitingsince = {}

def reloaddata():
    global userpartners
    partners, messages = loaddata(DATAPATH)
    userpartners = partners

async def findpartner(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    userid = query.from_user.id if query else update.effective_user.id
    
    if userid == ADMIN_ID:  # ✅ ИСПРАВЛЕНО: ADMINID → ADMIN_ID
        if query:
            await query.edit_message_text("👑 Админ не может искать партнёров.")
        else:
            await update.message.reply_text("👑 Админ не может искать партнёров.")
        return
    
    reloaddata()
    
    if userid in userpartners:
        partnerid = userpartners.pop(userid, None)
        if partnerid:
            userpartners.pop(partnerid, None)
        
        waitingusers = [uid for uid, pid in userpartners.items() if pid is None and uid != userid]
        if waitingusers:
            partnerid = waitingusers[0]
            userpartners[userid] = partnerid
            userpartners[partnerid] = userid
            savedata(DATAPATH, userpartners, {})
            
            keyboard = [[InlineKeyboardButton("🛑 Остановить чат", callback_data="stop")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if query:
                await query.edit_message_text(
                    "<b>✅ Партнёр найден!</b>\n🔒 Чат начался!", 
                    parse_mode='HTML', reply_markup=reply_markup
                )
            else:
                await update.message.reply_text(
                    "<b>✅ Партнёр найден!</b>\n🔒 Чат начался!", 
                    parse_mode='HTML', reply_markup=reply_markup
                )
            await context.bot.send_message(
                partnerid, 
                "<b>✅ Партнёр найден!</b>\n🔒 Чат начался!", 
                parse_mode='HTML', reply_markup=reply_markup
            )
        else:
            userpartners[userid] = None
            waitingsince[userid] = time.time()
            savedata(DATAPATH, userpartners, {})
            
            if query:
                await query.edit_message_text("<b>🔍 Ищем партнёра...</b>\n⏳ 1-2 минуты.", parse_mode='HTML')
            else:
                await update.message.reply_text("<b>🔍 Ищем партнёра...</b>\n⏳ 1-2 минуты.", parse_mode='HTML')
    else:
        userpartners[userid] = None
        waitingsince[userid] = time.time()
        savedata(DATAPATH, userpartners, {})
        
        if query:
            await query.edit_message_text("<b>🔍 Ищем партнёра...</b>\n⏳ 1-2 минуты.", parse_mode='HTML')
        else:
            await update.message.reply_text("<b>🔍 Ищем партнёра...</b>\n⏳ 1-2 минуты.", parse_mode='HTML')

async def stopchat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    userid = query.from_user.id
    
    if userid in userpartners:
        partnerid = userpartners.pop(userid, None)
        if partnerid and partnerid in userpartners:
            userpartners.pop(partnerid, None)
        savedata(DATAPATH, userpartners, {})
        
        if partnerid:
            await context.bot.send_message(partnerid, "<b>👋 Партнёр отключился</b>", parse_mode='HTML')
        
        keyboard = [[InlineKeyboardButton("🔍 Найти нового", callback_data="find")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "<b>🛑 Чат остановлен</b>\n🔍 Найдите нового партнёра?", 
            parse_mode='HTML', reply_markup=reply_markup
        )
