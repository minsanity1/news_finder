"""
더쿠 수집기
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


class TheqooCollector(BaseCommunityCollector):
    """더쿠 커뮤니티 수집기"""

    SOURCE_NAME = "더쿠"
    BASE_URL = "https://theqoo.net"
    REQUEST_DELAY = (1.0, 2.0)

    def __init__(self):
        # 더쿠 전용 헤더 (Referer 필수!)
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                "Referer": "https://theqoo.net/",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
            },
            follow_redirects=True
        )

    async def _request_with_retry(self, url: str, max_retry: int = 3) -> httpx.Response:
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
            await asyncio.sleep(random.uniform(0.5, 1.0) * attempt)
        raise last_err

    def _get_board_url(self, board_id: str, page: int = 1) -> str:
        """게시판 URL 생성"""
        config = COMMUNITY_BOARDS.get("theqoo", {})
        for board in config.get("boards", []):
            if board["id"] == board_id:
                path = board["path"]
                return f"{self.BASE_URL}/{path}?page={page}"

        # 기본값: 핫글
        return f"{self.BASE_URL}/hot?page={page}"

    async def get_board_list(self, board_id: str, page: int = 1) -> List[dict]:
        """게시판 글 목록 파싱"""
        url = self._get_board_url(board_id, page)
        print(f"[{self.SOURCE_NAME}] Fetching: {url}")

        try:
            response = await self._request_with_retry(url)
        except Exception as e:
            print(f"[{self.SOURCE_NAME}] Request failed: {e}")
            return []

        soup = BeautifulSoup(response.text, "lxml")
        posts = []

        # 게시글 목록: table.theqoo_board_table tbody tr (공지 제외)
        rows = soup.select("table.theqoo_board_table tbody tr:not(.notice)")
        if not rows:
            rows = soup.select("table.bd_lst tbody tr:not(.notice)")
        print(f"[{self.SOURCE_NAME}] Found {len(rows)} rows")

        for row in rows:
            try:
                # 제목: td.title > a (첫 번째 a 태그, replyNum 제외)
                title_td = row.select_one("td.title")
                if not title_td:
                    continue

                # 직접 자식 a 태그들 중 첫 번째 (replyNum은 제외)
                all_links = title_td.select("a")
                title_elem = None
                for link in all_links:
                    if "replyNum" not in link.get("class", []):
                        title_elem = link
                        break

                if not title_elem:
                    continue

                # 링크 먼저 추출
                href = title_elem.get("href", "")
                if not href:
                    continue

                # 제목 텍스트 추출 - 복사본에서 작업
                title_copy = BeautifulSoup(str(title_elem), "lxml")
                # 아이콘 제거
                for tag in title_copy.find_all("i"):
                    tag.decompose()
                title = title_copy.get_text(strip=True)

                # 제목이 없거나 너무 짧으면 스킵
                if not title or len(title) < 2:
                    continue

                # URL 정규화
                if href.startswith("/"):
                    full_url = self.BASE_URL + href
                elif not href.startswith("http"):
                    full_url = f"{self.BASE_URL}/{href}"
                else:
                    full_url = href

                # 쿼리 파라미터 제거 (중복 방지)
                if "?" in full_url:
                    full_url = full_url.split("?")[0]

                # 댓글수: a.replyNum
                comment_count = 0
                comment_elem = title_td.select_one("a.replyNum")
                if comment_elem:
                    num = re.sub(r"[^\d]", "", comment_elem.get_text())
                    comment_count = int(num) if num else 0

                # 조회수: td.m_no
                view_count = 0
                view_elem = row.select_one("td.m_no")
                if view_elem:
                    num = re.sub(r"[^\d]", "", view_elem.get_text())
                    view_count = int(num) if num else 0

                # 카테고리: td.cate span
                category = ""
                category_elem = row.select_one("td.cate span")
                if category_elem:
                    category = category_elem.get_text(strip=True)

                # 날짜: td.time
                date_str = ""
                time_elem = row.select_one("td.time")
                if time_elem:
                    date_str = time_elem.get_text(strip=True)

                posts.append({
                    "title": title,
                    "url": full_url,
                    "view_count": view_count,
                    "comment_count": comment_count,
                    "like_count": 0,  # 목록에서는 추천수 안 보임
                    "category": category,
                    "date_str": date_str,
                })

            except Exception as e:
                print(f"[{self.SOURCE_NAME}] Parse row error: {e}")
                continue

        print(f"[{self.SOURCE_NAME}] Parsed {len(posts)} posts")
        return posts

    async def get_hot_posts(
        self,
        board_id: str,
        limit: int = 20,
        fetch_detail: bool = True
    ) -> List[CommunityPost]:
        """핫글/인기글 수집 - 목록 데이터를 우선 사용"""
        post_list = await self.get_board_list(board_id, page=1)
        posts = []

        for item in post_list[:limit]:
            # 제외 패턴 확인
            if self._should_exclude(item.get("title", "")):
                continue

            # 목록에서 가져온 데이터로 기본 CommunityPost 생성
            list_title = item.get("title", "")
            list_view = item.get("view_count", 0)
            list_comment = item.get("comment_count", 0)
            list_category = item.get("category", "")

            if fetch_detail:
                try:
                    post = await self.get_post_detail(item["url"])
                    # 상세 페이지 제목이 비어있으면 목록 제목 사용
                    if not post.title:
                        post.title = list_title
                    # 조회수/댓글수가 0이면 목록 데이터 사용
                    if not post.view_count:
                        post.view_count = list_view
                    if not post.comment_count:
                        post.comment_count = list_comment
                    # 카테고리 설정
                    post.category = list_category or board_id
                    posts.append(post)
                except Exception as e:
                    print(f"[{self.SOURCE_NAME}] Failed to fetch {item['url']}: {e}")
                    # 상세 페이지 실패 시 목록 데이터만으로 생성
                    posts.append(CommunityPost(
                        title=list_title,
                        summary="",
                        content="",
                        url=item.get("url", ""),
                        source=self.SOURCE_NAME,
                        category=list_category or board_id,
                        view_count=list_view,
                        comment_count=list_comment,
                        published_at=datetime.now(),
                    ))
            else:
                # 목록 정보만으로 CommunityPost 생성
                posts.append(CommunityPost(
                    title=list_title,
                    summary="",
                    content="",
                    url=item.get("url", ""),
                    source=self.SOURCE_NAME,
                    category=list_category or board_id,
                    view_count=list_view,
                    comment_count=list_comment,
                ))

        return posts

    async def get_post_detail(self, post_url: str) -> CommunityPost:
        """게시글 상세 파싱"""
        try:
            response = await self._request_with_retry(post_url)
        except Exception as e:
            raise Exception(f"Request failed: {e}")

        soup = BeautifulSoup(response.text, "lxml")

        # 제목 - 다양한 셀렉터 시도
        title_elem = (
            soup.select_one("div.rd_hd h3.title a") or
            soup.select_one("div.rd_hd h3.title") or
            soup.select_one("h3.title a") or
            soup.select_one("h3.title") or
            soup.select_one("div.rd_hd h3") or
            soup.select_one("div.title_area h3")
        )
        title = ""
        if title_elem:
            # strong, span 등 내부 태그 포함 텍스트 추출
            title = title_elem.get_text(strip=True)

        # 본문
        content_div = (
            soup.select_one("div.rd_body article") or
            soup.select_one("article.rd_body") or
            soup.select_one("div.rd_body div.rd_body_wrap") or
            soup.select_one("div.rd_body")
        )
        content = ""
        if content_div:
            # 스크립트, 스타일 태그 제거
            for tag in content_div.find_all(["script", "style", "iframe", "ins"]):
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
            soup.select_one("div.rd_hd span.date") or
            soup.select_one("span.date") or
            soup.select_one("span.time")
        )

        if not time_elem:
            return datetime.now()

        text = time_elem.get_text(strip=True)

        # "2026.01.03 12:33" 형식
        try:
            return datetime.strptime(text[:16], "%Y.%m.%d %H:%M")
        except ValueError:
            pass

        # "01.03 12:33" 형식 (올해)
        try:
            dt = datetime.strptime(text[:11], "%m.%d %H:%M")
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
            soup.select_one("div.rd_hd a.member_plate") or
            soup.select_one("a.member_plate") or
            soup.select_one("span.member") or
            soup.select_one("div.rd_hd span.nick")
        )
        if author_elem:
            return author_elem.get_text(strip=True)
        return None

    def _parse_meta_value(self, soup, label: str) -> int:
        """메타 정보 값 파싱"""
        # rd_hd 영역에서 먼저 찾기
        for elem in soup.select("div.rd_hd span, div.rd_hd div"):
            text = elem.get_text(strip=True)
            if label in text:
                num = re.search(r"(\d[\d,]*)", text)
                if num:
                    return int(num.group(1).replace(",", ""))

        return 0
