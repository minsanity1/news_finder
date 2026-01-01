from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from app.database import get_db
from app.database.repository import NewsRepository
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class NewsUpdateRequest(BaseModel):
    is_read: Optional[bool] = None
    is_bookmarked: Optional[bool] = None
    is_used: Optional[bool] = None


class NewsResponse(BaseModel):
    id: int
    title: str
    summary: Optional[str]
    content: Optional[str]
    url: str
    source: Optional[str]
    category: Optional[str]
    published_at: Optional[str]
    collected_at: Optional[str]
    is_read: bool
    is_bookmarked: bool
    is_used: bool
    ai_analyzed: bool
    ai_score: Optional[int]
    ai_category: Optional[str]
    ai_reason: Optional[str]
    ai_key_points: Optional[List[str]]
    ai_youtube_potential: Optional[str]
    ai_analyzed_at: Optional[str]


class NewsListResponse(BaseModel):
    items: List[NewsResponse]
    total: int
    page: int
    limit: int
    total_pages: int


@router.get("", response_model=NewsListResponse)
async def get_news_list(
    keyword: Optional[str] = None,
    source: Optional[str] = None,
    category: Optional[str] = None,
    ai_min_score: Optional[int] = None,
    ai_category: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    is_bookmarked: Optional[bool] = None,
    is_read: Optional[bool] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """뉴스 목록 조회 (필터 적용)"""
    repo = NewsRepository(db)

    # 날짜 파싱
    parsed_from_date = None
    parsed_to_date = None

    if from_date:
        try:
            parsed_from_date = datetime.fromisoformat(from_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid from_date format")

    if to_date:
        try:
            parsed_to_date = datetime.fromisoformat(to_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid to_date format")

    news_list, total = await repo.get_all(
        keyword=keyword,
        source=source,
        category=category,
        ai_min_score=ai_min_score,
        ai_category=ai_category,
        from_date=parsed_from_date,
        to_date=parsed_to_date,
        is_bookmarked=is_bookmarked,
        is_read=is_read,
        page=page,
        limit=limit
    )

    total_pages = (total + limit - 1) // limit

    return NewsListResponse(
        items=[NewsResponse(**news.to_dict()) for news in news_list],
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )


@router.get("/sources")
async def get_sources(db: AsyncSession = Depends(get_db)):
    """수집된 뉴스의 언론사 목록"""
    repo = NewsRepository(db)
    sources = await repo.get_sources()
    return {"sources": sources}


@router.get("/categories")
async def get_categories(db: AsyncSession = Depends(get_db)):
    """수집된 뉴스의 카테고리 목록"""
    repo = NewsRepository(db)
    categories = await repo.get_categories()
    return {"categories": categories}


@router.get("/{news_id}", response_model=NewsResponse)
async def get_news_detail(
    news_id: int,
    db: AsyncSession = Depends(get_db)
):
    """뉴스 상세 조회"""
    repo = NewsRepository(db)
    news = await repo.get_by_id(news_id)

    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    return NewsResponse(**news.to_dict())


@router.patch("/{news_id}", response_model=NewsResponse)
async def update_news(
    news_id: int,
    update_data: NewsUpdateRequest,
    db: AsyncSession = Depends(get_db)
):
    """뉴스 상태 업데이트 (읽음, 북마크 등)"""
    repo = NewsRepository(db)

    update_dict = update_data.model_dump(exclude_unset=True)
    news = await repo.update(news_id, update_dict)

    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    return NewsResponse(**news.to_dict())


@router.delete("/{news_id}")
async def delete_news(
    news_id: int,
    db: AsyncSession = Depends(get_db)
):
    """뉴스 삭제"""
    repo = NewsRepository(db)
    success = await repo.delete(news_id)

    if not success:
        raise HTTPException(status_code=404, detail="News not found")

    return {"message": "News deleted successfully"}
