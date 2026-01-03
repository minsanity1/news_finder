"""
에펨코리아 수집기
"""
from datetime import datetime, timedelta
from typing import List, Optional
import re

from bs4 import BeautifulSoup

from .base import BaseCommunityCollector, CommunityPost
from .config import COMMUNITY_BOARDS


class FMKoreaCollector(BaseCommunityCollector):
    """에펨코리아 커뮤니티 수집기"""

    SOURCE_NAME = "에펨코리아"
    BASE_URL = "https://www.fmkorea.com"
    REQUEST_DELAY = (1.5, 3.0)  # 에펨코리아는 좀 더 조심

    def _get_board_url(self, board_id: str, page: int = 1) -> str:
        """게시판 URL 생성"""
        config = COMMUNITY_BOARDS.get("fmkorea", {})
        for board in config.get("boards", []):
            if board["id"] == board_id:
                return f"{self.BASE_URL}/{board['path']}&page={page}"

        # 기본값: board_id를 path로 사용
        return f"{self.BASE_URL}/index.php?mid={board_id}&page={page}"

    async def get_board_list(self, board_id: str, page: int = 1) -> List[dict]:
        """게시판 글 목록 파싱"""
        url = self._get_board_url(board_id, page)

        try:
            response = await self._request_with_delay(url)
            response.raise_for_status()
        except Exception as e:
            print(f"[{self.SOURCE_NAME}] Request failed: {e}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        posts = []

        # 게시글 목록 파싱 (여러 선택자 시도)
        rows = soup.select("li.li")
        if not rows:
            rows = soup.select("tr[class*='notice_'], tr:not([class])")

        for row in rows:
            try:
                # 제목 및 링크
                title_elem = (
                    row.select_one("a.title") or
                    row.select_one("h3.title a") or
                    row.select_one("a.hx")
                )

                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                href = title_elem.get("href", "")

                if not href:
                    continue

                # URL 정규화
                if href.startswith("/"):
                    full_url = self.BASE_URL + href
                elif not href.startswith("http"):
                    full_url = f"{self.BASE_URL}/{href}"
                else:
                    full_url = href

                # 조회수 파싱
                view_count = self._parse_view_count(row)

                # 댓글수 파싱
                comment_count = self._parse_comment_count(row, title_elem)

                # 추천수 파싱
                like_count = self._parse_like_count(row)

                posts.append({
                    "title": title,
                    "url": full_url,
                    "view_count": view_count,
                    "comment_count": comment_count,
                    "like_count": like_count,
                })

            except Exception as e:
                print(f"[{self.SOURCE_NAME}] Parse row error: {e}")
                continue

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

    def _parse_view_count(self, row) -> int:
        """조회수 파싱"""
        # 다양한 선택자 시도
        view_elem = (
            row.select_one("span.count") or
            row.select_one("td.m_no") or
            row.select_one(".count_hit")
        )
        if view_elem:
            text = view_elem.get_text(strip=True)
            num = re.sub(r"[^\d]", "", text)
            return int(num) if num else 0
        return 0

    def _parse_comment_count(self, row, title_elem) -> int:
        """댓글수 파싱"""
        # 제목 옆 댓글 수
        comment_span = row.select_one("span.comment_count, a.comment")
        if comment_span:
            text = comment_span.get_text(strip=True)
            num = re.sub(r"[^\d]", "", text)
            return int(num) if num else 0

        # 제목 내 [숫자] 패턴
        title_text = title_elem.get_text() if title_elem else ""
        match = re.search(r"\[(\d+)\]", title_text)
        if match:
            return int(match.group(1))

        return 0

    def _parse_like_count(self, row) -> int:
        """추천수 파싱"""
        like_elem = row.select_one("span.count_recommend, td.m_no_voted")
        if like_elem:
            text = like_elem.get_text(strip=True)
            num = re.sub(r"[^\d]", "", text)
            return int(num) if num else 0
        return 0

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
