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


# 최신 브라우저 User-Agent 목록 (2024-2025)
USER_AGENTS = [
    # Chrome Windows
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
    # Chrome Mac
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
]


class FMKoreaCollector(BaseCommunityCollector):
    """에펨코리아 커뮤니티 수집기"""

    SOURCE_NAME = "에펨코리아"
    BASE_URL = "https://www.fmkorea.com"
    REQUEST_DELAY = (1.0, 2.0)  # 조금 더 느리게

    def __init__(self):
        # 랜덤 User-Agent 선택
        user_agent = random.choice(USER_AGENTS)

        # FMKorea 전용 헤더 - 실제 브라우저와 유사하게
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
                "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept-Encoding": "gzip, deflate, br",
                "Cache-Control": "max-age=0",
                "Connection": "keep-alive",
                "Sec-Ch-Ua": '"Chromium";v="131", "Not_A Brand";v="24"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin",
                "Sec-Fetch-User": "?1",
                "Upgrade-Insecure-Requests": "1",
            },
            follow_redirects=True,
            http2=True,  # HTTP/2 지원
        )
        self._cookies_initialized = False

    async def _init_session(self):
        """첫 요청 전 세션 초기화 (쿠키 획득)"""
        if self._cookies_initialized:
            return

        try:
            # 메인 페이지 방문하여 쿠키 획득
            await asyncio.sleep(random.uniform(0.5, 1.0))
            resp = await self.client.get(
                self.BASE_URL,
                headers={"Referer": "https://www.google.com/"}
            )
            if resp.status_code == 200:
                self._cookies_initialized = True
                print(f"[{self.SOURCE_NAME}] Session initialized, cookies obtained")
        except Exception as e:
            print(f"[{self.SOURCE_NAME}] Session init warning: {e}")

    async def _request_with_retry(self, url: str, max_retry: int = 4, referer: str = None) -> httpx.Response:
        """재시도 로직이 포함된 요청"""
        # 세션 초기화
        await self._init_session()

        last_err = None
        headers = {}
        if referer:
            headers["Referer"] = referer
        else:
            headers["Referer"] = f"{self.BASE_URL}/"

        for attempt in range(1, max_retry + 1):
            try:
                # 요청 간격 (시도할수록 더 긴 간격)
                delay = random.uniform(*self.REQUEST_DELAY) * (1 + attempt * 0.3)
                await asyncio.sleep(delay)

                resp = await self.client.get(url, headers=headers)

                # Cloudflare 차단 감지
                if resp.status_code == 403:
                    if "cloudflare" in resp.text.lower() or "cf-ray" in resp.headers.get("server", "").lower():
                        print(f"[{self.SOURCE_NAME}] Cloudflare block detected, attempt {attempt}")
                        last_err = RuntimeError("Cloudflare blocked")
                        continue
                    print(f"[{self.SOURCE_NAME}] 403 Forbidden, attempt {attempt}")
                    last_err = RuntimeError("403 Forbidden")
                    continue

                if resp.status_code == 200 and resp.text:
                    # 차단 페이지인지 확인
                    if "차단" in resp.text[:1000] or "접근이 거부" in resp.text[:1000]:
                        print(f"[{self.SOURCE_NAME}] Access denied page detected")
                        last_err = RuntimeError("Access denied")
                        continue
                    return resp

                last_err = RuntimeError(f"Bad status {resp.status_code}")

            except Exception as e:
                print(f"[{self.SOURCE_NAME}] Request error (attempt {attempt}): {e}")
                last_err = e

            # 지수 백오프
            await asyncio.sleep(random.uniform(1.0, 2.0) * attempt)

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

        # 게시글 목록: 여러 선택자 시도
        rows = soup.select("div.fm_best_widget li.li")
        if not rows:
            rows = soup.select("ul.li li.li")
        if not rows:
            rows = soup.select("li.li")
        if not rows:
            # 테이블 형식 (best 게시판)
            rows = soup.select("table.bd_lst tbody tr")

        # 디버깅: 구조 변경 감지
        if not rows:
            print(f"[{self.SOURCE_NAME}] WARNING: No rows found!")
            # 페이지 구조 확인용 출력
            body_classes = soup.body.get("class", []) if soup.body else []
            print(f"[{self.SOURCE_NAME}] Body classes: {body_classes}")
            # 주요 컨테이너 확인
            main_containers = soup.select("div.content_container, div.best_widget, div#content")
            print(f"[{self.SOURCE_NAME}] Main containers found: {len(main_containers)}")
            # HTML 일부 저장 (디버깅용)
            if len(response.text) < 5000:
                print(f"[{self.SOURCE_NAME}] Full HTML (short): {response.text}")
            return []

        print(f"[{self.SOURCE_NAME}] Found {len(rows)} rows")

        for row in rows:
            try:
                # 제목 추출: 여러 선택자 시도
                title_elem = (
                    row.select_one("span.ellipsis-target") or
                    row.select_one("h3.title a") or
                    row.select_one("td.title a") or  # 테이블 형식
                    row.select_one("a.hx")  # 대체 형식
                )

                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)
                if not title:
                    continue

                # 링크 추출: 여러 선택자 시도
                link_elem = (
                    row.select_one("h3.title a") or
                    row.select_one("td.title a") or  # 테이블 형식
                    row.select_one("a.title") or
                    row.select_one("a.hx") or
                    title_elem if title_elem.name == "a" else None
                )

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

                # 추천수: 여러 선택자 시도
                like_count = 0
                like_elem = (
                    row.select_one("span.count") or
                    row.select_one("td.m_no") or  # 테이블 형식
                    row.select_one(".vote")
                )
                if like_elem:
                    num = re.sub(r"[^\d]", "", like_elem.get_text())
                    like_count = int(num) if num else 0

                # 댓글수: 여러 선택자 시도
                comment_count = 0
                comment_elem = (
                    row.select_one("span.comment_count") or
                    row.select_one("a.replyNum") or  # 테이블 형식
                    row.select_one(".reply_count")
                )
                if comment_elem:
                    text = comment_elem.get_text(strip=True)
                    # 대괄호/괄호 제거: [15] -> 15, (15) -> 15
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

    async def close(self):
        """클라이언트 연결 종료"""
        await self.client.aclose()
