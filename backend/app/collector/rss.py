import asyncio
import feedparser
import httpx
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass
import html
import re

from app.collector.sources import RSSSource, get_enabled_sources
from app.config import get_settings

settings = get_settings()


@dataclass
class CollectedNews:
    title: str
    summary: Optional[str]
    url: str
    source: str
    category: str
    published_at: Optional[datetime]


class RSSCollector:
    def __init__(self):
        self.timeout = 30
        self.max_news_per_source = settings.max_news_per_source

    def _clean_html(self, text: str) -> str:
        """HTML 태그 및 엔티티 제거"""
        if not text:
            return ""
        # HTML 엔티티 디코딩
        text = html.unescape(text)
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        # 여러 공백을 하나로
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def _parse_date(self, entry: dict) -> Optional[datetime]:
        """feedparser 엔트리에서 날짜 추출"""
        if hasattr(entry, 'published_parsed') and entry.published_parsed:
            try:
                return datetime(*entry.published_parsed[:6])
            except Exception:
                pass

        if hasattr(entry, 'updated_parsed') and entry.updated_parsed:
            try:
                return datetime(*entry.updated_parsed[:6])
            except Exception:
                pass

        return None

    async def _fetch_feed(self, source: RSSSource) -> List[CollectedNews]:
        """단일 RSS 피드 수집"""
        news_list = []

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    source.url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (compatible; NewsCollector/1.0)"
                    },
                    follow_redirects=True
                )
                response.raise_for_status()

            feed = feedparser.parse(response.text)

            for entry in feed.entries[:self.max_news_per_source]:
                # 제목
                title = self._clean_html(entry.get('title', ''))
                if not title:
                    continue

                # URL
                url = entry.get('link', '')
                if not url:
                    continue

                # 요약
                summary = ""
                if 'summary' in entry:
                    summary = self._clean_html(entry.summary)
                elif 'description' in entry:
                    summary = self._clean_html(entry.description)

                # 요약이 너무 길면 자르기
                if len(summary) > 500:
                    summary = summary[:500] + "..."

                news = CollectedNews(
                    title=title,
                    summary=summary,
                    url=url,
                    source=source.name,
                    category=source.category,
                    published_at=self._parse_date(entry)
                )
                news_list.append(news)

        except httpx.TimeoutException:
            print(f"[RSS] Timeout: {source.name}")
        except httpx.HTTPStatusError as e:
            print(f"[RSS] HTTP Error {e.response.status_code}: {source.name}")
        except Exception as e:
            print(f"[RSS] Error collecting from {source.name}: {str(e)}")

        return news_list

    async def collect_all(self) -> List[CollectedNews]:
        """모든 활성 소스에서 뉴스 수집"""
        sources = get_enabled_sources()
        all_news = []

        # 동시에 모든 소스에서 수집
        tasks = [self._fetch_feed(source) for source in sources]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        for result in results:
            if isinstance(result, list):
                all_news.extend(result)
            elif isinstance(result, Exception):
                print(f"[RSS] Collection error: {str(result)}")

        print(f"[RSS] Collected {len(all_news)} news from {len(sources)} sources")
        return all_news

    async def collect_from_source(self, source_name: str) -> List[CollectedNews]:
        """특정 소스에서만 뉴스 수집"""
        sources = get_enabled_sources()
        source = next((s for s in sources if s.name == source_name), None)

        if not source:
            return []

        return await self._fetch_feed(source)


def collected_news_to_dict(news: CollectedNews) -> dict:
    """CollectedNews를 딕셔너리로 변환"""
    return {
        "title": news.title,
        "summary": news.summary,
        "url": news.url,
        "source": news.source,
        "category": news.category,
        "published_at": news.published_at,
    }
