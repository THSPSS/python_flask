import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, MessageHandler, CallbackQueryHandler, ContextTypes, filters

load_dotenv()

TOKEN = os.getenv("TOKEN")

# Respond to any text message with buttons
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("20일 RSI 검색", callback_data='rsi')],
        [InlineKeyboardButton("아래꼬리 긴 모양 검색", callback_data='long-shadow')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    message = (
        "📊 <b>주식 검색 도우미</b>\n\n"
        "아래에서 원하시는 검색 유형을 선택해주세요:"
    )

    await update.message.reply_text(message, reply_markup=reply_markup)

# Respond to button presses
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    response_map = {
        'rsi': "📊 RSI 검색 실행 중입니다...",
        'long-shadow': "🔍 아래꼬리 긴 모양 검색 실행 중입니다...",
    }

    response = response_map.get(query.data, "❓ 알 수 없는 명령입니다.")
    await query.edit_message_text(text=response)

# Main app
if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(CallbackQueryHandler(handle_button))

    print("🤖 Bot is running...")
    app.run_polling()
