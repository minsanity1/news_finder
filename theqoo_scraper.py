"""더쿠 인기글 크롤러"""

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
    comments: int
    views: int
    category: str
    date: str
    has_image: bool
    has_youtube: bool
    has_twitter: bool


class TheqooScraper:
    """더쿠 인기글 스크래퍼"""

    BASE_URL = "https://theqoo.net"
    HOT_URL = f"{BASE_URL}/hot"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def fetch_hot_page(self, page: int = 1) -> str:
        """인기글 페이지 HTML 가져오기"""
        url = self.HOT_URL
        if page > 1:
            url = f"{url}?page={page}"

        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    def parse_post(self, row) -> Optional[Post]:
        """게시글 row 파싱"""
        try:
            # 공지 제외
            if "notice" in row.get("class", []):
                return None

            # 제목 (첫 번째 a 태그)
            title_elem = row.select_one("td.title > a")
            title = title_elem.get_text(strip=True) if title_elem else ""

            # 링크
            link = title_elem.get("href", "") if title_elem else ""
            if link and not link.startswith("http"):
                link = self.BASE_URL + link

            # 댓글수
            comments_elem = row.select_one("a.replyNum")
            comments = self._parse_int(comments_elem.get_text(strip=True)) if comments_elem else 0

            # 조회수
            views_elem = row.select_one("td.m_no")
            views = self._parse_int(views_elem.get_text(strip=True)) if views_elem else 0

            # 카테고리
            category_elem = row.select_one("td.cate span")
            category = category_elem.get_text(strip=True) if category_elem else ""

            # 날짜
            date_elem = row.select_one("td.time")
            date = date_elem.get_text(strip=True) if date_elem else ""

            # 미디어 여부
            has_image = row.select_one("td.title i.fas.fa-images") is not None
            has_youtube = row.select_one("td.title i.fab.fa-youtube") is not None
            has_twitter = row.select_one("td.title i.fab.fa-twitter") is not None

            return Post(
                title=title,
                link=link,
                comments=comments,
                views=views,
                category=category,
                date=date,
                has_image=has_image,
                has_youtube=has_youtube,
                has_twitter=has_twitter,
            )
        except Exception as e:
            print(f"파싱 오류: {e}")
            return None

    def _parse_int(self, text: str) -> int:
        """숫자 문자열 파싱"""
        try:
            return int(text.replace(",", "").strip())
        except (ValueError, AttributeError):
            return 0

    def scrape_hot(self, page: int = 1) -> list[Post]:
        """인기글 목록 스크래핑"""
        html = self.fetch_hot_page(page)
        soup = BeautifulSoup(html, "lxml")

        # 게시글 테이블
        table = soup.select_one("table.theqoo_board_table tbody")
        if not table:
            return []

        # 각 게시글 row (공지 제외)
        rows = table.select("tr:not(.notice)")

        posts = []
        for row in rows:
            post = self.parse_post(row)
            if post:
                posts.append(post)

        return posts

    def scrape_multiple_pages(self, pages: int = 3) -> list[Post]:
        """여러 페이지 스크래핑"""
        all_posts = []
        for page in range(1, pages + 1):
            posts = self.scrape_hot(page)
            all_posts.extend(posts)
            print(f"페이지 {page}: {len(posts)}개 게시글")
        return all_posts


def main():
    """메인 함수"""
    scraper = TheqooScraper()

    print("더쿠 인기글 크롤링 시작...")
    posts = scraper.scrape_hot()

    print(f"\n총 {len(posts)}개 게시글 수집\n")

    for i, post in enumerate(posts[:10], 1):
        media = []
        if post.has_image:
            media.append("이미지")
        if post.has_youtube:
            media.append("유튜브")
        if post.has_twitter:
            media.append("트위터")
        media_str = f" [{', '.join(media)}]" if media else ""

        print(f"{i}. [{post.category}] {post.title}{media_str}")
        print(f"   댓글: {post.comments} | 조회: {post.views} | {post.date}")
        print(f"   {post.link}\n")


if __name__ == "__main__":
    main()
