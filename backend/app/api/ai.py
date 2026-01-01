from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import get_db
from app.database.repository import NewsRepository, AIAnalysisLogRepository
from app.filter.ai_filter import AIFilter, AI_PRESETS
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class AnalyzeRequest(BaseModel):
    news_id: int
    prompt: Optional[str] = None
    preset_key: Optional[str] = None


class BatchAnalyzeRequest(BaseModel):
    news_ids: List[int]
    prompt: Optional[str] = None
    preset_key: Optional[str] = None


class AnalysisResult(BaseModel):
    news_id: int
    is_relevant: bool
    score: int
    category: str
    reason: str
    youtube_potential: str
    key_points: List[str]


@router.post("/analyze", response_model=AnalysisResult)
async def analyze_single(
    request: AnalyzeRequest,
    db: AsyncSession = Depends(get_db)
):
    """단일 뉴스 AI 분석"""
    news_repo = NewsRepository(db)
    log_repo = AIAnalysisLogRepository(db)

    # 뉴스 조회
    news = await news_repo.get_by_id(request.news_id)
    if not news:
        raise HTTPException(status_code=404, detail="News not found")

    # 프롬프트 결정
    prompt = request.prompt
    if not prompt and request.preset_key:
        preset = AI_PRESETS.get(request.preset_key)
        if preset:
            prompt = preset["prompt"]

    if not prompt:
        raise HTTPException(
            status_code=400,
            detail="Either prompt or preset_key is required"
        )

    # AI 분석 실행
    ai_filter = AIFilter()
    result = await ai_filter.analyze(
        news.title,
        news.summary or "",
        prompt
    )

    # 뉴스에 분석 결과 저장
    await news_repo.update(request.news_id, {
        "ai_analyzed": True,
        "ai_score": result.get("score", 0),
        "ai_category": result.get("category", "other"),
        "ai_reason": result.get("reason", ""),
        "ai_key_points": result.get("key_points", []),
        "ai_youtube_potential": result.get("youtube_potential", "낮음"),
        "ai_analyzed_at": datetime.utcnow()
    })

    # 분석 로그 저장
    await log_repo.create({
        "news_id": request.news_id,
        "input_chars": len(news.title) + len(news.summary or "")
    })

    return AnalysisResult(
        news_id=request.news_id,
        is_relevant=result.get("is_relevant", False),
        score=result.get("score", 0),
        category=result.get("category", "other"),
        reason=result.get("reason", ""),
        youtube_potential=result.get("youtube_potential", "낮음"),
        key_points=result.get("key_points", [])
    )


@router.post("/batch-analyze")
async def analyze_batch(
    request: BatchAnalyzeRequest,
    db: AsyncSession = Depends(get_db)
):
    """배치 AI 분석"""
    news_repo = NewsRepository(db)
    log_repo = AIAnalysisLogRepository(db)

    # 프롬프트 결정
    prompt = request.prompt
    if not prompt and request.preset_key:
        preset = AI_PRESETS.get(request.preset_key)
        if preset:
            prompt = preset["prompt"]

    if not prompt:
        raise HTTPException(
            status_code=400,
            detail="Either prompt or preset_key is required"
        )

    # 뉴스 목록 조회
    news_list = []
    for news_id in request.news_ids:
        news = await news_repo.get_by_id(news_id)
        if news:
            news_list.append({
                "id": news.id,
                "title": news.title,
                "summary": news.summary or ""
            })

    if not news_list:
        raise HTTPException(status_code=404, detail="No valid news found")

    # AI 분석 실행
    ai_filter = AIFilter()
    results = await ai_filter.batch_analyze(news_list, prompt)

    # 결과 저장
    for result in results:
        news_id = result.get("news_id")
        if news_id:
            await news_repo.update(news_id, {
                "ai_analyzed": True,
                "ai_score": result.get("score", 0),
                "ai_category": result.get("category", "other"),
                "ai_reason": result.get("reason", ""),
                "ai_key_points": result.get("key_points", []),
                "ai_youtube_potential": result.get("youtube_potential", "낮음"),
                "ai_analyzed_at": datetime.utcnow()
            })

            # 분석 로그 저장
            news_item = next((n for n in news_list if n["id"] == news_id), None)
            if news_item:
                await log_repo.create({
                    "news_id": news_id,
                    "input_chars": len(news_item["title"]) + len(news_item["summary"])
                })

    return {
        "message": f"Analyzed {len(results)} news items",
        "results": [
            AnalysisResult(
                news_id=r.get("news_id", 0),
                is_relevant=r.get("is_relevant", False),
                score=r.get("score", 0),
                category=r.get("category", "other"),
                reason=r.get("reason", ""),
                youtube_potential=r.get("youtube_potential", "낮음"),
                key_points=r.get("key_points", [])
            )
            for r in results
        ]
    }


@router.get("/usage")
async def get_usage(db: AsyncSession = Depends(get_db)):
    """API 사용량 통계"""
    log_repo = AIAnalysisLogRepository(db)
    stats = await log_repo.get_usage_stats()

    return {
        "today": stats["today"],
        "total": stats["total"],
        "daily_limit": 1500,  # Gemini Flash 무료 티어
        "remaining": max(0, 1500 - stats["today"])
    }


@router.post("/analyze-unanalyzed")
async def analyze_unanalyzed(
    preset_key: str = "brand_failure",
    limit: int = 10,
    db: AsyncSession = Depends(get_db)
):
    """미분석 뉴스 자동 분석"""
    news_repo = NewsRepository(db)

    # 미분석 뉴스 조회
    unanalyzed = await news_repo.get_unanalyzed(limit=limit)

    if not unanalyzed:
        return {"message": "No unanalyzed news found", "count": 0}

    # BatchAnalyzeRequest 생성
    request = BatchAnalyzeRequest(
        news_ids=[news.id for news in unanalyzed],
        preset_key=preset_key
    )

    # 배치 분석 실행
    return await analyze_batch(request, db)
