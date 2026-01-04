"""
에펨코리아 수집기
"""
from datetime import datetime, timedelta
from typing import List, Optional
import asyncio
import random
import re

import httpx
from bs4 import BeautifulSoup

from .base import BaseCommunityCollector, CommunityPost
from .config import COMMUNITY_BOARDS


class FMKoreaCollector(BaseCommunityCollector):
    """에펨코리아 커뮤니티 수집기"""

    SOURCE_NAME = "에펨코리아"
    BASE_URL = "https://www.fmkorea.com"
    REQUEST_DELAY = (0.8, 1.6)  # 성공한 크롤러와 동일

    def __init__(self):
        # FMKorea 전용 헤더 (Referer 필수!)
        self.client = httpx.AsyncClient(
            timeout=25.0,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0 Safari/537.36"
                ),
                "Referer": "https://www.fmkorea.com/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ko,en;q=0.8",
            },
            follow_redirects=True
        )

    async def _request_with_retry(self, url: str, max_retry: int = 4) -> httpx.Response:
        """재시도 로직이 포함된 요청"""
        last_err = None
        for attempt in range(1, max_retry + 1):
            try:
                await asyncio.sleep(random.uniform(*self.REQUEST_DELAY))
                resp = await self.client.get(url)
                if resp.status_code == 200 and resp.text:
                    return resp
                last_err = RuntimeError(f"Bad status {resp.status_code}")
            except Exception as e:
                last_err = e
            # 지수 백오프
            await asyncio.sleep(random.uniform(0.6, 1.2) * attempt)
        raise last_err

    def _get_board_url(self, board_id: str, page: int = 1) -> str:
        """게시판 URL 생성"""
        config = COMMUNITY_BOARDS.get("fmkorea", {})
        for board in config.get("boards", []):
            if board["id"] == board_id:
                path = board["path"]
                if "?" in path:
                    return f"{self.BASE_URL}/{path}&page={page}"
                return f"{self.BASE_URL}/{path}?page={page}"

        # 기본값: 유머 인기글
        return f"{self.BASE_URL}/humor?sort_index=pop&page={page}"

    async def get_board_list(self, board_id: str, page: int = 1) -> List[dict]:
        """게시판 글 목록 파싱 (fm_best_widget 구조)"""
        url = self._get_board_url(board_id, page)
        print(f"[{self.SOURCE_NAME}] Fetching: {url}")

        try:
            response = await self._request_with_retry(url)
        except Exception as e:
            print(f"[{self.SOURCE_NAME}] Request failed: {e}")
            return []

        soup = BeautifulSoup(response.text, "lxml")
        posts = []

        # 게시글 목록: div.fm_best_widget li.li 또는 li.li > div.li
        rows = soup.select("div.fm_best_widget li.li")
        if not rows:
            # fallback: 기존 선택자
            rows = soup.select("li.li")
        print(f"[{self.SOURCE_NAME}] Found {len(rows)} rows")

        for row in rows:
            try:
                # 제목: span.ellipsis-target
                title_elem = row.select_one("span.ellipsis-target")
                if not title_elem:
                    # fallback
                    title_elem = row.select_one("h3.title a")

                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                if not title:
                    continue

                # 링크: h3.title a[href]
                link_elem = row.select_one("h3.title a")
                if not link_elem:
                    link_elem = row.select_one("a.title")

                if not link_elem:
                    continue

                href = link_elem.get("href", "")
                if not href:
                    continue

                # URL 정규화
                if href.startswith("/"):
                    full_url = self.BASE_URL + href
                elif not href.startswith("http"):
                    full_url = f"{self.BASE_URL}/{href}"
                else:
                    full_url = href

                # 추천수: span.count 또는 a.pc_voted_count span.count
                like_count = 0
                like_elem = row.select_one("span.count")
                if like_elem:
                    num = re.sub(r"[^\d]", "", like_elem.get_text())
                    like_count = int(num) if num else 0

                # 댓글수: span.comment_count (대괄호 포함, 예: [15])
                comment_count = 0
                comment_elem = row.select_one("span.comment_count")
                if comment_elem:
                    text = comment_elem.get_text(strip=True)
                    # 대괄호 제거: [15] -> 15
                    num = re.sub(r"[^\d]", "", text)
                    comment_count = int(num) if num else 0

                # 카테고리: span.category a
                category = ""
                category_elem = row.select_one("span.category a")
                if category_elem:
                    category = category_elem.get_text(strip=True)

                # 시간: span.regdate
                date_str = ""
                time_elem = row.select_one("span.regdate")
                if time_elem:
                    date_str = time_elem.get_text(strip=True)

                # 작성자: span.author
                author = ""
                author_elem = row.select_one("span.author")
                if author_elem:
                    author = author_elem.get_text(strip=True)

                # 포텐 여부: span.STAR-BEST
                is_poten = row.select_one("span.STAR-BEST") is not None

                posts.append({
                    "title": title,
                    "url": full_url,
                    "view_count": 0,  # 목록에서는 조회수 안 보임
                    "comment_count": comment_count,
                    "like_count": like_count,
                    "category": category,
                    "date_str": date_str,
                    "author": author,
                    "is_poten": is_poten,
                })

            except Exception as e:
                print(f"[{self.SOURCE_NAME}] Parse row error: {e}")
                continue

        print(f"[{self.SOURCE_NAME}] Parsed {len(posts)} posts")
        return posts

    async def get_post_detail(self, post_url: str) -> CommunityPost:
        """게시글 상세 파싱"""
        try:
            response = await self._request_with_retry(post_url)
        except Exception as e:
            raise Exception(f"Request failed: {e}")

        soup = BeautifulSoup(response.text, "lxml")

        # 제목
        title_elem = (
            soup.select_one("span.np_18px_span") or
            soup.select_one("h1.np_18px") or
            soup.select_one("div.title_area h1")
        )
        title = title_elem.get_text(strip=True) if title_elem else ""

        # 본문
        content_div = (
            soup.select_one("div.rd_body article") or
            soup.select_one("div.rd_body") or
            soup.select_one("article")
        )
        content = ""
        if content_div:
            # 스크립트, 스타일 태그 제거
            for tag in content_div.find_all(["script", "style", "iframe"]):
                tag.decompose()
            content = content_div.get_text(separator="\n", strip=True)

        # 작성 시간
        published_at = self._parse_datetime(soup)

        # 작성자
        author = self._parse_author(soup)

        # 조회수, 추천수
        view_count = self._parse_meta_value(soup, "조회")
        like_count = self._parse_meta_value(soup, "추천")
        comment_count = self._parse_meta_value(soup, "댓글")

        return CommunityPost(
            title=title,
            summary=content[:300] if content else "",
            content=content,
            url=post_url,
            source=self.SOURCE_NAME,
            category="",  # 호출 시 지정됨
            published_at=published_at,
            view_count=view_count,
            comment_count=comment_count,
            like_count=like_count,
            author=author,
        )

    def _parse_datetime(self, soup) -> Optional[datetime]:
        """작성 시간 파싱"""
        time_elem = (
            soup.select_one("span.date") or
            soup.select_one("span.time") or
            soup.select_one("div.top_area span.date")
        )

        if not time_elem:
            return datetime.now()

        text = time_elem.get_text(strip=True)

        # "2025.01.02 14:30" 형식
        try:
            return datetime.strptime(text, "%Y.%m.%d %H:%M")
        except ValueError:
            pass

        # "01.02 14:30" 형식 (올해)
        try:
            dt = datetime.strptime(text, "%m.%d %H:%M")
            return dt.replace(year=datetime.now().year)
        except ValueError:
            pass

        # "14:30" 형식 (오늘)
        try:
            dt = datetime.strptime(text, "%H:%M")
            now = datetime.now()
            return dt.replace(year=now.year, month=now.month, day=now.day)
        except ValueError:
            pass

        # "N분 전", "N시간 전" 형식
        if "분 전" in text:
            match = re.search(r"(\d+)분", text)
            if match:
                return datetime.now() - timedelta(minutes=int(match.group(1)))
        elif "시간 전" in text:
            match = re.search(r"(\d+)시간", text)
            if match:
                return datetime.now() - timedelta(hours=int(match.group(1)))

        return datetime.now()

    def _parse_author(self, soup) -> Optional[str]:
        """작성자 파싱"""
        author_elem = (
            soup.select_one("a.member_plate") or
            soup.select_one("span.member") or
            soup.select_one("div.top_area a.nick")
        )
        if author_elem:
            return author_elem.get_text(strip=True)
        return None

    def _parse_meta_value(self, soup, label: str) -> int:
        """메타 정보 값 파싱 (조회, 추천 등)"""
        # "조회 수 1234" 형태 또는 아이콘 + 숫자 형태
        for elem in soup.select("span, div.top_area *"):
            text = elem.get_text(strip=True)
            if label in text:
                num = re.search(r"(\d[\d,]*)", text)
                if num:
                    return int(num.group(1).replace(",", ""))

        return 0
