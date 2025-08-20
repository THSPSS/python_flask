import os
from datetime import datetime, timedelta
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup
import yfinance as yf

import holidays
from dotenv import load_dotenv

from utils.telegram import send_to_telegram

load_dotenv()
TOKEN = os.getenv("AI_SMART_TOKEN")
KR_CHANNEL_ID = os.getenv("KR_CHANNEL_ID")
US_CHANNEL_ID = os.getenv("US_CHANNEL_ID")


def get_prev_and_current(symbol):
    t = yf.Ticker(symbol)
    try:
        fi = t.fast_info  # last_price / previous_close가 빨리 뜸
        prev_c = fi.get('previous_close', None)
        last_p = fi.get('last_price', None)
        if prev_c and last_p:
            return float(prev_c), float(last_p)
    except Exception:
        pass
    # 폴백: 룩백 확장해서 마지막 유효 2개 종가
    return get_last_two_closes(symbol, lookback_days=21)


def get_last_two_closes(symbol, lookback_days=14):
    df = yf.download(symbol, period=f'{lookback_days}d', interval='1d', auto_adjust=False, progress=False)
    if df is None or df.empty or 'Close' not in df:
        return None
    closes = df['Close'].dropna()
    # 혹시 같은 날짜가 중복되면 마지막만 남기기 (안전장치)
    closes = closes[~closes.index.duplicated(keep='last')]
    if len(closes) < 2:
        return None
    return float(closes.iloc[-2]), float(closes.iloc[-1])

def is_korean_holiday(date=None):
    if date is None:
        date = datetime.today().date()
    return date in holidays.KR()

def is_us_market_holiday_kst():
    # 오늘 한국 날짜 기준으로 미국은 어제였음
    us_yesterday = (datetime.today() - timedelta(days=1)).date()
    return us_yesterday in holidays.US()

def format_market_report():
    today = datetime.today()
    date_str = today.strftime("%Y년 %-m월 %-d일") if os.name != 'nt' else today.strftime("%Y년 %#m월 %#d일")

    is_kr_holiday_flag = is_korean_holiday()
    is_us_holiday_flag = is_us_market_holiday_kst()

    data = get_finance_data()
    kr_news = get_kr_top_news() if not is_kr_holiday_flag else []
    world_news = get_world_top_news() if not is_us_holiday_flag else []

    kr_report, us_report = None, None

    if not is_kr_holiday_flag:
        kr_title = f"🇰🇷 {date_str} 한국주식"
        kr_body = "📊 한국 주요 지수:\n"
        for name in ['코스피', '코스닥', '코스피200']:
            info = data.get(name)
            if isinstance(info, dict):
                sign = "+" if info["diff"] >= 0 else ""
                kr_body += f" - {name}: {info['current']} ({sign}{info['diff']}, {sign}{info['ratio']}%)\n"
            else:
                kr_body += f" - {name}: {info}\n"

        kr_body += "\n📰 한국 주요 뉴스:\n"
        for i, (title, url) in enumerate(kr_news, 1):
            kr_body += f" {i}. {title}\n    👉 {url}\n"

        kr_report = f"{kr_title}\n\n{kr_body.strip()}"

    if not is_us_holiday_flag:
        us_title = f"🇺🇸 {date_str} 미국주식"
        us_body = "📊 미국 주요 지수:\n"
        for name in ['다우존스', '나스닥', 'S&P500']:
            info = data.get(name)
            if isinstance(info, dict):
                sign = "+" if info["diff"] >= 0 else ""
                us_body += f" - {name}: {info['current']} ({sign}{info['diff']}, {sign}{info['ratio']}%)\n"
            else:
                us_body += f" - {name}: {info}\n"

        us_body += "\n📰 미국 주요 뉴스:\n"
        for i, (title, url) in enumerate(world_news, 1):
            us_body += f" {i}. {title}\n    👉 {url}\n"

        us_report = f"{us_title}\n\n{us_body.strip()}"

    return kr_report, us_report

def get_finance_data():
    tickers = {
        '코스피': '^KS11',
        '코스닥': '^KQ11',
        '코스피200': '^KS200',
        '다우존스': '^DJI',
        '나스닥': '^IXIC',
        'S&P500': '^GSPC'
    }

    results = {}

    for name, symbol in tickers.items():
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period='2d')  # 전일 + 오늘 데이터
            if hist.shape[0] < 2:
                results[name] = "데이터 부족"
                continue

            prev_close = hist['Close'].iloc[-2]
            current = hist['Close'].iloc[-1]
            diff = current - prev_close
            ratio = (diff / prev_close) * 100

            results[name] = {
                "current": round(current, 2),
                "diff": round(diff, 2),
                "ratio": round(ratio, 2)
            }

        except Exception as e:
            results[name]    = f"오류 발생: {e}"

    return results
    #---------백업
    # try:
    #     pair = get_prev_and_current(symbol)
    #     if not pair:
    #         # 한 번 더 재시도: 아주 짧은 지연이었을 수 있음
    #         pair = get_last_two_closes(symbol, lookback_days=30)
    #     if not pair:
    #         results[name] = "데이터 부족"
    #         continue
    #
    #     prev_close, current = pair
    #     diff = current - prev_close
    #     ratio = (diff / prev_close) * 100
    #
    #     results[name] = {
    #         "current": round(current, 2),
    #         "diff": round(diff, 2),
    #         "ratio": round(ratio, 2)
    #     }
    # except Exception as e:
    #     results[name] = f"에러: {e}"
    #
    # return results

def get_kr_top_news():
    url = "https://finance.naver.com/"
    headers = {"User-Agent": "Mozilla/5.0"}  # 크롤링 차단 방지용
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    # 주요 뉴스 영역 찾기
    ul_tag = soup.select_one('#content > div.article > div.section > div.news_area._replaceNewsLink > div > ul')
    if not ul_tag:
        print("❌ 주요 뉴스 영역을 찾지 못했습니다.")
        return []

    news_list = []
    for a_tag in ul_tag.select("li > span > a"):
        title = a_tag.text.strip()
        relative_link = a_tag['href'].strip()
        # 링크 파싱 후 커스텀 뉴스 URL 생성
        parsed = urlparse(relative_link)
        query = parse_qs(parsed.query)
        office_id = query.get("office_id", [""])[0]
        article_id = query.get("article_id", [""])[0]
        news_url = f"https://n.news.naver.com/article/{office_id}/{article_id}"
        news_list.append((title, news_url))

    return news_list

def get_world_top_news():
    url = "https://finance.naver.com/world"
    headers = {"User-Agent": "Mozilla/5.0"}  # 크롤링 차단 방지용
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, "html.parser")

    # 주요 뉴스 영역 찾기
    ul_tag = soup.select_one('#content > div.section_news._replaceNewsLink > div > ul')
    if not ul_tag:
        print("❌ 주요 뉴스 영역을 찾지 못했습니다.")
        return []

    news_list = []
    for a_tag in ul_tag.select("li > p > a"):
        title = a_tag.text.strip()
        link = a_tag['href'].strip()
        full_url = link if link.startswith("http") else f"https://finance.naver.com{link}"
        news_list.append((title, full_url))

    return news_list


# 테스트 실행
if __name__ == "__main__":

    kr_report, us_report = format_market_report()
    if kr_report is not None:
        print("✅ 한국 리포트 전송 준비 중...")
        print(kr_report)
        send_to_telegram(TOKEN, KR_CHANNEL_ID, kr_report)
        # upload_to_blog(kr_report)

    if us_report is not None:
        print("✅ 미국 리포트 전송 준비 중...")
        print(us_report)
        send_to_telegram(TOKEN, US_CHANNEL_ID, us_report)
        # upload_to_blog(us_report)
