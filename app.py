import os
from utils.cache_utils import refresh_cache_if_needed
from dotenv import load_dotenv
from flask import Flask, jsonify , request
from threading import Thread
from utils.telegram import background_search_and_notify
#웹 훅(사용 정지)
# from webhook_routes import register_webhook_routes

app = Flask(__name__)

#기본 토큰값 불러오기
load_dotenv()

TOKEN = os.getenv("TOKEN")

RESEARCHES = ['rsi', 'long-lower-shadow','52weeks']

@app.route("/")
def home():
    return "✅ Flask server is running!"


@app.route("/search", methods=["GET"])
def search():
    #1일 1번 종목명 + 종목코드 가져오기
    refresh_cache_if_needed()

    chat_id = request.args.get("chat_id")
    code = request.args.get("code")  # "1", "2", etc.
    token = request.args.get("token") or TOKEN

    if not chat_id or not code or not token:
        return jsonify({"error": "필수 파라미터 chat_id , code , token 부족"}), 400

    # ✅ 숫자인 경우 +1 처리
    if code.isdigit():
        idx = int(code) - 1
        if 0 <= idx < len(RESEARCHES):
            code = RESEARCHES[idx]
        else:
            return jsonify({"error": f"유효하지 않은 index: {idx}"}), 400

    Thread(target=background_search_and_notify, args=(token, chat_id, code)).start()
    return jsonify({"message": "🔍 검색을 시작했습니다. 결과는 텔레그램으로 전송됩니다."})

# ✅ Register webhook routes
# register_webhook_routes(app)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000 , debug=True)