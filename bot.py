import logging
import json
from datetime import datetime, timezone, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8486993696:AAFLyvI3lbMYltXTKXVSbMj552dcXaXwgRI"
MODERATOR_CHAT_ID = -1003816309605
REQUIRED_CHANNEL = "@TheBr1aH"
CHANNEL_ID = -1002563413691
WEBAPP_URL = "https://strong-mermaid-746240.netlify.app"

MSK = timezone(timedelta(hours=3))
logging.basicConfig(level=logging.INFO)

def get_msk_time():
    return datetime.now(MSK)

async def check_subscription(user_id, context):
    try:
        chat_member = await context.bot.get_chat_member(REQUIRED_CHANNEL, user_id)
        if chat_member.status in ["member", "administrator", "creator"]:
            return True
    except:
        pass
    try:
        chat_member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        return chat_member.status in ["member", "administrator", "creator"]
    except:
        return False

def get_main_menu():
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("🚀 Открыть меню", web_app=WebAppInfo(url=WEBAPP_URL))
    ]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_subscription(user_id, context):
        keyboard = [[InlineKeyboardButton("📢 Подписаться", url="https://t.me/TheBr1aH")]]
        await update.message.reply_text(
            f"🔒 Подпишись на @TheBr1aH",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    await update.message.reply_text(
        f"👋 Привет! Нажми кнопку:",
        reply_markup=get_main_menu()
    )

async def webapp_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    raw_data = update.message.web_app_data.data
    
    print(f"📥 ПОЛУЧЕНО: {raw_data}")
    
    if not await check_subscription(user.id, context):
        await update.message.reply_text("🔒 Подпишись на @TheBr1aH")
        return
    
    try:
        form_data = json.loads(raw_data)
        ticket_type = form_data.get('type')
        msk_time = get_msk_time().strftime("%d.%m.%Y %H:%M:%S")
        
        if ticket_type == "complaint":
            text = f"⚠️ ЖАЛОБА\n\n🎮 ID: {form_data.get('userId')}\n💬 {form_data.get('reason')}\n📸 {form_data.get('screenshot')}"
        elif ticket_type == "donate":
            text = f"💎 ДОНАТ\n\n🎮 ID: {form_data.get('userId')}\n📦 {form_data.get('product')}\n📸 {form_data.get('screenshot')}"
        elif ticket_type == "unmute":
            text = f"🔓 РАЗМУТ\n\n🎮 ID: {form_data.get('userId')}\n🔨 {form_data.get('muteReason')}\n💬 {form_data.get('appealReason')}"
        else:
            await update.message.reply_text("❌ Ошибка")
            return
        
        full_text = f"{text}\n\n👤 {user.full_name}\n🆔 {user.id}\n⏰ {msk_time}"
        
        sent = await context.bot.send_message(
            chat_id=MODERATOR_CHAT_ID,
            text=full_text
        )
        
        if 'ticket_map' not in context.bot_data:
            context.bot_data['ticket_map'] = {}
        context.bot_data['ticket_map'][sent.message_id] = user.id
        
        await update.message.reply_text("✅ Отправлено!")
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

async def forward_to_player(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.chat_id != MODERATOR_CHAT_ID:
        return
    if not update.message.reply_to_message:
        return
    
    ticket_map = context.bot_data.get('ticket_map', {})
    player_id = ticket_map.get(update.message.reply_to_message.message_id)
    
    if player_id:
        await context.bot.send_message(
            chat_id=player_id,
            text=f"📩 Ответ: {update.message.text}"
        )
        await update.message.reply_text("✅ Отправлено")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, webapp_handler))
    app.add_handler(MessageHandler(filters.TEXT & filters.Chat(MODERATOR_CHAT_ID), forward_to_player))
    
    print("🤖 Бот запущен")
    app.run_polling()

if __name__ == "__main__":
    main()
