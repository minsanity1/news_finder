from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.database import get_db
from app.database.repository import FilterPresetRepository
from app.filter.keyword import DEFAULT_INCLUDE_KEYWORDS, DEFAULT_EXCLUDE_KEYWORDS
from app.filter.ai_filter import get_ai_presets, get_ai_preset_detail
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


class FilterPresetCreate(BaseModel):
    name: str
    type: str  # 'keyword' | 'ai' | 'combined'
    include_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    ai_prompt: Optional[str] = None
    ai_min_score: Optional[int] = 70
    is_default: Optional[bool] = False


class FilterPresetUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    include_keywords: Optional[List[str]] = None
    exclude_keywords: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    ai_prompt: Optional[str] = None
    ai_min_score: Optional[int] = None
    is_default: Optional[bool] = None


class FilterPresetResponse(BaseModel):
    id: int
    name: str
    type: str
    include_keywords: Optional[List[str]]
    exclude_keywords: Optional[List[str]]
    sources: Optional[List[str]]
    categories: Optional[List[str]]
    ai_prompt: Optional[str]
    ai_min_score: Optional[int]
    is_default: bool
    created_at: Optional[str]
    updated_at: Optional[str]


@router.get("/presets")
async def get_presets(db: AsyncSession = Depends(get_db)):
    """필터 프리셋 목록 조회"""
    repo = FilterPresetRepository(db)
    presets = await repo.get_all()
    return {
        "presets": [FilterPresetResponse(**preset.to_dict()) for preset in presets]
    }


@router.post("/presets", response_model=FilterPresetResponse)
async def create_preset(
    preset_data: FilterPresetCreate,
    db: AsyncSession = Depends(get_db)
):
    """필터 프리셋 생성"""
    repo = FilterPresetRepository(db)
    preset = await repo.create(preset_data.model_dump())
    return FilterPresetResponse(**preset.to_dict())


@router.put("/presets/{preset_id}", response_model=FilterPresetResponse)
async def update_preset(
    preset_id: int,
    update_data: FilterPresetUpdate,
    db: AsyncSession = Depends(get_db)
):
    """필터 프리셋 수정"""
    repo = FilterPresetRepository(db)
    update_dict = update_data.model_dump(exclude_unset=True)
    preset = await repo.update(preset_id, update_dict)

    if not preset:
        raise HTTPException(status_code=404, detail="Preset not found")

    return FilterPresetResponse(**preset.to_dict())


@router.delete("/presets/{preset_id}")
async def delete_preset(
    preset_id: int,
    db: AsyncSession = Depends(get_db)
):
    """필터 프리셋 삭제"""
    repo = FilterPresetRepository(db)
    success = await repo.delete(preset_id)

    if not success:
        raise HTTPException(status_code=404, detail="Preset not found")

    return {"message": "Preset deleted successfully"}


@router.get("/keywords/defaults")
async def get_default_keywords():
    """기본 키워드 목록 조회"""
    return {
        "include_keywords": DEFAULT_INCLUDE_KEYWORDS,
        "exclude_keywords": DEFAULT_EXCLUDE_KEYWORDS
    }


@router.get("/ai/presets")
async def get_ai_presets_list():
    """AI 프리셋 목록 조회"""
    presets = get_ai_presets()
    return {"presets": presets}


@router.get("/ai/presets/{preset_key}")
async def get_ai_preset_by_key(preset_key: str):
    """AI 프리셋 상세 조회"""
    preset = get_ai_preset_detail(preset_key)

    if not preset:
        raise HTTPException(status_code=404, detail="AI Preset not found")

    return preset
