import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from core.settings import MAX_LENGTH
from scan.kr.long_shadow_scan import long_lower_shadow_scan, format_shadow_message
from scan.kr.new_high_scan import run_new_high_scan, format_new_high_message
from scan.kr.rsi_scan import format_rsi_message, rsi_scan
from scan.us.long_lower_shadow import *
from scan.us.new_high_scan import *
from scan.us.rsi_scan import *

SEARCH_CONFIG = {
    # 🇰🇷 한국 종목
    'rsi': {
        'label': '📈 RSI 분석 중...',
        'function': lambda: rsi_scan(),
        'formatter': format_rsi_message
    },
    'lower-shadow': {
        'label': '💧 아래꼬리 검색 중...',
        'function': lambda: long_lower_shadow_scan(),
        'formatter': format_shadow_message
    },
    '52w': {
        'label': '📊 52주 신고가 검색 중...',
        'function': lambda: run_new_high_scan(date="250"),
        "formatter": lambda df: format_new_high_message(df, date="52"),
    },
    '30w': {
        'label': '📊 30주 신고가 검색 중...',
        'function': lambda: run_new_high_scan(date="150"),
        "formatter": lambda df: format_new_high_message(df, date="30"),
    },
    # 🇺🇸 미국 종목
    'us-rsi': {
        'label': '🇺🇸📈 미국 RSI 분석 중...',
        'function': lambda: us_rsi_scan(),
        'formatter': format_us_rsi_summary
    },
    'us-lower-shadow': {
        'label': '🇺🇸💧 미국 아래꼬리 검색 중...',
        'function': lambda: us_long_lower_shadow_scan(),
        'formatter': format_us_long_shadow
    },
    'us-52w': {
        'label': '🇺🇸📊 미국 52주 신고가 검색 중...',
        'function': lambda: us_new_high_scan(),
        'formatter': lambda df: format_us_high(df , date = "52")
    },
    'us-30w': {
        'label': '📊 미국 30주 신고가 검색 중...',
        'function': lambda: us_new_high_scan(date=150),
        'formatter': lambda df: format_us_high(df , date = "30")
    },
}

load_dotenv()

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 봇 토큰 설정
BOT_TOKEN = os.getenv('TOKEN')

# 사용자 상태 관리
user_states = {}


# /start 명령어 처리
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """사용자가 /start 명령어를 입력했을 때 처리"""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    logger.info(f"User {user_id} chat_id {chat_id} started the bot")

    # 사용자 상태 설정
    user_states[user_id] = 'waiting_for_selection'

    # 인라인 키보드 생성
    keyboard = [
        [
            InlineKeyboardButton("📈 RSI (🇰🇷)", callback_data='rsi'),
            InlineKeyboardButton("📈 RSI (🇺🇸)", callback_data='us-rsi')
        ],
        [
            InlineKeyboardButton("💧 아래꼬리 (🇰🇷)", callback_data='lower-shadow'),
            InlineKeyboardButton("💧 아래꼬리 (🇺🇸)", callback_data='us-lower-shadow')
        ],
        [
            InlineKeyboardButton("📊 52주 신고가 (🇰🇷)", callback_data='52w'),
            InlineKeyboardButton("📊 52주 신고가 (🇺🇸)", callback_data='us-52w')
        ],
        [
            InlineKeyboardButton("📊 30주 신고가 (🇰🇷)", callback_data='30w'),
            InlineKeyboardButton("📊 30주 신고가 (🇺🇸)", callback_data='us-30w')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "검색할 옵션을 선택하세요:",
        reply_markup=reply_markup
    )


# 일반 메시지 처리
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """일반 메시지 처리 - /start가 아닌 메시지에 대한 응답"""
    user_id = update.effective_user.id
    text = update.message.text

    logger.info(f"User {user_id} sent message: {text}")

    # /start를 보내지 않은 경우
    if user_id not in user_states:
        await update.message.reply_text("시작하려면 /start 명령어를 입력해주세요.")


# 콜백 쿼리 처리 (버튼 클릭)
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """인라인 키보드 버튼 클릭 처리"""
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data

    logger.info(f"User {user_id} clicked button: {data}")

    # 콜백 쿼리 확인
    await query.answer()

    # 사용자 상태 확인
    if user_states.get(user_id) == 'waiting_for_selection':
        await handle_search_selection(query, user_id, data)
    else:
        await query.edit_message_text("세션이 만료되었습니다. /start 를 다시 입력해주세요.")


# 검색 선택 처리
async def handle_search_selection(query, user_id: int, selected_option: str):
    if selected_option not in SEARCH_CONFIG:
        await query.edit_message_text("잘못된 선택입니다. /start 를 다시 입력해주세요.")
        user_states.pop(user_id, None)
        return

    user_states[user_id] = 'searching'
    await perform_search(query, user_id, selected_option)


# 검색 수행
async def perform_search(query, user_id: int, search_type: str):
    try:
        logger.info(f"🔎 사용자 {user_id} 검색 시작: {search_type}")

        config = SEARCH_CONFIG.get(search_type)
        if not config:
            await query.message.reply_text("지원하지 않는 검색 유형입니다.")
            return

        # 검색 시작 메시지
        await query.edit_message_text(config['label'])

        await asyncio.sleep(1)  # UX용 대기

        df = config['function']()
        message = config['formatter'](df)

        # 메시지 분할 전송
        await send_long_message(query, message)

    except Exception as e:
        logger.error(f"❌ 검색 중 오류: {e}")
        await query.message.reply_text("검색 중 오류가 발생했습니다. 다시 /start 명령어로 시도해주세요.")
    finally:
        user_states.pop(user_id, None)
        await asyncio.sleep(1)
        await query.message.reply_text("새로운 검색을 원하시면 /start 를 입력해주세요.")

async def send_long_message(query, message: str):
    if len(message) <= MAX_LENGTH:
        await query.message.reply_text(message)
        return

    lines = message.split('\n\n')
    chunk = ""

    for line in lines:
        # 줄 자체가 너무 길면 쪼개기
        if len(line) > MAX_LENGTH:
            while len(line) > MAX_LENGTH:
                part = line[:MAX_LENGTH]
                await query.message.reply_text(part.strip())
                line = line[MAX_LENGTH:]
            if line:
                await query.message.reply_text(line.strip())
            continue

        if len(chunk) + len(line) + 2 <= MAX_LENGTH:
            chunk += line + "\n\n"
        else:
            await query.message.reply_text(chunk.strip())
            chunk = line + "\n\n"

    if chunk:
        await query.message.reply_text(chunk.strip())


# 검색 함수들
async def search_rsi(user_id: int):
    """제품 검색 함수"""
    # 실제 데이터베이스 쿼리나 API 호출 로직 구현
    # 예시 데이터
    await asyncio.sleep(1)  # 검색 시뮬레이션

    # 사용자 ID를 기반으로 개인화된 검색 결과 반환 가능
    logger.info(f"Searching rsi for user {user_id}")

    df = rsi_scan()
    message = format_rsi_message(df)

    return message


async def search_lower_shadow(user_id: int):
    """사용자 검색 함수"""
    await asyncio.sleep(1)

    logger.info(f"Searching users for user {user_id}")

    df = long_lower_shadow_scan()
    message = format_shadow_message(df)

    return message


async def search_52week_high_price(user_id: int):
    """주문 검색 함수"""
    await asyncio.sleep(1)

    logger.info(f"Searching orders for user {user_id}")

    df = run_new_high_scan()
    message = format_new_high_message(df)

    return message


# 에러 처리
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """에러 처리"""
    logger.error(f"Update {update} caused error {context.error}")


# 메인 함수
def main():
    """메인 함수"""
    # 애플리케이션 생성
    application = Application.builder().token(BOT_TOKEN).build()

    # 핸들러 등록
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # 에러 핸들러 등록
    application.add_error_handler(error_handler)

    # 봇 실행
    logger.info("텔레그램 봇이 시작되었습니다...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()