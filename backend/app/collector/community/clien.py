"""
클리앙 수집기
"""
from datetime import datetime, timedelta
from typing import List, Optional
import re

from bs4 import BeautifulSoup

from .base import BaseCommunityCollector, CommunityPost
from .config import COMMUNITY_BOARDS


class ClienCollector(BaseCommunityCollector):
    """클리앙 커뮤니티 수집기"""

    SOURCE_NAME = "클리앙"
    BASE_URL = "https://www.clien.net"
    REQUEST_DELAY = (1.0, 2.0)

    def _get_board_url(self, board_id: str, page: int = 1) -> str:
        """게시판 URL 생성"""
        config = COMMUNITY_BOARDS.get("clien", {})
        for board in config.get("boards", []):
            if board["id"] == board_id:
                path = board["path"]
                if "?" in path:
                    return f"{self.BASE_URL}/{path}&po={page - 1}"
                return f"{self.BASE_URL}/{path}?po={page - 1}"

        # 기본값: 추천글
        return f"{self.BASE_URL}/service/recommend?po={page - 1}"

    async def get_board_list(self, board_id: str, page: int = 1) -> List[dict]:
        """게시판 글 목록 파싱"""
        url = self._get_board_url(board_id, page)
        print(f"[{self.SOURCE_NAME}] Fetching: {url}")

        try:
            response = await self._request_with_delay(url)
            response.raise_for_status()
        except Exception as e:
            print(f"[{self.SOURCE_NAME}] Request failed: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        posts = []

        # 게시글 목록: div.list_item.symph_row
        rows = soup.select("div.list_item.symph_row")
        print(f"[{self.SOURCE_NAME}] Found {len(rows)} rows")

        for row in rows:
            try:
                # 제목: span.subject_fixed (title 속성에 전체 제목)
                title_elem = row.select_one("span.subject_fixed")
                if not title_elem:
                    continue

                # title 속성에 전체 제목이 있음
                title = title_elem.get("title", "") or title_elem.get_text(strip=True)
                if not title:
                    continue

                # 링크: a.list_subject
                link_elem = row.select_one("a.list_subject")
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

                # 공감수: div.list_symph span
                like_count = 0
                like_elem = row.select_one("div.list_symph span")
                if not like_elem:
                    like_elem = row.select_one("div.list_symph")
                if like_elem:
                    num = re.sub(r"[^\d]", "", like_elem.get_text())
                    like_count = int(num) if num else 0

                # 댓글수: span.rSymph05 또는 다른 댓글 셀렉터
                comment_count = 0
                comment_elem = row.select_one("span.rSymph05")
                if not comment_elem:
                    comment_elem = row.select_one("span.reply_symph")
                if comment_elem:
                    num = re.sub(r"[^\d]", "", comment_elem.get_text())
                    comment_count = int(num) if num else 0

                # 조회수: span.hit
                view_count = 0
                view_elem = row.select_one("span.hit")
                if not view_elem:
                    view_elem = row.select_one("div.list_hit span")
                if not view_elem:
                    view_elem = row.select_one("div.list_hit")
                if view_elem:
                    num = re.sub(r"[^\d]", "", view_elem.get_text())
                    view_count = int(num) if num else 0

                # 게시판: span.shortname
                category = ""
                category_elem = row.select_one("span.shortname")
                if category_elem:
                    category = category_elem.get_text(strip=True)

                posts.append({
                    "title": title,
                    "url": full_url,
                    "view_count": view_count,
                    "comment_count": comment_count,
                    "like_count": like_count,
                    "category": category,
                })

            except Exception as e:
                print(f"[{self.SOURCE_NAME}] Parse row error: {e}")
                continue

        print(f"[{self.SOURCE_NAME}] Parsed {len(posts)} posts")
        return posts

    async def get_post_detail(self, post_url: str) -> CommunityPost:
        """게시글 상세 파싱"""
        try:
            response = await self._request_with_delay(post_url)
            response.raise_for_status()
        except Exception as e:
            raise Exception(f"Request failed: {e}")

        soup = BeautifulSoup(response.text, "html.parser")

        # 제목
        title_elem = (
            soup.select_one("h3.post_subject span") or
            soup.select_one("h3.post_subject") or
            soup.select_one("div.post_title")
        )
        title = title_elem.get_text(strip=True) if title_elem else ""

        # 본문
        content_div = (
            soup.select_one("div.post_content article") or
            soup.select_one("div.post_content") or
            soup.select_one("article.post_article")
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

        # 조회수, 공감수
        view_count = self._parse_meta_value(soup, "조회")
        like_count = self._parse_meta_value(soup, "공감")

        return CommunityPost(
            title=title,
            summary=content[:300] if content else "",
            content=content,
            url=post_url,
            source=self.SOURCE_NAME,
            category="",  # 호출 시 지정됨
            published_at=published_at,
            view_count=view_count,
            like_count=like_count,
            author=author,
        )

    def _parse_datetime(self, soup) -> Optional[datetime]:
        """작성 시간 파싱"""
        # span.timestamp (2026-01-03 12:33:26 형식)
        time_elem = (
            soup.select_one("span.timestamp") or
            soup.select_one("span.post_time") or
            soup.select_one("div.post_info span.time")
        )

        if not time_elem:
            return datetime.now()

        text = time_elem.get_text(strip=True)

        # "2026-01-03 12:33:26" 형식
        try:
            return datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

        # "2026-01-03 12:33" 형식
        try:
            return datetime.strptime(text[:16], "%Y-%m-%d %H:%M")
        except ValueError:
            pass

        # "01-03 12:33" 형식 (올해)
        try:
            dt = datetime.strptime(text[:11], "%m-%d %H:%M")
            return dt.replace(year=datetime.now().year)
        except ValueError:
            pass

        # "12:33" 형식 (오늘)
        try:
            dt = datetime.strptime(text[:5], "%H:%M")
            now = datetime.now()
            return dt.replace(year=now.year, month=now.month, day=now.day)
        except ValueError:
            pass

        return datetime.now()

    def _parse_author(self, soup) -> Optional[str]:
        """작성자 파싱"""
        # div.list_author span.nickname span
        author_elem = (
            soup.select_one("div.post_info span.nickname") or
            soup.select_one("span.nickname span") or
            soup.select_one("a.member")
        )
        if author_elem:
            return author_elem.get_text(strip=True)
        return None

    def _parse_meta_value(self, soup, label: str) -> int:
        """메타 정보 값 파싱"""
        for elem in soup.select("span, div.post_info *"):
            text = elem.get_text(strip=True)
            if label in text:
                num = re.search(r"(\d[\d,]*)", text)
                if num:
                    return int(num.group(1).replace(",", ""))

        return 0
