"""
네이버 뉴스 랭킹 수집기

URL 패턴: https://media.naver.com/press/{언론사ID}/ranking?type={정렬타입}&date={날짜}
- type=popular: 조회수 순
- type=comment: 댓글수 순
- date=YYYYMMDD
"""
import asyncio
import random
import re
from dataclasses import dataclass, asdict
from datetime import datetime, date
from typing import Optional, List

import httpx
from bs4 import BeautifulSoup

from .ranking_config import (
    PRESS_LIST,
    PRESS_MAP,
    RANKING_TYPES,
    SCRAPING_CONFIG,
    PressInfo,
)


@dataclass
class RankingNews:
    """랭킹 뉴스 데이터"""
    rank: int                      # 순위 (1~10)
    title: str
    url: str
    source: str                    # 언론사명
    source_id: str                 # 언론사 ID
    category: str                  # 언론사 카테고리
    ranking_type: str              # "popular" | "comment"
    ranking_date: date             # 랭킹 기준 날짜
    view_count: Optional[int] = None
    comment_count: Optional[int] = None
    thumbnail_url: Optional[str] = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["ranking_date"] = self.ranking_date.isoformat()
        return d


class NaverRankingCollector:
    """네이버 뉴스 랭킹 수집기"""

    BASE_URL = "https://media.naver.com/press/{press_id}/ranking"

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=SCRAPING_CONFIG["timeout"],
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": "https://media.naver.com/",
            },
            follow_redirects=True
        )

    async def _request_with_retry(
        self,
        url: str,
        max_retry: int = None
    ) -> httpx.Response:
        """재시도 로직이 포함된 요청"""
        max_retry = max_retry or SCRAPING_CONFIG["max_retries"]
        last_err = None

        for attempt in range(1, max_retry + 1):
            try:
                delay = random.uniform(*SCRAPING_CONFIG["request_delay"])
                await asyncio.sleep(delay)

                resp = await self.client.get(url)
                if resp.status_code == 200 and resp.text:
                    return resp
                last_err = RuntimeError(f"Bad status {resp.status_code}")
            except Exception as e:
                last_err = e

            # 지수 백오프
            await asyncio.sleep(random.uniform(0.5, 1.0) * attempt)

        raise last_err

    async def get_ranking(
        self,
        press_id: str,
        ranking_type: str = "popular",
        target_date: Optional[date] = None,
        limit: int = 10
    ) -> List[RankingNews]:
        """
        특정 언론사의 랭킹 뉴스 수집

        Args:
            press_id: 언론사 ID (예: "009")
            ranking_type: "popular" (조회수) 또는 "comment" (댓글수)
            target_date: 수집 날짜 (기본: 오늘)
            limit: 수집 개수 (기본: 10, 최대: 30)

        Returns:
            RankingNews 리스트
        """
        if press_id not in PRESS_MAP:
            raise ValueError(f"Unknown press_id: {press_id}")

        if ranking_type not in RANKING_TYPES:
            raise ValueError(f"Unknown ranking_type: {ranking_type}")

        press_info = PRESS_MAP[press_id]
        target_date = target_date or date.today()
        date_str = target_date.strftime("%Y%m%d")

        url = f"{self.BASE_URL.format(press_id=press_id)}?type={ranking_type}&date={date_str}"
        print(f"[Ranking] Fetching: {url}")

        try:
            response = await self._request_with_retry(url)
        except Exception as e:
            print(f"[Ranking] Failed to fetch {url}: {e}")
            return []

        return self._parse_ranking_page(
            html=response.text,
            press_info=press_info,
            ranking_type=ranking_type,
            ranking_date=target_date,
            limit=limit
        )

    def _parse_ranking_page(
        self,
        html: str,
        press_info: PressInfo,
        ranking_type: str,
        ranking_date: date,
        limit: int
    ) -> List[RankingNews]:
        """랭킹 페이지 HTML 파싱"""
        soup = BeautifulSoup(html, "lxml")
        results = []

        # 네이버 미디어 랭킹 페이지 셀렉터들 (여러 패턴 시도)
        selectors = [
            # 현재 네이버 미디어 구조 (2024-2025)
            "ul.press_ranking_list > li",
            "div.press_ranking_list li",
            # 대안 구조들
            "div.ranking_list li",
            "ul.ranking_news li",
            "div.list_ranking li",
            # 일반적인 뉴스 목록 구조
            "ul.type_list li",
            "div.news_list li",
        ]

        ranking_items = []
        for selector in selectors:
            ranking_items = soup.select(selector)
            if ranking_items:
                print(f"[Ranking] Found {len(ranking_items)} items with selector: {selector}")
                break

        if not ranking_items:
            # 최후 수단: a 태그 중 article URL 패턴 찾기
            print("[Ranking] Trying fallback: article links")
            ranking_items = soup.select("a[href*='/article/']")

        for idx, item in enumerate(ranking_items[:limit], start=1):
            try:
                news = self._parse_ranking_item(
                    item=item,
                    rank=idx,
                    press_info=press_info,
                    ranking_type=ranking_type,
                    ranking_date=ranking_date
                )
                if news:
                    results.append(news)
            except Exception as e:
                print(f"[Ranking] Failed to parse item {idx}: {e}")
                continue

        print(f"[Ranking] Parsed {len(results)} news from {press_info.name}")
        return results

    def _parse_ranking_item(
        self,
        item,
        rank: int,
        press_info: PressInfo,
        ranking_type: str,
        ranking_date: date
    ) -> Optional[RankingNews]:
        """개별 랭킹 아이템 파싱"""

        # 제목 추출
        title_selectors = [
            "a.list_title",
            "strong.list_title",
            "a.news_tit",
            "span.title",
            "a",  # fallback
        ]

        title = ""
        link_elem = None

        for sel in title_selectors:
            elem = item.select_one(sel)
            if elem:
                title = elem.get_text(strip=True)
                if elem.name == "a":
                    link_elem = elem
                if title:
                    break

        if not title:
            return None

        # URL 추출
        if not link_elem:
            link_elem = item.select_one("a[href]")

        href = link_elem.get("href", "") if link_elem else ""

        if not href:
            return None

        # 전체 URL로 변환
        if href.startswith("/"):
            href = "https://media.naver.com" + href
        elif not href.startswith("http"):
            href = "https://n.news.naver.com/article/" + href

        # 조회수 추출
        view_count = self._extract_count(item, ["조회", "view", "읽음", "hit"])

        # 댓글수 추출
        comment_count = self._extract_count(item, ["댓글", "comment", "의견"])

        # 썸네일 추출
        thumb_elem = item.select_one("img")
        thumbnail_url = None
        if thumb_elem:
            thumbnail_url = thumb_elem.get("src") or thumb_elem.get("data-src")

        return RankingNews(
            rank=rank,
            title=title,
            url=href,
            source=press_info.name,
            source_id=press_info.id,
            category=press_info.category,
            ranking_type=ranking_type,
            ranking_date=ranking_date,
            view_count=view_count,
            comment_count=comment_count,
            thumbnail_url=thumbnail_url,
        )

    def _extract_count(self, item, keywords: List[str]) -> Optional[int]:
        """조회수/댓글수 숫자 추출"""
        text = item.get_text()

        for keyword in keywords:
            # "조회 1,234" 또는 "조회수 1234" 패턴
            pattern = rf'{keyword}\s*[수]?\s*[:\s]*([0-9,]+)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1).replace(",", ""))

        # 숫자만 있는 span 찾기
        for span in item.select("span.count, span.num, em.count, span.hit"):
            num_text = span.get_text(strip=True)
            num_clean = num_text.replace(",", "")
            if num_clean.isdigit():
                return int(num_clean)

        return None

    async def get_rankings_by_press_list(
        self,
        press_ids: Optional[List[str]] = None,
        ranking_type: str = "popular",
        target_date: Optional[date] = None,
        limit_per_press: int = 10
    ) -> List[RankingNews]:
        """
        여러 언론사의 랭킹 뉴스 일괄 수집

        Args:
            press_ids: 언론사 ID 리스트 (None이면 전체 활성화된 언론사)
            ranking_type: "popular" 또는 "comment"
            target_date: 수집 날짜
            limit_per_press: 언론사당 수집 개수

        Returns:
            모든 언론사의 RankingNews 리스트 (중복 URL 제거됨)
        """
        if press_ids is None:
            press_ids = [p.id for p in PRESS_LIST if p.enabled]

        all_news = []
        seen_urls = set()

        for press_id in press_ids:
            try:
                news_list = await self.get_ranking(
                    press_id=press_id,
                    ranking_type=ranking_type,
                    target_date=target_date,
                    limit=limit_per_press
                )

                for news in news_list:
                    if news.url not in seen_urls:
                        seen_urls.add(news.url)
                        all_news.append(news)

            except Exception as e:
                print(f"[Ranking] Failed to collect from {press_id}: {e}")
                continue

        return all_news

    async def get_all_rankings(
        self,
        press_ids: Optional[List[str]] = None,
        target_date: Optional[date] = None,
        limit_per_press: int = 10
    ) -> dict:
        """
        조회수 + 댓글수 랭킹 모두 수집

        Returns:
            {
                "popular": [RankingNews, ...],
                "comment": [RankingNews, ...]
            }
        """
        results = {}

        for ranking_type in RANKING_TYPES.keys():
            results[ranking_type] = await self.get_rankings_by_press_list(
                press_ids=press_ids,
                ranking_type=ranking_type,
                target_date=target_date,
                limit_per_press=limit_per_press
            )

        return results

    def to_news_dict(self, ranking_news: RankingNews) -> dict:
        """News 모델 저장용 딕셔너리로 변환"""
        return {
            "title": ranking_news.title,
            "summary": "",  # 상세 페이지에서 추출 필요
            "content": "",
            "url": ranking_news.url,
            "source": ranking_news.source,
            "category": ranking_news.category,
            "published_at": datetime.combine(ranking_news.ranking_date, datetime.min.time()),
            "view_count": ranking_news.view_count,
            "comment_count": ranking_news.comment_count,
            "source_type": "ranking",
        }

    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
