import aiohttp
import urllib.parse
from datetime import datetime
from typing import Optional
import re

from app.config import get_settings

settings = get_settings()

NAVER_SEARCH_URL = "https://openapi.naver.com/v1/search/news.json"


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text"""
    if not text:
        return ""
    clean = re.sub(r'<[^>]+>', '', text)
    clean = clean.replace('&quot;', '"').replace('&amp;', '&')
    clean = clean.replace('&lt;', '<').replace('&gt;', '>')
    clean = clean.replace('&apos;', "'")
    return clean.strip()


def parse_naver_date(date_str: str) -> Optional[datetime]:
    """Parse Naver API date format (RFC 822)
    Example: 'Mon, 30 Dec 2024 10:30:00 +0900'
    """
    try:
        # Remove timezone for parsing
        date_str = re.sub(r'\s*[+-]\d{4}$', '', date_str)
        return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S')
    except Exception:
        return None


class NaverNewsCollector:
    def __init__(self):
        self.client_id = settings.naver_client_id
        self.client_secret = settings.naver_client_secret

    def is_configured(self) -> bool:
        return settings.has_naver_api()

    async def search(
        self,
        query: str,
        display: int = 100,  # 한 번에 가져올 개수 (최대 100)
        start: int = 1,      # 시작 위치 (1~1000)
        sort: str = "date"   # date: 최신순, sim: 정확도순
    ) -> dict:
        """네이버 뉴스 검색 API 호출"""
        if not self.is_configured():
            return {"error": "Naver API not configured", "items": []}

        headers = {
            "X-Naver-Client-Id": self.client_id,
            "X-Naver-Client-Secret": self.client_secret
        }

        params = {
            "query": query,
            "display": min(display, 100),
            "start": min(start, 1000),
            "sort": sort
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    NAVER_SEARCH_URL,
                    headers=headers,
                    params=params
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        error_text = await response.text()
                        return {
                            "error": f"API error: {response.status}",
                            "detail": error_text,
                            "items": []
                        }
        except Exception as e:
            return {"error": str(e), "items": []}

    async def search_and_collect(
        self,
        query: str,
        max_results: int = 100,
        sort: str = "date"
    ) -> list[dict]:
        """검색 후 뉴스 데이터 형식으로 변환"""
        all_items = []
        start = 1

        while len(all_items) < max_results:
            display = min(100, max_results - len(all_items))
            result = await self.search(query, display=display, start=start, sort=sort)

            if "error" in result and result["error"]:
                print(f"[Naver Collector] Error: {result['error']}")
                break

            items = result.get("items", [])
            if not items:
                break

            for item in items:
                news_item = {
                    "title": strip_html_tags(item.get("title", "")),
                    "summary": strip_html_tags(item.get("description", "")),
                    "url": item.get("originallink") or item.get("link", ""),
                    "source": "네이버 뉴스",
                    "category": "검색",
                    "published_at": parse_naver_date(item.get("pubDate", ""))
                }
                all_items.append(news_item)

            start += len(items)
            if start > 1000:  # Naver API limit
                break

        return all_items[:max_results]

    async def search_multiple_keywords(
        self,
        keywords: list[str],
        max_per_keyword: int = 50,
        sort: str = "date"
    ) -> list[dict]:
        """여러 키워드로 검색하여 결과 합치기"""
        all_items = []
        seen_urls = set()

        for keyword in keywords:
            items = await self.search_and_collect(
                keyword,
                max_results=max_per_keyword,
                sort=sort
            )

            for item in items:
                if item["url"] not in seen_urls:
                    seen_urls.add(item["url"])
                    all_items.append(item)

        return all_items


def get_naver_collector() -> NaverNewsCollector:
    return NaverNewsCollector()
