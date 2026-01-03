"""클리앙 추천글 크롤러"""

import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Post:
    """게시글 정보"""
    title: str
    link: str
    likes: int
    comments: int
    views: int
    author: str
    timestamp: datetime
    board: str


class ClienScraper:
    """클리앙 추천글 스크래퍼"""

    BASE_URL = "https://www.clien.net"
    RECOMMEND_URL = f"{BASE_URL}/service/recommend"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def fetch_recommend_page(self, page: int = 0) -> str:
        """추천글 페이지 HTML 가져오기"""
        url = self.RECOMMEND_URL
        if page > 0:
            url = f"{url}?po={page}"

        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    def parse_post(self, item) -> Optional[Post]:
        """게시글 아이템 파싱"""
        try:
            # 제목 (title 속성에 전체 제목)
            subject_elem = item.select_one("span.subject_fixed")
            title = subject_elem.get("title", "").strip() if subject_elem else ""
            if not title:
                title = subject_elem.get_text(strip=True) if subject_elem else ""

            # 링크
            link_elem = item.select_one("a.list_subject")
            link = link_elem.get("href", "") if link_elem else ""
            if link and not link.startswith("http"):
                link = self.BASE_URL + link

            # 공감수
            likes_elem = item.select_one("div.list_symph span")
            likes = self._parse_int(likes_elem.get_text(strip=True)) if likes_elem else 0

            # 댓글수
            comments_elem = item.select_one("span.rSymph05")
            comments = self._parse_int(comments_elem.get_text(strip=True)) if comments_elem else 0

            # 조회수
            views_elem = item.select_one("span.hit")
            views = self._parse_int(views_elem.get_text(strip=True)) if views_elem else 0

            # 작성자
            author_elem = item.select_one("div.list_author span.nickname span")
            author = author_elem.get_text(strip=True) if author_elem else ""

            # 시간 (2026-01-03 12:33:26 형식)
            timestamp_elem = item.select_one("span.timestamp")
            timestamp_str = timestamp_elem.get_text(strip=True) if timestamp_elem else ""
            timestamp = self._parse_timestamp(timestamp_str)

            # 게시판
            board_elem = item.select_one("span.shortname")
            board = board_elem.get_text(strip=True) if board_elem else ""

            return Post(
                title=title,
                link=link,
                likes=likes,
                comments=comments,
                views=views,
                author=author,
                timestamp=timestamp,
                board=board,
            )
        except Exception as e:
            print(f"파싱 오류: {e}")
            return None

    def _parse_int(self, text: str) -> int:
        """숫자 문자열 파싱"""
        try:
            # 쉼표 제거 후 정수 변환
            return int(text.replace(",", "").strip())
        except (ValueError, AttributeError):
            return 0

    def _parse_timestamp(self, text: str) -> datetime:
        """타임스탬프 파싱"""
        try:
            return datetime.strptime(text.strip(), "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return datetime.now()

    def scrape_recommend(self, page: int = 0) -> list[Post]:
        """추천글 목록 스크래핑"""
        html = self.fetch_recommend_page(page)
        soup = BeautifulSoup(html, "lxml")

        # 게시글 목록 컨테이너
        container = soup.select_one("div.recommend_underList")
        if not container:
            return []

        # 각 게시글 아이템
        items = container.select("div.list_item.symph_row")

        posts = []
        for item in items:
            post = self.parse_post(item)
            if post:
                posts.append(post)

        return posts

    def scrape_multiple_pages(self, pages: int = 3) -> list[Post]:
        """여러 페이지 스크래핑"""
        all_posts = []
        for page in range(pages):
            posts = self.scrape_recommend(page)
            all_posts.extend(posts)
            print(f"페이지 {page + 1}: {len(posts)}개 게시글")
        return all_posts


def main():
    """메인 함수"""
    scraper = ClienScraper()

    print("클리앙 추천글 크롤링 시작...")
    posts = scraper.scrape_recommend()

    print(f"\n총 {len(posts)}개 게시글 수집\n")

    for i, post in enumerate(posts[:10], 1):
        print(f"{i}. [{post.board}] {post.title}")
        print(f"   공감: {post.likes} | 댓글: {post.comments} | 조회: {post.views}")
        print(f"   작성자: {post.author} | {post.timestamp}")
        print(f"   {post.link}\n")


if __name__ == "__main__":
    main()
