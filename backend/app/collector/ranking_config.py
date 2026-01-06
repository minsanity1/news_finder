"""
네이버 뉴스 랭킹 수집 설정
"""
from dataclasses import dataclass


@dataclass
class PressInfo:
    """언론사 정보"""
    id: str
    name: str
    category: str
    priority: int  # 1=높음, 2=중간, 3=낮음
    enabled: bool = True


# 언론사 목록 (21개)
PRESS_LIST: list[PressInfo] = [
    # 경제 (6개)
    PressInfo("009", "매일경제", "경제", 1),
    PressInfo("015", "한국경제", "경제", 1),
    PressInfo("016", "헤럴드경제", "경제", 1),
    PressInfo("018", "이데일리", "경제", 1),
    PressInfo("277", "아시아경제", "경제", 1),
    PressInfo("648", "비즈워치", "경제", 3),

    # 종합 (6개)
    PressInfo("023", "조선일보", "종합", 1),
    PressInfo("025", "중앙일보", "종합", 1),
    PressInfo("022", "세계일보", "종합", 2),
    PressInfo("005", "국민일보", "종합", 2),
    PressInfo("469", "한국일보", "종합", 2),
    PressInfo("119", "데일리안", "종합", 3),

    # 방송 (6개)
    PressInfo("055", "SBS", "방송", 1),
    PressInfo("214", "MBC", "방송", 1),
    PressInfo("056", "KBS", "방송", 2),
    PressInfo("057", "MBN", "방송", 2),
    PressInfo("448", "TV조선", "방송", 2),
    PressInfo("374", "SBS Biz", "경제/방송", 2),

    # IT/테크 (3개)
    PressInfo("030", "전자신문", "IT", 1),
    PressInfo("092", "지디넷코리아", "IT", 1),
    PressInfo("031", "아이뉴스24", "IT", 2),
]

# ID로 빠르게 조회
PRESS_MAP = {p.id: p for p in PRESS_LIST}

# 랭킹 타입
RANKING_TYPES = {
    "popular": "많이 본",      # 조회수 순
    "comment": "댓글 많은",    # 댓글수 순
}

# 스크래핑 설정
SCRAPING_CONFIG = {
    "request_delay": (1.0, 2.0),    # 요청 간 딜레이 (초)
    "max_retries": 3,
    "timeout": 30,
    "default_limit": 10,             # 언론사당 기본 수집 개수
}


def get_enabled_press() -> list[PressInfo]:
    """활성화된 언론사 목록"""
    return [p for p in PRESS_LIST if p.enabled]


def get_press_by_category(category: str) -> list[PressInfo]:
    """카테고리별 언론사 목록"""
    return [p for p in PRESS_LIST if p.category == category and p.enabled]


def get_press_by_priority(priority: int) -> list[PressInfo]:
    """우선순위별 언론사 목록"""
    return [p for p in PRESS_LIST if p.priority == priority and p.enabled]
