from flask import Flask, jsonify
from datetime import datetime
from main import scan  # 위 코드의 파일명이 main.py일 경우


app = Flask(__name__)

@app.route("/rsi-scan", methods=["GET"])
def run_scan():
    print("SCAN ON")
    df = scan()

    if df.empty:
        return jsonify({"message": "❗조건을 만족하는 종목이 없습니다."})

    summary = "\n\n".join([
        f"🔹 {row['종목명']} ({row['종목코드']})\n📈 상승률: {row['상승률%']}%\nRSI: {row['어제RSI']} > {row['최저RSI']}"
        for _, row in df.iterrows()
    ])

    return jsonify({
        "message": f"📊 {datetime.now().strftime('%Y-%m-%d')} RSI 조건 종목 목록\n\n{summary}"
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)