from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

Base = declarative_base()


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    from app.database.models import News, FilterPreset, AIAnalysisLog
    from sqlalchemy import select

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Seed default presets
    await seed_default_presets()


async def seed_default_presets():
    from app.database.models import FilterPreset
    from sqlalchemy import select

    default_presets = [
        {
            "name": "브랜드 몰락",
            "type": "combined",
            "include_keywords": ["파산", "폐업", "몰락", "위기", "실패", "철수", "매각", "적자"],
            "exclude_keywords": ["광고", "포토", "영상"],
            "ai_min_score": 0,
            "is_default": True,
        },
        {
            "name": "브랜드 성공",
            "type": "combined",
            "include_keywords": ["대박", "흥행", "돌풍", "급성장", "1위", "신기록", "떡상", "히트"],
            "exclude_keywords": ["광고", "포토", "영상"],
            "ai_min_score": 0,
            "is_default": True,
        },
        {
            "name": "부활 스토리",
            "type": "combined",
            "include_keywords": ["부활", "회생", "턴어라운드", "재기", "흑자전환", "반등", "회복"],
            "exclude_keywords": ["광고", "포토", "영상"],
            "ai_min_score": 0,
            "is_default": True,
        },
        {
            "name": "프랜차이즈",
            "type": "combined",
            "include_keywords": ["프랜차이즈", "가맹점", "치킨", "카페", "창업", "폐점", "매장"],
            "exclude_keywords": ["광고", "포토", "영상"],
            "ai_min_score": 0,
            "is_default": True,
        },
        {
            "name": "스타트업",
            "type": "combined",
            "include_keywords": ["스타트업", "투자", "유니콘", "시리즈", "인수", "엑싯", "폐업"],
            "exclude_keywords": ["광고", "포토", "채용"],
            "ai_min_score": 0,
            "is_default": True,
        },
    ]

    async with AsyncSessionLocal() as session:
        # Check if default presets already exist
        result = await session.execute(
            select(FilterPreset).where(FilterPreset.is_default == True)
        )
        existing = result.scalars().first()

        if not existing:
            for preset_data in default_presets:
                preset = FilterPreset(**preset_data)
                session.add(preset)
            await session.commit()
            print("[DB] Default presets created")
