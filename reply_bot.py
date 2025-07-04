import asyncio
import logging
import os

from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from scans.long_shadow_scan import long_lower_shadow_scan, format_shadow_message
from scans.new_high_scan import run_new_high_scan, format_new_high_message
from scans.rsi_scan import format_rsi_message, rsi_scan


load_dotenv()

# 로깅 설정
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 봇 토큰 설정
BOT_TOKEN = os.getenv('STOCK_STUDY_TOKEN')

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
        [InlineKeyboardButton("📈 RSI 검색", callback_data='rsi')],
        [InlineKeyboardButton("💧 아래꼬리 검색", callback_data='lower-shadow')],
        [InlineKeyboardButton("📊 52주 신고가", callback_data='52w')]
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
    """사용자가 선택한 검색 옵션 처리"""
    # 사용자 상태 업데이트
    user_states[user_id] = 'searching'

    search_options = {
        'rsi': {
            'type': 'rsi',
            'message': '📈 RSI 분석 검색하고 있습니다...'
        },
        'lower-shadow': {
            'type': 'lower-shadow',
            'message': '💧 아래꼬리 검색하고 있습니다...'
        },
        '52w': {
            'type': '52w',
            'message': '📊 52주 신고가 검색하고 있습니다...'
        }
    }

    if selected_option in search_options:
        option_info = search_options[selected_option]

        # 검색 시작 메시지
        await query.edit_message_text(option_info['message'])

        # 실제 검색 수행
        await perform_search(query, user_id, option_info['type'])
    else:
        await query.edit_message_text("잘못된 선택입니다. /start 를 다시 입력해주세요.")
        if user_id in user_states:
            del user_states[user_id]


# 검색 수행
async def perform_search(query, user_id: int, search_type: str):
    """실제 검색 수행"""
    try:
        logger.info(f"Starting search for user {user_id}, type: {search_type}")

        # 검색 함수 매핑
        search_functions = {
            'rsi': search_rsi,
            'lower-shadow': search_lower_shadow,
            '52w': search_52week_high_price
        }

        if search_type in search_functions:
            # 해당 검색 함수 호출
            result_message = await search_functions[search_type](user_id)

            # 검색 결과 전송
            if result_message:
                # result_message = f"검색 결과 ({len(results)}개):\n\n"
                # for i, item in enumerate(results, 1):
                #     result_message += f"{i}. {item['name']} - {item['description']}\n"

                await query.message.reply_text(result_message)
            # else:
            #     await query.message.reply_text("검색 결과가 없습니다.")
        else:
            await query.message.reply_text("지원하지 않는 검색 유형입니다.")

        # 사용자 상태 리셋
        if user_id in user_states:
            del user_states[user_id]

        # 다시 시작할 수 있도록 안내
        await asyncio.sleep(1)
        await query.message.reply_text("새로운 검색을 원하시면 /start 를 입력해주세요.")

    except Exception as e:
        logger.error(f"Search error for user {user_id}: {e}")
        await query.message.reply_text("검색 중 오류가 발생했습니다. 다시 /start 명령어로 시도해주세요.")
        if user_id in user_states:
            del user_states[user_id]


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