"""
디시인사이드 수집기
"""
from datetime import datetime, timedelta
from typing import List, Optional
import re

from bs4 import BeautifulSoup

from .base import BaseCommunityCollector, CommunityPost
from .config import COMMUNITY_BOARDS


class DCInsideCollector(BaseCommunityCollector):
    """디시인사이드 커뮤니티 수집기"""

    SOURCE_NAME = "디시인사이드"
    BASE_URL = "https://gall.dcinside.com"
    REQUEST_DELAY = (1.0, 2.0)

    def _get_board_url(self, board_id: str, page: int = 1) -> str:
        """게시판 URL 생성"""
        config = COMMUNITY_BOARDS.get("dcinside", {})
        for board in config.get("boards", []):
            if board["id"] == board_id:
                path = board["path"]
                if "?" in path:
                    return f"{self.BASE_URL}/{path}&page={page}"
                return f"{self.BASE_URL}/{path}?page={page}"

        # 기본값: 실시간베스트
        return f"{self.BASE_URL}/board/lists/?id=dcbest&page={page}"

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

        # 게시글 목록: tr.ub-content.us-post (공지/설문 제외)
        rows = soup.select("tr.ub-content.us-post")
        print(f"[{self.SOURCE_NAME}] Found {len(rows)} rows")

        for row in rows:
            try:
                # 게시글 번호 (data-no 속성)
                post_no = row.get("data-no", "")

                # 공지/설문 스킵
                num_cell = row.select_one("td.gall_num")
                if num_cell:
                    num_text = num_cell.get_text(strip=True)
                    if num_text in ["공지", "설문", "AD"]:
                        continue

                # 제목 셀
                title_cell = row.select_one("td.gall_tit")
                if not title_cell:
                    continue

                # 제목 링크
                title_link = title_cell.select_one("a")
                if not title_link:
                    continue

                # 원본 갤러리 태그 제거 후 제목 추출
                source_gall = title_cell.select_one("strong")
                source_gall_text = source_gall.get_text(strip=True) if source_gall else ""

                title = title_link.get_text(strip=True)
                # 원본 갤러리 태그 제거
                if source_gall_text and title.startswith(source_gall_text):
                    title = title[len(source_gall_text):].strip()

                if not title or len(title) < 2:
                    continue

                # 링크
                href = title_link.get("href", "")
                if not href:
                    continue

                # URL 정규화
                if href.startswith("/"):
                    full_url = self.BASE_URL + href
                elif not href.startswith("http"):
                    full_url = f"{self.BASE_URL}/{href}"
                else:
                    full_url = href

                # 댓글 수: span.reply_num
                comment_count = 0
                reply_span = title_cell.select_one("span.reply_num")
                if reply_span:
                    # [123] 형식에서 숫자 추출
                    num = re.sub(r"[^\d]", "", reply_span.get_text())
                    comment_count = int(num) if num else 0

                # 작성자 정보
                writer_cell = row.select_one("td.gall_writer")
                author = ""
                if writer_cell:
                    author = writer_cell.get("data-nick", "")

                # 날짜: td.gall_date (title 속성에 전체 날짜)
                date_cell = row.select_one("td.gall_date")
                date_str = ""
                if date_cell:
                    date_str = date_cell.get("title", "") or date_cell.get_text(strip=True)

                # 조회수: td.gall_count
                view_count = 0
                view_cell = row.select_one("td.gall_count")
                if view_cell:
                    num = re.sub(r"[^\d]", "", view_cell.get_text())
                    view_count = int(num) if num else 0

                # 추천수: td.gall_recommend
                like_count = 0
                recommend_cell = row.select_one("td.gall_recommend")
                if recommend_cell:
                    num = re.sub(r"[^\d]", "", recommend_cell.get_text())
                    like_count = int(num) if num else 0

                posts.append({
                    "title": title,
                    "url": full_url,
                    "view_count": view_count,
                    "comment_count": comment_count,
                    "like_count": like_count,
                    "category": source_gall_text,  # 원본 갤러리
                    "author": author,
                    "date_str": date_str,
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
            soup.select_one("span.title_subject") or
            soup.select_one("h3.title") or
            soup.select_one("div.view_title")
        )
        title = title_elem.get_text(strip=True) if title_elem else ""

        # 본문
        content_div = (
            soup.select_one("div.write_div") or
            soup.select_one("div.view_content") or
            soup.select_one("div.writing_view_box")
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
        time_elem = (
            soup.select_one("span.gall_date") or
            soup.select_one("span.date")
        )

        if not time_elem:
            return datetime.now()

        # title 속성 또는 텍스트에서 날짜 추출
        text = time_elem.get("title", "") or time_elem.get_text(strip=True)

        # "2026-01-03 20:20:02" 형식
        try:
            return datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

        # "2026.01.03 20:20" 형식
        try:
            return datetime.strptime(text[:16], "%Y.%m.%d %H:%M")
        except ValueError:
            pass

        # "01.03 20:20" 형식 (올해)
        try:
            dt = datetime.strptime(text[:11], "%m.%d %H:%M")
            return dt.replace(year=datetime.now().year)
        except ValueError:
            pass

        # "20:20" 형식 (오늘)
        try:
            dt = datetime.strptime(text[:5], "%H:%M")
            now = datetime.now()
            return dt.replace(year=now.year, month=now.month, day=now.day)
        except ValueError:
            pass

        return datetime.now()

    def _parse_author(self, soup) -> Optional[str]:
        """작성자 파싱"""
        author_elem = (
            soup.select_one("span.nickname") or
            soup.select_one("span.gall_writer") or
            soup.select_one("div.gall_writer")
        )
        if author_elem:
            # data-nick 속성 우선
            nick = author_elem.get("data-nick", "")
            if nick:
                return nick
            return author_elem.get_text(strip=True)
        return None

    def _parse_meta_value(self, soup, label: str) -> int:
        """메타 정보 값 파싱"""
        # 디시 상세페이지의 조회수/추천수 파싱
        for elem in soup.select("span, div.view_info *"):
            text = elem.get_text(strip=True)
            if label in text:
                num = re.search(r"(\d[\d,]*)", text)
                if num:
                    return int(num.group(1).replace(",", ""))

        return 0
