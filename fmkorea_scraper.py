"""에펨코리아 인기글 크롤러"""

import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional


@dataclass
class Post:
    """게시글 정보"""
    title: str
    link: str
    votes: int
    comments: int
    category: str
    author: str
    regdate: str
    is_poten: bool
    thumbnail: Optional[str]


class FmkoreaScraper:
    """에펨코리아 인기글 스크래퍼"""

    BASE_URL = "https://www.fmkorea.com"
    HUMOR_URL = f"{BASE_URL}/humor"

    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(self.HEADERS)

    def fetch_humor_page(self, page: int = 1, sort_by_pop: bool = True) -> str:
        """유머 게시판 HTML 가져오기"""
        url = self.HUMOR_URL
        params = []
        if sort_by_pop:
            params.append("sort_index=pop")
        if page > 1:
            params.append(f"page={page}")
        if params:
            url = f"{url}?{'&'.join(params)}"

        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.text

    def parse_post(self, item) -> Optional[Post]:
        """게시글 아이템 파싱"""
        try:
            # 제목
            title_elem = item.select_one("span.ellipsis-target")
            title = title_elem.get_text(strip=True) if title_elem else ""

            # 링크
            link_elem = item.select_one("h3.title a")
            link = link_elem.get("href", "") if link_elem else ""
            if link and not link.startswith("http"):
                link = self.BASE_URL + link

            # 추천수
            votes_elem = item.select_one("span.count")
            votes = self._parse_int(votes_elem.get_text(strip=True)) if votes_elem else 0

            # 댓글수 (대괄호 제거)
            comments_elem = item.select_one("span.comment_count")
            if comments_elem:
                comments_text = comments_elem.get_text(strip=True)
                comments = self._parse_int(comments_text.strip("[]"))
            else:
                comments = 0

            # 카테고리
            category_elem = item.select_one("span.category a")
            category = category_elem.get_text(strip=True) if category_elem else ""

            # 작성자
            author_elem = item.select_one("span.author")
            author = author_elem.get_text(strip=True) if author_elem else ""

            # 시간
            regdate_elem = item.select_one("span.regdate")
            regdate = regdate_elem.get_text(strip=True) if regdate_elem else ""

            # 포텐 여부
            is_poten = item.select_one("span.STAR-BEST") is not None

            # 썸네일
            thumb_elem = item.select_one("img.thumb")
            thumbnail = None
            if thumb_elem:
                thumbnail = thumb_elem.get("data-original") or thumb_elem.get("src")

            return Post(
                title=title,
                link=link,
                votes=votes,
                comments=comments,
                category=category,
                author=author,
                regdate=regdate,
                is_poten=is_poten,
                thumbnail=thumbnail,
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

    def scrape_humor(self, page: int = 1, sort_by_pop: bool = True) -> list[Post]:
        """유머 게시판 스크래핑"""
        html = self.fetch_humor_page(page, sort_by_pop)
        soup = BeautifulSoup(html, "lxml")

        # 게시글 리스트
        container = soup.select_one("div.fm_best_widget ul")
        if not container:
            return []

        # 각 게시글 아이템
        items = container.select("li.li")

        posts = []
        for item in items:
            post = self.parse_post(item)
            if post:
                posts.append(post)

        return posts

    def scrape_multiple_pages(self, pages: int = 3) -> list[Post]:
        """여러 페이지 스크래핑"""
        all_posts = []
        for page in range(1, pages + 1):
            posts = self.scrape_humor(page)
            all_posts.extend(posts)
            print(f"페이지 {page}: {len(posts)}개 게시글")
        return all_posts


def main():
    """메인 함수"""
    scraper = FmkoreaScraper()

    print("에펨코리아 인기글 크롤링 시작...")
    posts = scraper.scrape_humor()

    print(f"\n총 {len(posts)}개 게시글 수집\n")

    for i, post in enumerate(posts[:10], 1):
        poten_str = " ★포텐" if post.is_poten else ""
        print(f"{i}. [{post.category}] {post.title}{poten_str}")
        print(f"   추천: {post.votes} | 댓글: {post.comments} | {post.regdate}")
        print(f"   작성자: {post.author}")
        print(f"   {post.link}\n")


if __name__ == "__main__":
    main()
