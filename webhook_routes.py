import os

from dotenv import load_dotenv
from flask import request
from threading import Thread
from utils.telegram import background_search_and_notify, send_to_telegram
import json

load_dotenv()

BOT_TOKENS = json.loads(os.getenv("BOT_TOKENS"))

def register_webhook_routes(app):

    @app.route('/webhook/<botname>', methods=['POST'])
    def handle_webhook(botname):
        token = BOT_TOKENS.get(botname)
        if not token:
            return f"❌ 확인되지 않은 봇입니다 : {botname}", 404
        print(f"webhook token check: {token}")

        data = request.json
        message = data.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        user_text = message.get('text', '').strip()

        if not chat_id or not user_text:
            return "❌ 메시지 포맷을 다시 확인해주세요", 400

        if "1" in user_text:
            res_text = "📈 RSI 검색을 시작했어요!"
        elif "2" in user_text:
            res_text = "💧 아래꼬리 패턴 검색 중입니다!"
        elif "3" in user_text:
            res_text = "📊 52주 신고가 검색을 시작했어요!"
        else :
            res_text = "❌ 지원하지 않는 코드입니다.\n\n1: RSI 검색\n2: 아래꼬리 검색\n3: 52주 신고가 검색 중 선택하여 입력해주세요."
            send_to_telegram(token, chat_id, res_text)
            return "❌ 유효하지 않은 요청", 200

        # ✅ 유효한 코드일 경우 안내 메시지 + 백그라운드 시작
        res_text += "\n\n검색 완료 후 결과를 보내드릴게요."

        send_to_telegram(token, chat_id, res_text)

        # ✅ Background 처리
        Thread(target=background_search_and_notify, args=(token, chat_id, user_text)).start()

        return "✅ 검색이 시작되었습니다. 결과는 텔레그램으로 다시 전송됩니다.", 200