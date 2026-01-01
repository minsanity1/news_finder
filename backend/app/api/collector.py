from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from app.database import get_db
from app.database.repository import NewsRepository
from app.collector.rss import RSSCollector, collected_news_to_dict
from app.collector.sources import get_sources_info
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class CollectorStatus(BaseModel):
    is_running: bool
    last_run: Optional[str]
    last_collected_count: int


# 간단한 상태 저장
_collector_state = {
    "is_running": False,
    "last_run": None,
    "last_collected_count": 0
}


async def run_collection(db: AsyncSession):
    """백그라운드에서 뉴스 수집 실행"""
    global _collector_state

    _collector_state["is_running"] = True

    try:
        collector = RSSCollector()
        collected_news = await collector.collect_all()

        # DB에 저장
        repo = NewsRepository(db)
        news_dicts = [collected_news_to_dict(news) for news in collected_news]
        saved_news = await repo.create_many(news_dicts)

        _collector_state["last_collected_count"] = len(saved_news)
        _collector_state["last_run"] = datetime.utcnow().isoformat()

        print(f"[Collector] Saved {len(saved_news)} new news items")

    except Exception as e:
        print(f"[Collector] Error: {e}")

    finally:
        _collector_state["is_running"] = False


@router.post("/run")
async def run_collector(
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """수동 수집 실행"""
    if _collector_state["is_running"]:
        return {
            "message": "Collection already in progress",
            "status": "running"
        }

    # 백그라운드에서 수집 실행
    collector = RSSCollector()
    collected_news = await collector.collect_all()

    # DB에 저장
    repo = NewsRepository(db)
    news_dicts = [collected_news_to_dict(news) for news in collected_news]
    saved_news = await repo.create_many(news_dicts)

    _collector_state["last_collected_count"] = len(saved_news)
    _collector_state["last_run"] = datetime.utcnow().isoformat()

    return {
        "message": "Collection completed",
        "collected_count": len(collected_news),
        "saved_count": len(saved_news),
        "status": "completed"
    }


@router.get("/status", response_model=CollectorStatus)
async def get_collector_status():
    """수집 상태 조회"""
    return CollectorStatus(
        is_running=_collector_state["is_running"],
        last_run=_collector_state["last_run"],
        last_collected_count=_collector_state["last_collected_count"]
    )


@router.get("/sources")
async def get_collector_sources():
    """수집 소스 목록 조회"""
    sources = get_sources_info()
    return {"sources": sources}
