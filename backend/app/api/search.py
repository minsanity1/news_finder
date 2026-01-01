from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime

from app.database import get_db
from app.database.repository import NewsRepository
from app.collector.naver_collector import get_naver_collector
from app.config import get_settings
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()
settings = get_settings()


class SearchRequest(BaseModel):
    query: str
    max_results: int = 100
    sort: str = "date"  # date or sim
    save_to_db: bool = True
    filter_sources: Optional[List[str]] = None  # 언론사 필터 (빈 리스트면 전체)


class SearchResult(BaseModel):
    title: str
    summary: str
    url: str
    source: str
    category: str
    published_at: Optional[str]


class SearchResponse(BaseModel):
    query: str
    total_found: int
    filtered_count: int
    saved_count: int
    items: List[SearchResult]


def extract_source_name(url: str, title: str) -> str:
    """URL이나 제목에서 언론사명 추출"""
    source_patterns = {
        'yna.co.kr': '연합뉴스',
        'yonhapnews': '연합뉴스',
        'hankyung.com': '한국경제',
        'mk.co.kr': '매일경제',
        'etnews.com': '전자신문',
        'chosun.com': '조선일보',
        'joongang.co.kr': '중앙일보',
        'donga.com': '동아일보',
        'hani.co.kr': '한겨레',
        'khan.co.kr': '경향신문',
        'sbs.co.kr': 'SBS',
        'kbs.co.kr': 'KBS',
        'mbc.co.kr': 'MBC',
        'ytn.co.kr': 'YTN',
        'newsis.com': '뉴시스',
        'news1.kr': '뉴스1',
        'edaily.co.kr': '이데일리',
        'mt.co.kr': '머니투데이',
        'sedaily.com': '서울경제',
        'fnnews.com': '파이낸셜뉴스',
        'asiae.co.kr': '아시아경제',
        'heraldcorp.com': '헤럴드경제',
    }

    url_lower = url.lower()
    for pattern, name in source_patterns.items():
        if pattern in url_lower:
            return name
    return "기타"


@router.get("/status")
async def get_search_status():
    """검색 API 상태 확인"""
    collector = get_naver_collector()
    return {
        "naver_api_configured": collector.is_configured(),
        "naver_api_url": "https://developers.naver.com/apps" if not collector.is_configured() else None
    }


@router.post("/naver", response_model=SearchResponse)
async def search_naver(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db)
):
    """네이버 뉴스 검색 및 저장"""
    collector = get_naver_collector()

    if not collector.is_configured():
        raise HTTPException(
            status_code=400,
            detail="Naver API not configured. Set NAVER_CLIENT_ID and NAVER_CLIENT_SECRET in .env"
        )

    # 검색 실행
    items = await collector.search_and_collect(
        query=request.query,
        max_results=request.max_results,
        sort=request.sort
    )

    total_found = len(items)

    # 언론사명 추출 및 source 업데이트
    for item in items:
        detected_source = extract_source_name(item["url"], item["title"])
        item["source"] = detected_source

    # 언론사 필터링
    filtered_items = items
    if request.filter_sources and len(request.filter_sources) > 0:
        filtered_items = [
            item for item in items
            if item["source"] in request.filter_sources
        ]

    saved_count = 0

    # DB에 저장
    if request.save_to_db and filtered_items:
        news_repo = NewsRepository(db)
        for item in filtered_items:
            try:
                # URL 중복 체크
                existing = await news_repo.get_by_url(item["url"])
                if not existing:
                    await news_repo.create({
                        "title": item["title"],
                        "summary": item["summary"],
                        "url": item["url"],
                        "source": item["source"],
                        "category": f"검색: {request.query}",
                        "published_at": item["published_at"],
                        "collected_at": datetime.utcnow()
                    })
                    saved_count += 1
            except Exception as e:
                print(f"[Search] Error saving: {e}")

    return SearchResponse(
        query=request.query,
        total_found=total_found,
        filtered_count=len(filtered_items),
        saved_count=saved_count,
        items=[
            SearchResult(
                title=item["title"],
                summary=item["summary"],
                url=item["url"],
                source=item["source"],
                category=item["category"],
                published_at=item["published_at"].isoformat() if item["published_at"] else None
            )
            for item in filtered_items
        ]
    )


@router.get("/naver/quick")
async def quick_search_naver(
    query: str = Query(..., description="검색어"),
    max_results: int = Query(50, description="최대 결과 수"),
    save: bool = Query(True, description="DB에 저장 여부"),
    db: AsyncSession = Depends(get_db)
):
    """간단한 네이버 뉴스 검색 (GET 방식)"""
    request = SearchRequest(
        query=query,
        max_results=max_results,
        save_to_db=save
    )
    return await search_naver(request, db)


@router.post("/naver/keywords")
async def search_multiple_keywords(
    keywords: List[str],
    max_per_keyword: int = 50,
    save_to_db: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """여러 키워드로 네이버 뉴스 검색"""
    collector = get_naver_collector()

    if not collector.is_configured():
        raise HTTPException(
            status_code=400,
            detail="Naver API not configured"
        )

    items = await collector.search_multiple_keywords(
        keywords=keywords,
        max_per_keyword=max_per_keyword
    )

    saved_count = 0

    if save_to_db and items:
        news_repo = NewsRepository(db)
        for item in items:
            try:
                existing = await news_repo.get_by_url(item["url"])
                if not existing:
                    await news_repo.create({
                        "title": item["title"],
                        "summary": item["summary"],
                        "url": item["url"],
                        "source": item["source"],
                        "category": "검색",
                        "published_at": item["published_at"],
                        "collected_at": datetime.utcnow()
                    })
                    saved_count += 1
            except Exception as e:
                print(f"[Search] Error saving: {e}")

    return {
        "keywords": keywords,
        "total_found": len(items),
        "saved_count": saved_count
    }
