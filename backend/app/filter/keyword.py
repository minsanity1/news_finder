from typing import List, Optional
from dataclasses import dataclass


@dataclass
class KeywordFilterConfig:
    include_keywords: List[str]
    exclude_keywords: List[str]
    match_any: bool = True  # True: OR 조건, False: AND 조건


# 기본 키워드 프리셋
DEFAULT_INCLUDE_KEYWORDS = {
    "failure": ["파산", "폐업", "적자", "매각", "철수", "구조조정", "몰락", "위기", "추락", "실패", "적자전환", "손실"],
    "success": ["흥행", "대박", "매출 급등", "성장", "돌풍", "떡상", "히트", "성공", "1위", "신기록", "급성장", "흑자"],
    "comeback": ["턴어라운드", "회생", "부활", "재기", "흑자전환", "V자 반등", "회복", "재도약"],
    "brand": ["브랜드", "기업", "회사", "제품", "서비스", "프랜차이즈", "스타트업", "법인"],
}

DEFAULT_EXCLUDE_KEYWORDS = ["광고", "후원", "포토", "영상", "화보", "포토뉴스", "[AD]", "스폰서"]


class KeywordFilter:
    def __init__(
        self,
        include_keywords: Optional[List[str]] = None,
        exclude_keywords: Optional[List[str]] = None
    ):
        self.include_keywords = include_keywords or []
        self.exclude_keywords = exclude_keywords or DEFAULT_EXCLUDE_KEYWORDS

    def _contains_any(self, text: str, keywords: List[str]) -> bool:
        """텍스트에 키워드 중 하나라도 포함되어 있는지 확인"""
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in keywords)

    def _contains_all(self, text: str, keywords: List[str]) -> bool:
        """텍스트에 모든 키워드가 포함되어 있는지 확인"""
        text_lower = text.lower()
        return all(keyword.lower() in text_lower for keyword in keywords)

    def filter_single(
        self,
        title: str,
        summary: str = "",
        match_any: bool = True
    ) -> bool:
        """
        단일 뉴스 필터링

        Returns:
            True: 필터 통과 (보여줄 뉴스)
            False: 필터 제외 (숨길 뉴스)
        """
        combined_text = f"{title} {summary}"

        # 제외 키워드 확인 (하나라도 있으면 제외)
        if self.exclude_keywords:
            if self._contains_any(combined_text, self.exclude_keywords):
                return False

        # 포함 키워드 확인
        if self.include_keywords:
            if match_any:
                return self._contains_any(combined_text, self.include_keywords)
            else:
                return self._contains_all(combined_text, self.include_keywords)

        # 포함 키워드가 없으면 모두 통과
        return True

    def filter_many(
        self,
        news_list: List[dict],
        match_any: bool = True
    ) -> List[dict]:
        """여러 뉴스 필터링"""
        return [
            news for news in news_list
            if self.filter_single(
                news.get("title", ""),
                news.get("summary", ""),
                match_any
            )
        ]

    def get_matching_keywords(self, text: str) -> List[str]:
        """텍스트에서 매칭된 키워드 목록 반환"""
        text_lower = text.lower()
        return [
            keyword for keyword in self.include_keywords
            if keyword.lower() in text_lower
        ]


def get_preset_keywords(preset_type: str) -> List[str]:
    """프리셋 타입에 따른 키워드 반환"""
    return DEFAULT_INCLUDE_KEYWORDS.get(preset_type, [])


def get_combined_keywords(*preset_types: str) -> List[str]:
    """여러 프리셋 타입의 키워드 결합"""
    keywords = []
    for preset_type in preset_types:
        keywords.extend(get_preset_keywords(preset_type))
    return list(set(keywords))  # 중복 제거
