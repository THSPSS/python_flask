from flask import Flask, jsonify , request
from threading import Thread
from utils.telegram import background_search_and_notify

app = Flask(__name__)


@app.route("/")
def home():
    return "✅ Flask server is running!"


@app.route("/search", methods=["GET"])
def search():
    chat_id = request.args.get("chat_id")
    code = request.args.get("code")  # "1", "2", etc.

    if not chat_id or not code:
        return jsonify({"error": "chat_id와 code 파라미터가 필요합니다."}), 400

    Thread(target=background_search_and_notify, args=(chat_id, code)).start()
    return jsonify({"message": "🔍 검색을 시작했습니다. 결과는 텔레그램으로 전송됩니다."})



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)