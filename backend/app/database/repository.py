from datetime import datetime
from typing import List, Optional
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import News, FilterPreset, AIAnalysisLog


class NewsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, news_data: dict) -> News:
        news = News(**news_data)
        self.session.add(news)
        await self.session.commit()
        await self.session.refresh(news)
        return news

    async def create_many(self, news_list: List[dict]) -> List[News]:
        news_objects = []
        for news_data in news_list:
            existing = await self.get_by_url(news_data.get("url", ""))
            if not existing:
                news = News(**news_data)
                self.session.add(news)
                news_objects.append(news)

        if news_objects:
            await self.session.commit()
            for news in news_objects:
                await self.session.refresh(news)

        return news_objects

    async def get_by_id(self, news_id: int) -> Optional[News]:
        result = await self.session.execute(
            select(News).where(News.id == news_id)
        )
        return result.scalar_one_or_none()

    async def get_by_url(self, url: str) -> Optional[News]:
        result = await self.session.execute(
            select(News).where(News.url == url)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        keyword: Optional[str] = None,
        source: Optional[str] = None,
        category: Optional[str] = None,
        ai_min_score: Optional[int] = None,
        ai_category: Optional[str] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        is_bookmarked: Optional[bool] = None,
        is_read: Optional[bool] = None,
        page: int = 1,
        limit: int = 20
    ) -> tuple[List[News], int]:
        query = select(News)
        conditions = []

        if keyword:
            conditions.append(
                or_(
                    News.title.ilike(f"%{keyword}%"),
                    News.summary.ilike(f"%{keyword}%")
                )
            )

        if source:
            conditions.append(News.source == source)

        if category:
            conditions.append(News.category == category)

        if ai_min_score is not None:
            conditions.append(News.ai_score >= ai_min_score)

        if ai_category:
            conditions.append(News.ai_category == ai_category)

        if from_date:
            conditions.append(News.published_at >= from_date)

        if to_date:
            conditions.append(News.published_at <= to_date)

        if is_bookmarked is not None:
            conditions.append(News.is_bookmarked == is_bookmarked)

        if is_read is not None:
            conditions.append(News.is_read == is_read)

        if conditions:
            query = query.where(and_(*conditions))

        # Count total
        count_query = select(News.id)
        if conditions:
            count_query = count_query.where(and_(*conditions))
        count_result = await self.session.execute(count_query)
        total = len(count_result.all())

        # Get paginated results
        query = query.order_by(desc(News.published_at))
        query = query.offset((page - 1) * limit).limit(limit)

        result = await self.session.execute(query)
        news_list = result.scalars().all()

        return news_list, total

    async def update(self, news_id: int, update_data: dict) -> Optional[News]:
        news = await self.get_by_id(news_id)
        if not news:
            return None

        for key, value in update_data.items():
            if hasattr(news, key):
                setattr(news, key, value)

        await self.session.commit()
        await self.session.refresh(news)
        return news

    async def delete(self, news_id: int) -> bool:
        news = await self.get_by_id(news_id)
        if not news:
            return False

        await self.session.delete(news)
        await self.session.commit()
        return True

    async def get_unanalyzed(self, limit: int = 10) -> List[News]:
        result = await self.session.execute(
            select(News)
            .where(News.ai_analyzed == False)
            .order_by(desc(News.published_at))
            .limit(limit)
        )
        return result.scalars().all()

    async def get_sources(self) -> List[str]:
        result = await self.session.execute(
            select(News.source).distinct().where(News.source.isnot(None))
        )
        return [r[0] for r in result.all()]

    async def get_categories(self) -> List[str]:
        result = await self.session.execute(
            select(News.category).distinct().where(News.category.isnot(None))
        )
        return [r[0] for r in result.all()]


class FilterPresetRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, preset_data: dict) -> FilterPreset:
        preset = FilterPreset(**preset_data)
        self.session.add(preset)
        await self.session.commit()
        await self.session.refresh(preset)
        return preset

    async def get_by_id(self, preset_id: int) -> Optional[FilterPreset]:
        result = await self.session.execute(
            select(FilterPreset).where(FilterPreset.id == preset_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self) -> List[FilterPreset]:
        result = await self.session.execute(
            select(FilterPreset).order_by(FilterPreset.created_at)
        )
        return result.scalars().all()

    async def update(self, preset_id: int, update_data: dict) -> Optional[FilterPreset]:
        preset = await self.get_by_id(preset_id)
        if not preset:
            return None

        for key, value in update_data.items():
            if hasattr(preset, key):
                setattr(preset, key, value)

        await self.session.commit()
        await self.session.refresh(preset)
        return preset

    async def delete(self, preset_id: int) -> bool:
        preset = await self.get_by_id(preset_id)
        if not preset:
            return False

        await self.session.delete(preset)
        await self.session.commit()
        return True


class AIAnalysisLogRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, log_data: dict) -> AIAnalysisLog:
        log = AIAnalysisLog(**log_data)
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log

    async def get_usage_stats(self) -> dict:
        from sqlalchemy import func

        today = datetime.utcnow().date()

        # Today's usage
        today_result = await self.session.execute(
            select(func.count(AIAnalysisLog.id))
            .where(func.date(AIAnalysisLog.created_at) == today)
        )
        today_count = today_result.scalar() or 0

        # Total usage
        total_result = await self.session.execute(
            select(func.count(AIAnalysisLog.id))
        )
        total_count = total_result.scalar() or 0

        return {
            "today": today_count,
            "total": total_count
        }
