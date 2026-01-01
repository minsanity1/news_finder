from dataclasses import dataclass
from typing import List


@dataclass
class RSSSource:
    name: str
    url: str
    category: str
    enabled: bool = True


# RSS 소스 목록
RSS_SOURCES: List[RSSSource] = [
    # 종합
    RSSSource(
        name="연합뉴스",
        url="https://www.yonhapnewstv.co.kr/browse/feed/",
        category="종합",
        enabled=True
    ),
    RSSSource(
        name="한겨레",
        url="https://www.hani.co.kr/rss/",
        category="종합",
        enabled=True
    ),

    # 경제/비즈니스
    RSSSource(
        name="조선일보 경제",
        url="https://www.chosun.com/arc/outboundfeeds/rss/category/economy/",
        category="경제",
        enabled=True
    ),
    RSSSource(
        name="한국경제",
        url="https://www.hankyung.com/feed/all-news",
        category="경제",
        enabled=True
    ),
    RSSSource(
        name="매일경제",
        url="https://www.mk.co.kr/rss/30000001/",
        category="경제",
        enabled=True
    ),

    # IT/테크
    RSSSource(
        name="ZDNet Korea",
        url="https://zdnet.co.kr/rss/news.xml",
        category="IT",
        enabled=True
    ),
    RSSSource(
        name="전자신문",
        url="https://rss.etnews.com/Section901.xml",
        category="IT",
        enabled=True
    ),
    RSSSource(
        name="블로터",
        url="https://www.bloter.net/feed",
        category="IT",
        enabled=True
    ),

    # 스타트업/창업
    RSSSource(
        name="플래텀",
        url="https://platum.kr/feed",
        category="스타트업",
        enabled=True
    ),
    RSSSource(
        name="벤처스퀘어",
        url="https://www.venturesquare.net/feed",
        category="스타트업",
        enabled=True
    ),
]


def get_enabled_sources() -> List[RSSSource]:
    return [source for source in RSS_SOURCES if source.enabled]


def get_sources_info() -> List[dict]:
    return [
        {
            "name": source.name,
            "url": source.url,
            "category": source.category,
            "enabled": source.enabled
        }
        for source in RSS_SOURCES
    ]
