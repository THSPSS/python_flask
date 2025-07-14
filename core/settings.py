EXCLUDE_KEYWORDS = [
    'ETN','KODEX','TIGER','KBSTAR','KOSEF','HANARO','ARIRANG',
    'FOCUS','스팩','SOL','RISE','BNK','우','1우','2우','3우',
    '우B','우C','우선주','KOACT',"KIWOOM","지주","ACE", "PLUS","50","200",
    "액티브"
]

WEEKDAY_MAP = ['월', '화', '수', '목', '금', '토', '일']
RESEARCHES = [
    'rsi', 'long-lower-shadow','52weeks' ,
    "us-rsi",
    "us-long-lower-shadow",
    "us-52weeks"
]

RSI_PERIOD = 14 #RSI 검색을 위한 일수
MIN_CANDLE_COUNT = 23 #최소 종가 count
RISE_THRESHOLD = 3  # 어제 대비 오늘 증가 %
MAX_LENGTH = 4000