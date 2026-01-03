"""
커뮤니티 수집 API
"""
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.database.repository import NewsRepository
from app.collector.community import (
    FMKoreaCollector,
    PpomppuCollector,
    COMMUNITY_BOARDS,
)
from app.collector.community.config import get_enabled_boards, get_board_config

router = APIRouter()


# 수집기 맵핑
COLLECTORS = {
    "fmkorea": FMKoreaCollector,
    "ppomppu": PpomppuCollector,
}


class CollectRequest(BaseModel):
    source: str                    # "fmkorea", "ppomppu"
    board: str                     # "핫이슈", "자유게시판"
    limit: int = 20
    save_to_db: bool = True
    fetch_detail: bool = True      # 상세 내용까지 가져올지


class CollectResponse(BaseModel):
    source: str
    board: str
    collected: int
    saved: int
    duplicates: int


class BoardInfo(BaseModel):
    id: str
    priority: int
    collect_limit: int


class SourceInfo(BaseModel):
    name: str
    enabled: bool
    boards: List[BoardInfo]


@router.post("/collect", response_model=CollectResponse)
async def collect_community_posts(
    request: CollectRequest,
    db: AsyncSession = Depends(get_db)
):
    """특정 커뮤니티 게시판 수집"""

    if request.source not in COLLECTORS:
        raise HTTPException(400, f"Unknown source: {request.source}. Available: {list(COLLECTORS.keys())}")

    # 게시판 설정 확인
    board_config = get_board_config(request.source, request.board)
    if not board_config:
        raise HTTPException(400, f"Unknown board: {request.board}")

    collector_class = COLLECTORS[request.source]
    collector = collector_class()

    try:
        # 게시글 수집
        posts = await collector.get_hot_posts(
            request.board,
            limit=request.limit,
            fetch_detail=request.fetch_detail
        )

        collected = len(posts)
        saved = 0
        duplicates = 0

        if request.save_to_db and posts:
            news_repo = NewsRepository(db)

            for post in posts:
                news_dict = collector.to_news_dict(post)
                news_dict["collected_at"] = datetime.utcnow()

                try:
                    # 중복 체크 (URL 기준)
                    existing = await news_repo.get_by_url(news_dict["url"])
                    if existing:
                        duplicates += 1
                        continue

                    await news_repo.create(news_dict)
                    saved += 1
                except Exception as e:
                    print(f"[Community] Error saving: {e}")
                    continue

        return CollectResponse(
            source=request.source,
            board=request.board,
            collected=collected,
            saved=saved,
            duplicates=duplicates,
        )

    finally:
        await collector.close()


@router.post("/collect/all")
async def collect_all_enabled(
    db: AsyncSession = Depends(get_db)
):
    """활성화된 모든 커뮤니티 수집"""
    enabled_boards = get_enabled_boards()
    results = {}

    for source_id, config in enabled_boards.items():
        if source_id not in COLLECTORS:
            continue

        results[source_id] = {
            "name": config["name"],
            "boards": {}
        }

        for board in config["boards"]:
            try:
                result = await collect_community_posts(
                    CollectRequest(
                        source=source_id,
                        board=board["id"],
                        limit=board["collect_limit"],
                        save_to_db=True,
                        fetch_detail=True,
                    ),
                    db
                )
                results[source_id]["boards"][board["id"]] = {
                    "collected": result.collected,
                    "saved": result.saved,
                    "duplicates": result.duplicates,
                }
            except Exception as e:
                results[source_id]["boards"][board["id"]] = {"error": str(e)}

    # 총계 계산
    total_collected = sum(
        board.get("collected", 0)
        for source in results.values()
        for board in source.get("boards", {}).values()
        if isinstance(board, dict) and "error" not in board
    )
    total_saved = sum(
        board.get("saved", 0)
        for source in results.values()
        for board in source.get("boards", {}).values()
        if isinstance(board, dict) and "error" not in board
    )

    return {
        "results": results,
        "total_collected": total_collected,
        "total_saved": total_saved,
    }


@router.get("/sources")
async def get_available_sources():
    """사용 가능한 커뮤니티 소스 목록"""
    sources = {}

    for source_id, config in COMMUNITY_BOARDS.items():
        # 수집기가 구현되어 있는지 확인
        has_collector = source_id in COLLECTORS

        sources[source_id] = SourceInfo(
            name=config["name"],
            enabled=config["enabled"] and has_collector,
            boards=[
                BoardInfo(
                    id=b["id"],
                    priority=b["priority"],
                    collect_limit=b["collect_limit"]
                )
                for b in config["boards"]
            ]
        )

    return {"sources": sources}


@router.get("/status")
async def get_community_status():
    """커뮤니티 수집 상태"""
    enabled = get_enabled_boards()

    return {
        "enabled_sources": list(enabled.keys()),
        "available_collectors": list(COLLECTORS.keys()),
        "total_boards": sum(len(c["boards"]) for c in enabled.values()),
    }


@router.post("/test")
async def test_crawling(source: str = "ppomppu", board: str = "핫게시글", limit: int = 5):
    """크롤링 테스트 (DB 저장 없이 결과만 반환)"""

    if source not in COLLECTORS:
        raise HTTPException(400, f"Unknown source: {source}")

    board_config = get_board_config(source, board)
    if not board_config:
        # 기본 board_id로 테스트
        available_boards = [b["id"] for b in COMMUNITY_BOARDS.get(source, {}).get("boards", [])]
        raise HTTPException(400, f"Unknown board: {board}. Available: {available_boards}")

    collector_class = COLLECTORS[source]
    collector = collector_class()

    try:
        # 목록만 가져오기 (상세 없이)
        posts = await collector.get_board_list(board, page=1)

        # limit 적용
        posts = posts[:limit]

        return {
            "success": True,
            "source": source,
            "board": board,
            "found": len(posts),
            "posts": posts,  # 제목, URL, 조회수 등
        }
    except Exception as e:
        return {
            "success": False,
            "source": source,
            "board": board,
            "error": str(e),
        }
    finally:
        await collector.close()
