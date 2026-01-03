"""
커뮤니티 수집기 베이스 클래스
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, List
import asyncio
import random
import re

import httpx
from bs4 import BeautifulSoup

from .config import EXCLUDE_TITLE_PATTERNS


@dataclass
class CommunityPost:
    """커뮤니티 게시글 표준 형식 (News 모델과 호환)"""
    title: str
    summary: str              # 본문 앞부분 또는 전체
    content: str              # 전체 본문
    url: str                  # 원본 URL (중복 체크 기준)
    source: str               # "에펨코리아", "뽐뿌" 등
    category: str             # 게시판명 ("핫이슈", "자유게시판" 등)
    published_at: Optional[datetime] = None

    # 커뮤니티 전용 메타
    view_count: Optional[int] = None
    comment_count: Optional[int] = None
    like_count: Optional[int] = None
    author: Optional[str] = None

    def to_dict(self) -> dict:
        """딕셔너리로 변환"""
        return asdict(self)


class BaseCommunityCollector(ABC):
    """커뮤니티 수집기 추상 베이스 클래스"""

    SOURCE_NAME: str = ""     # "에펨코리아", "뽐뿌" 등
    BASE_URL: str = ""
    REQUEST_DELAY: tuple = (1.0, 2.0)  # 요청 간 딜레이 (초)

    def __init__(self):
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            },
            follow_redirects=True
        )

    async def _request_with_delay(self, url: str) -> httpx.Response:
        """딜레이 적용된 요청"""
        await asyncio.sleep(random.uniform(*self.REQUEST_DELAY))
        return await self.client.get(url)

    def _should_exclude(self, title: str) -> bool:
        """제외 패턴 확인 (광고, 스팸 등)"""
        for pattern in EXCLUDE_TITLE_PATTERNS:
            if re.search(pattern, title, re.IGNORECASE):
                return True
        return False

    @abstractmethod
    async def get_board_list(self, board_id: str, page: int = 1) -> List[dict]:
        """게시판 목록 가져오기 (제목, URL, 메타 정보)

        Returns:
            list[dict]: [{"title": str, "url": str, "view_count": int, ...}, ...]
        """
        pass

    @abstractmethod
    async def get_post_detail(self, post_url: str) -> CommunityPost:
        """게시글 상세 내용 가져오기"""
        pass

    async def get_hot_posts(
        self,
        board_id: str,
        limit: int = 20,
        fetch_detail: bool = True
    ) -> List[CommunityPost]:
        """핫글/인기글 수집

        Args:
            board_id: 게시판 ID
            limit: 수집할 개수
            fetch_detail: 상세 내용까지 가져올지 여부
        """
        post_list = await self.get_board_list(board_id, page=1)
        posts = []

        for item in post_list[:limit]:
            # 제외 패턴 확인
            if self._should_exclude(item.get("title", "")):
                continue

            if fetch_detail:
                try:
                    post = await self.get_post_detail(item["url"])
                    post.category = board_id
                    posts.append(post)
                except Exception as e:
                    print(f"[{self.SOURCE_NAME}] Failed to fetch {item['url']}: {e}")
                    continue
            else:
                # 목록 정보만으로 CommunityPost 생성
                posts.append(CommunityPost(
                    title=item.get("title", ""),
                    summary="",
                    content="",
                    url=item.get("url", ""),
                    source=self.SOURCE_NAME,
                    category=board_id,
                    view_count=item.get("view_count"),
                    comment_count=item.get("comment_count"),
                ))

        return posts

    def to_news_dict(self, post: CommunityPost) -> dict:
        """News 모델 저장용 딕셔너리로 변환"""
        return {
            "title": post.title,
            "summary": post.summary[:500] if post.summary else "",
            "content": post.content,
            "url": post.url,
            "source": post.source,
            "category": post.category,
            "published_at": post.published_at,
            "view_count": post.view_count,
            "comment_count": post.comment_count,
            "like_count": post.like_count,
            "author": post.author,
            "source_type": "community",
        }

    async def close(self):
        """클라이언트 종료"""
        await self.client.aclose()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
