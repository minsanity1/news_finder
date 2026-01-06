"""
네이버 뉴스 랭킹 수집 API
"""
from datetime import date, datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.repository import NewsRepository
from app.collector.naver_ranking_collector import NaverRankingCollector
from app.collector.ranking_config import (
    PRESS_LIST,
    PRESS_MAP,
    RANKING_TYPES,
    get_enabled_press,
)

router = APIRouter()


# ========== Request/Response Models ==========

class CollectRequest(BaseModel):
    press_ids: Optional[List[str]] = None    # None이면 전체
    ranking_type: str = "popular"            # "popular" | "comment" | "all"
    target_date: Optional[str] = None        # "YYYY-MM-DD" 형식
    limit_per_press: int = 10
    save_to_db: bool = True


class CollectResponse(BaseModel):
    collected: int
    saved: int
    duplicates: int
    by_press: dict


class PressInfoResponse(BaseModel):
    id: str
    name: str
    category: str
    priority: int
    enabled: bool


class RankingNewsResponse(BaseModel):
    rank: int
    title: str
    url: str
    source: str
    category: str
    ranking_type: str
    view_count: Optional[int]
    comment_count: Optional[int]


# ========== Endpoints ==========

@router.get("/press-list")
async def get_press_list() -> List[PressInfoResponse]:
    """수집 가능한 언론사 목록"""
    return [
        PressInfoResponse(
            id=p.id,
            name=p.name,
            category=p.category,
            priority=p.priority,
            enabled=p.enabled
        )
        for p in PRESS_LIST
    ]


@router.get("/ranking-types")
async def get_ranking_types() -> dict:
    """랭킹 타입 목록"""
    return RANKING_TYPES


@router.post("/collect", response_model=CollectResponse)
async def collect_ranking_news(
    request: CollectRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    랭킹 뉴스 수집

    - press_ids: 수집할 언론사 ID 리스트 (비우면 전체)
    - ranking_type: "popular" (조회수), "comment" (댓글수), "all" (둘 다)
    - target_date: 수집 날짜 (YYYY-MM-DD, 비우면 오늘)
    - limit_per_press: 언론사당 수집 개수 (기본 10)
    - save_to_db: DB 저장 여부
    """

    # 날짜 파싱
    target_date = None
    if request.target_date:
        try:
            target_date = date.fromisoformat(request.target_date)
        except ValueError:
            raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")

    collector = NaverRankingCollector()

    try:
        # 수집
        if request.ranking_type == "all":
            results = await collector.get_all_rankings(
                press_ids=request.press_ids,
                target_date=target_date,
                limit_per_press=request.limit_per_press
            )
            all_news = results.get("popular", []) + results.get("comment", [])
        else:
            if request.ranking_type not in RANKING_TYPES:
                raise HTTPException(400, f"Unknown ranking_type: {request.ranking_type}")

            all_news = await collector.get_rankings_by_press_list(
                press_ids=request.press_ids,
                ranking_type=request.ranking_type,
                target_date=target_date,
                limit_per_press=request.limit_per_press
            )

        collected = len(all_news)
        saved = 0
        duplicates = 0
        by_press = {}

        if request.save_to_db and all_news:
            news_repo = NewsRepository(db)

            # URL 기준 중복 제거
            seen_urls = set()
            unique_news = []
            for news in all_news:
                if news.url not in seen_urls:
                    seen_urls.add(news.url)
                    unique_news.append(news)

            for news in unique_news:
                news_dict = collector.to_news_dict(news)
                news_dict["collected_at"] = datetime.utcnow()

                # 언론사별 카운트 초기화
                if news.source not in by_press:
                    by_press[news.source] = 0

                # DB 중복 체크 및 카운트 병합
                try:
                    existing = await news_repo.get_by_url(news_dict["url"])
                    if existing:
                        # 기존 레코드가 있으면 카운트 병합
                        update_data = {}
                        if news_dict.get("view_count") and not existing.view_count:
                            update_data["view_count"] = news_dict["view_count"]
                        if news_dict.get("comment_count") and not existing.comment_count:
                            update_data["comment_count"] = news_dict["comment_count"]

                        if update_data:
                            # 새로운 카운트가 있으면 업데이트
                            await news_repo.update(existing.id, update_data)
                            saved += 1  # 업데이트도 saved로 카운트
                            by_press[news.source] += 1
                        else:
                            duplicates += 1
                        continue

                    await news_repo.create(news_dict)
                    saved += 1
                    by_press[news.source] += 1
                except Exception as e:
                    print(f"[Ranking] Error saving: {e}")
                    continue

        return CollectResponse(
            collected=collected,
            saved=saved,
            duplicates=duplicates,
            by_press=by_press
        )

    finally:
        await collector.close()


@router.post("/collect/single/{press_id}")
async def collect_single_press(
    press_id: str,
    ranking_type: str = Query("popular", pattern="^(popular|comment)$"),
    target_date: Optional[str] = None,
    limit: int = Query(10, ge=1, le=30),
    save_to_db: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """단일 언론사 랭킹 수집"""

    if press_id not in PRESS_MAP:
        raise HTTPException(404, f"Unknown press_id: {press_id}")

    return await collect_ranking_news(
        CollectRequest(
            press_ids=[press_id],
            ranking_type=ranking_type,
            target_date=target_date,
            limit_per_press=limit,
            save_to_db=save_to_db
        ),
        db
    )


@router.get("/preview/{press_id}")
async def preview_ranking(
    press_id: str,
    ranking_type: str = Query("popular", pattern="^(popular|comment)$"),
    target_date: Optional[str] = None,
    limit: int = Query(10, ge=1, le=30)
) -> List[RankingNewsResponse]:
    """
    랭킹 미리보기 (DB 저장 없이)

    Returns:
        랭킹 뉴스 리스트
    """
    if press_id not in PRESS_MAP:
        raise HTTPException(404, f"Unknown press_id: {press_id}")

    parsed_date = None
    if target_date:
        try:
            parsed_date = date.fromisoformat(target_date)
        except ValueError:
            raise HTTPException(400, "Invalid date format. Use YYYY-MM-DD")

    collector = NaverRankingCollector()

    try:
        news_list = await collector.get_ranking(
            press_id=press_id,
            ranking_type=ranking_type,
            target_date=parsed_date,
            limit=limit
        )

        return [
            RankingNewsResponse(
                rank=n.rank,
                title=n.title,
                url=n.url,
                source=n.source,
                category=n.category,
                ranking_type=n.ranking_type,
                view_count=n.view_count,
                comment_count=n.comment_count,
            )
            for n in news_list
        ]

    finally:
        await collector.close()


@router.get("/status")
async def get_ranking_status():
    """랭킹 수집 상태"""
    enabled = get_enabled_press()

    by_category = {}
    for p in enabled:
        if p.category not in by_category:
            by_category[p.category] = 0
        by_category[p.category] += 1

    return {
        "total_press": len(PRESS_LIST),
        "enabled_press": len(enabled),
        "by_category": by_category,
        "ranking_types": list(RANKING_TYPES.keys()),
    }
