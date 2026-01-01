from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime

from app.config import get_settings
from app.collector.rss import RSSCollector, collected_news_to_dict
from app.database import AsyncSessionLocal
from app.database.repository import NewsRepository

settings = get_settings()

scheduler = AsyncIOScheduler()


async def scheduled_collection():
    """스케줄된 뉴스 수집 작업"""
    print(f"[Scheduler] Starting scheduled collection at {datetime.utcnow()}")

    try:
        async with AsyncSessionLocal() as session:
            collector = RSSCollector()
            collected_news = await collector.collect_all()

            repo = NewsRepository(session)
            news_dicts = [collected_news_to_dict(news) for news in collected_news]
            saved_news = await repo.create_many(news_dicts)

            print(f"[Scheduler] Collected {len(collected_news)}, saved {len(saved_news)} new items")

    except Exception as e:
        print(f"[Scheduler] Error during collection: {e}")


def start_scheduler():
    """스케줄러 시작"""
    if not scheduler.running:
        # 주기적 뉴스 수집 작업 추가
        scheduler.add_job(
            scheduled_collection,
            trigger=IntervalTrigger(minutes=settings.collect_interval_minutes),
            id="news_collection",
            name="RSS News Collection",
            replace_existing=True
        )

        scheduler.start()
        print(f"[Scheduler] Started with {settings.collect_interval_minutes} minute interval")


def shutdown_scheduler():
    """스케줄러 종료"""
    if scheduler.running:
        scheduler.shutdown()
        print("[Scheduler] Shutdown complete")


def get_scheduler_status():
    """스케줄러 상태 조회"""
    return {
        "running": scheduler.running,
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in scheduler.get_jobs()
        ]
    }
