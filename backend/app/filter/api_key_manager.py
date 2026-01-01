from datetime import datetime, date
from typing import Optional, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database.models import AIAnalysisLog

settings = get_settings()


class APIKeyManager:
    """Manages multiple API keys with automatic rotation"""

    def __init__(self):
        self._keys = settings.get_api_keys()
        self._current_index = 0
        self._daily_limit = settings.ai_daily_limit_per_key

    @property
    def total_keys(self) -> int:
        return len(self._keys)

    @property
    def current_key_index(self) -> int:
        return self._current_index

    def has_keys(self) -> bool:
        return len(self._keys) > 0

    def get_current_key(self) -> Optional[str]:
        if not self._keys:
            return None
        return self._keys[self._current_index]

    async def get_key_usage_today(self, session: AsyncSession, key_index: int) -> int:
        """Get usage count for a specific key today"""
        today_start = datetime.combine(date.today(), datetime.min.time())

        result = await session.execute(
            select(func.count(AIAnalysisLog.id))
            .where(AIAnalysisLog.created_at >= today_start)
            .where(AIAnalysisLog.api_key_index == key_index)
        )
        return result.scalar() or 0

    async def get_all_usage_today(self, session: AsyncSession) -> dict:
        """Get usage stats for all keys"""
        today_start = datetime.combine(date.today(), datetime.min.time())

        usage_stats = []
        total_used = 0
        total_remaining = 0

        for i, key in enumerate(self._keys):
            count = await self.get_key_usage_today(session, i)
            remaining = max(0, self._daily_limit - count)
            usage_stats.append({
                "index": i,
                "used": count,
                "remaining": remaining,
                "is_current": i == self._current_index,
                "key_preview": f"{key[:8]}...{key[-4:]}" if len(key) > 12 else "***"
            })
            total_used += count
            total_remaining += remaining

        return {
            "keys": usage_stats,
            "total_keys": len(self._keys),
            "current_key_index": self._current_index,
            "total_used_today": total_used,
            "total_remaining_today": total_remaining,
            "daily_limit_per_key": self._daily_limit
        }

    async def get_available_key(self, session: AsyncSession) -> Tuple[Optional[str], int]:
        """Get an available key that hasn't exceeded daily limit.
        Returns (api_key, key_index) or (None, -1) if all exhausted.
        """
        if not self._keys:
            return None, -1

        # Start from current key and try each one
        for offset in range(len(self._keys)):
            index = (self._current_index + offset) % len(self._keys)
            usage = await self.get_key_usage_today(session, index)

            if usage < self._daily_limit:
                # Update current index if we switched
                if index != self._current_index:
                    print(f"[API Key Manager] Switching from key {self._current_index} to key {index}")
                    self._current_index = index
                return self._keys[index], index

        # All keys exhausted
        print("[API Key Manager] All API keys have reached daily limit")
        return None, -1

    async def record_usage(self, session: AsyncSession, news_id: int, input_chars: int, key_index: int):
        """Record API usage"""
        log = AIAnalysisLog(
            news_id=news_id,
            api_key_index=key_index,
            input_chars=input_chars
        )
        session.add(log)
        await session.commit()


# Singleton instance
_api_key_manager: Optional[APIKeyManager] = None


def get_api_key_manager() -> APIKeyManager:
    global _api_key_manager
    if _api_key_manager is None:
        _api_key_manager = APIKeyManager()
    return _api_key_manager
