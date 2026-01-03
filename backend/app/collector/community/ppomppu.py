"""
뽐뿌 수집기
"""
from datetime import datetime, timedelta
from typing import List, Optional
import re

from bs4 import BeautifulSoup

from .base import BaseCommunityCollector, CommunityPost
from .config import COMMUNITY_BOARDS


class PpomppuCollector(BaseCommunityCollector):
    """뽐뿌 커뮤니티 수집기"""

    SOURCE_NAME = "뽐뿌"
    BASE_URL = "https://www.ppomppu.co.kr"
    REQUEST_DELAY = (1.0, 2.0)

    def _get_board_url(self, board_id: str, page: int = 1) -> str:
        """게시판 URL 생성"""
        config = COMMUNITY_BOARDS.get("ppomppu", {})
        for board in config.get("boards", []):
            if board["id"] == board_id:
                path = board['path']
                # hot.php는 page 파라미터가 다름
                if "hot.php" in path:
                    if page > 1:
                        return f"{self.BASE_URL}/{path}&page={page}"
                    return f"{self.BASE_URL}/{path}"
                return f"{self.BASE_URL}/{path}&page={page}"

        # 기본값
        return f"{self.BASE_URL}/hot.php?category=2&page={page}"

    async def get_board_list(self, board_id: str, page: int = 1) -> List[dict]:
        """게시판 글 목록 파싱 (hot.php용)"""
        url = self._get_board_url(board_id, page)
        print(f"[{self.SOURCE_NAME}] Fetching: {url}")

        try:
            response = await self._request_with_delay(url)
            response.raise_for_status()
        except Exception as e:
            print(f"[{self.SOURCE_NAME}] Request failed: {e}")
            return []

        # 뽐뿌는 EUC-KR 인코딩 사용
        try:
            content = response.content.decode("euc-kr", errors="replace")
        except:
            content = response.text

        soup = BeautifulSoup(content, "html.parser")
        posts = []

        # hot.php 구조: <tr class="baseList ...">
        rows = soup.select("tr.baseList")
        print(f"[{self.SOURCE_NAME}] Found {len(rows)} rows")

        for row in rows:
            try:
                # 제목 링크: a.baseList-title
                title_elem = row.select_one("a.baseList-title")
                if not title_elem:
                    continue

                # 제목 텍스트 (이미지 제외)
                title = title_elem.get_text(strip=True)
                # 앞의 아이콘 텍스트 제거
                title = re.sub(r'^(AD|hot)\s*', '', title)

                href = title_elem.get("href", "")
                if not href or not title:
                    continue

                # AD(광고) 게시글 스킵
                if row.select_one("span#ad-icon"):
                    continue

                # URL 정규화
                if href.startswith("/"):
                    full_url = self.BASE_URL + href
                elif not href.startswith("http"):
                    full_url = f"{self.BASE_URL}/{href}"
                else:
                    full_url = href

                # 댓글수: span.list_comment2
                comment_count = 0
                comment_elem = row.select_one("span.list_comment2")
                if comment_elem:
                    num = re.sub(r"[^\d]", "", comment_elem.get_text())
                    comment_count = int(num) if num else 0

                # td.board_date 컬럼들에서 조회수, 추천수 파싱
                # 순서: 날짜, 추천-비추천, 조회수
                date_tds = row.select("td.board_date")
                view_count = 0
                like_count = 0

                if len(date_tds) >= 3:
                    # 마지막 td가 조회수
                    view_text = date_tds[-1].get_text(strip=True)
                    view_num = re.sub(r"[^\d]", "", view_text)
                    view_count = int(view_num) if view_num else 0

                    # 두번째가 추천-비추천 (예: "8 - 0")
                    like_text = date_tds[-2].get_text(strip=True)
                    like_match = re.match(r"(\d+)\s*-\s*(\d+)", like_text)
                    if like_match:
                        like_count = int(like_match.group(1))

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

        print(f"[{self.SOURCE_NAME}] Parsed {len(posts)} posts")
        return posts

    def _extract_number(self, element, keywords: List[str]) -> int:
        """요소에서 키워드 관련 숫자 추출"""
        text = element.get_text()

        # 키워드 근처의 숫자 찾기
        for keyword in keywords:
            pattern = rf"{keyword}[:\s]*(\d[\d,]*)"
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return int(match.group(1).replace(",", ""))

        # span/div에서 숫자 클래스 찾기
        for span in element.select("span, div, td"):
            cls = " ".join(span.get("class", []))
            for keyword in keywords:
                if keyword in cls.lower():
                    num = re.sub(r"[^\d]", "", span.get_text())
                    if num:
                        return int(num)

        return 0

    async def get_post_detail(self, post_url: str) -> CommunityPost:
        """게시글 상세 파싱"""
        try:
            response = await self._request_with_delay(post_url)
            response.raise_for_status()
        except Exception as e:
            raise Exception(f"Request failed: {e}")

        # 뽐뿌는 EUC-KR 인코딩 사용
        try:
            content_html = response.content.decode("euc-kr", errors="replace")
        except:
            content_html = response.text

        soup = BeautifulSoup(content_html, "html.parser")

        # 제목
        title_elem = (
            soup.select_one("h2.view-title") or
            soup.select_one("td.view_title") or
            soup.select_one("font.view_title")
        )
        title = title_elem.get_text(strip=True) if title_elem else ""

        # 본문
        content_div = (
            soup.select_one("div.view-content") or
            soup.select_one("td.board-contents") or
            soup.select_one("td.han")
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

        # 메타 정보
        view_count = self._parse_meta_from_page(soup, "조회")
        like_count = self._parse_meta_from_page(soup, "추천")

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

    def _parse_count_from_row(self, row, td_index: int) -> int:
        """테이블 행에서 특정 인덱스의 td 값 파싱"""
        tds = row.select("td")
        if len(tds) > td_index:
            text = tds[td_index].get_text(strip=True)
            num = re.sub(r"[^\d]", "", text)
            return int(num) if num else 0
        return 0

    def _parse_comment_count(self, row, title_elem) -> int:
        """댓글수 파싱"""
        # 제목 옆 댓글 수 (보통 빨간색 숫자)
        comment_elem = row.select_one("span.list_comment2, font.list_comment2")
        if comment_elem:
            text = comment_elem.get_text(strip=True)
            num = re.sub(r"[^\d]", "", text)
            return int(num) if num else 0

        # 제목 내 [숫자] 패턴
        title_text = title_elem.get_text() if title_elem else ""
        match = re.search(r"\[(\d+)\]", title_text)
        if match:
            return int(match.group(1))

        return 0

    def _parse_datetime(self, soup) -> Optional[datetime]:
        """작성 시간 파싱"""
        # 여러 선택자 시도
        time_elem = (
            soup.select_one("span.view-time") or
            soup.select_one("td.view_time") or
            soup.select_one("font.view_time")
        )

        if not time_elem:
            # 테이블 내 날짜 찾기
            for td in soup.select("td"):
                text = td.get_text(strip=True)
                if re.match(r"\d{2,4}[./\-]\d{2}[./\-]\d{2}", text):
                    time_elem = td
                    break

        if not time_elem:
            return datetime.now()

        text = time_elem.get_text(strip=True)

        # "2025-01-02 14:30:00" 형식
        try:
            return datetime.strptime(text[:19], "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

        # "2025.01.02 14:30" 형식
        try:
            return datetime.strptime(text[:16], "%Y.%m.%d %H:%M")
        except ValueError:
            pass

        # "25/01/02 14:30" 형식
        try:
            return datetime.strptime(text[:14], "%y/%m/%d %H:%M")
        except ValueError:
            pass

        # "01-02 14:30" 형식 (올해)
        try:
            dt = datetime.strptime(text[:11], "%m-%d %H:%M")
            return dt.replace(year=datetime.now().year)
        except ValueError:
            pass

        return datetime.now()

    def _parse_author(self, soup) -> Optional[str]:
        """작성자 파싱"""
        author_elem = (
            soup.select_one("span.view-name") or
            soup.select_one("td.view_name a") or
            soup.select_one("font.view_name")
        )
        if author_elem:
            return author_elem.get_text(strip=True)
        return None

    def _parse_meta_from_page(self, soup, label: str) -> int:
        """페이지에서 메타 정보 파싱"""
        # "조회: 1234" 또는 "조회 1234" 형태
        for elem in soup.select("td, span, font, div"):
            text = elem.get_text(strip=True)
            if label in text and len(text) < 50:  # 너무 긴 텍스트 제외
                num = re.search(r"(\d[\d,]*)", text)
                if num:
                    return int(num.group(1).replace(",", ""))

        return 0
