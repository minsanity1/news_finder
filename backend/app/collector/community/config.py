"""
커뮤니티 수집 설정
"""

# 커뮤니티별 게시판 설정
COMMUNITY_BOARDS = {
    "fmkorea": {
        "name": "에펨코리아",
        "enabled": True,
        "boards": [
            {"id": "핫이슈", "path": "index.php?mid=best", "priority": 1, "collect_limit": 30},
            {"id": "유머", "path": "index.php?mid=humor", "priority": 2, "collect_limit": 20},
            {"id": "자유", "path": "index.php?mid=free", "priority": 3, "collect_limit": 20},
        ],
        "collect_interval_minutes": 30,
    },
    "ppomppu": {
        "name": "뽐뿌",
        "enabled": True,
        "boards": [
            {"id": "핫딜", "path": "zboard/zboard.php?id=ppomppu", "priority": 1, "collect_limit": 30},
            {"id": "자유게시판", "path": "zboard/zboard.php?id=freeboard", "priority": 2, "collect_limit": 20},
        ],
        "collect_interval_minutes": 30,
    },
    "clien": {
        "name": "클리앙",
        "enabled": False,  # Phase 2-B
        "boards": [
            {"id": "모두의공원", "path": "service/board/park", "priority": 1, "collect_limit": 30},
            {"id": "새로운소식", "path": "service/board/news", "priority": 2, "collect_limit": 20},
        ],
        "collect_interval_minutes": 60,
    },
    "theqoo": {
        "name": "더쿠",
        "enabled": False,  # Phase 2-B
        "boards": [
            {"id": "이슈", "path": "hot", "priority": 1, "collect_limit": 30},
        ],
        "collect_interval_minutes": 30,
    },
    "dcinside": {
        "name": "디시인사이드",
        "enabled": False,  # Phase 2-C
        "boards": [
            {"id": "실시간베스트", "path": "board/lists?id=dcbest", "priority": 1, "collect_limit": 50},
        ],
        "collect_interval_minutes": 15,
    },
}

# 수집 제외 키워드 (광고, 스팸 필터링)
EXCLUDE_TITLE_PATTERNS = [
    r"^\[광고\]",
    r"^\[AD\]",
    r"^광고\s",
    r"텔레그램",
    r"카톡.*문의",
    r"^\[구인\]",
    r"^\[구매\]",
    r"^\[판매\]",
    r"사이트.*추천",
    r"무료\s*체험",
    r"이벤트\s*참여",
]

# 수집 우선 키워드 (바이럴 가능성 높음)
PRIORITY_KEYWORDS = [
    # 바이럴 트리거
    "레전드", "ㄹㅇ", "실화", "충격", "논란", "대참사",
    # 비즈니스 스토리
    "폐업", "망한", "대박", "떡상", "역대급", "매출",
    # 가격/소비
    "가격", "인상", "인하", "무료", "할인", "가성비",
    # 프랜차이즈/외식
    "치킨", "커피", "배달", "프랜차이즈", "편의점", "마트",
    # 브랜드
    "교촌", "BBQ", "노랑통닭", "스타벅스", "맥도날드",
    "롯데", "이마트", "쿠팡", "배민", "당근마켓",
]


def get_enabled_boards() -> dict:
    """활성화된 커뮤니티와 게시판 목록 반환"""
    return {
        source_id: config
        for source_id, config in COMMUNITY_BOARDS.items()
        if config["enabled"]
    }


def get_board_config(source_id: str, board_id: str) -> dict | None:
    """특정 게시판 설정 반환"""
    if source_id not in COMMUNITY_BOARDS:
        return None

    for board in COMMUNITY_BOARDS[source_id]["boards"]:
        if board["id"] == board_id:
            return board

    return None
