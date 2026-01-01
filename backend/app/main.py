from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.database import init_db
from app.api import news, filters, ai, collector, search
from app.scheduler.jobs import start_scheduler, shutdown_scheduler


settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    start_scheduler()
    yield
    # Shutdown
    shutdown_scheduler()


app = FastAPI(
    title="Korean News Filter",
    description="한국 뉴스 수집 및 AI 필터링 API",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
app.include_router(news.router, prefix="/api/news", tags=["news"])
app.include_router(filters.router, prefix="/api/filters", tags=["filters"])
app.include_router(ai.router, prefix="/api/ai", tags=["ai"])
app.include_router(collector.router, prefix="/api/collector", tags=["collector"])
app.include_router(search.router, prefix="/api/search", tags=["search"])


@app.get("/")
async def root():
    return {"message": "Korean News Filter API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
