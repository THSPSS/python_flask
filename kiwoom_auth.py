# kiwoom_auth.py
from dotenv import load_dotenv
import requests
import os


load_dotenv()

APP_KEY    = os.getenv("KIWOOM_APP_KEY")
SECRET_KEY = os.getenv("KIWOOM_SECRET_KEY")


def get_token() -> str:
    url = "https://api.kiwoom.com/oauth2/token"
    payload = {
        "grant_type": "client_credentials",
        "appkey": APP_KEY,
        "secretkey": SECRET_KEY
    }
    r = requests.post(url, json=payload, timeout=10)
    print("🔍 토큰 응답 내용:", r.status_code, r.text)  # 이 줄 추가
    r.raise_for_status()
    return r.json()["token"]
