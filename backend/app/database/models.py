from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(Text, nullable=False)
    summary = Column(Text)
    content = Column(Text)
    url = Column(Text, unique=True, nullable=False)
    source = Column(String(100))
    category = Column(String(50))
    published_at = Column(DateTime)
    collected_at = Column(DateTime, default=datetime.utcnow)

    # 상태
    is_read = Column(Boolean, default=False)
    is_bookmarked = Column(Boolean, default=False)
    is_used = Column(Boolean, default=False)

    # AI 분석 결과
    ai_analyzed = Column(Boolean, default=False)
    ai_score = Column(Integer)
    ai_category = Column(String(50))
    ai_reason = Column(Text)
    ai_key_points = Column(JSON)
    ai_youtube_potential = Column(String(20))
    ai_analyzed_at = Column(DateTime)

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "content": self.content,
            "url": self.url,
            "source": self.source,
            "category": self.category,
            "published_at": self.published_at.isoformat() if self.published_at else None,
            "collected_at": self.collected_at.isoformat() if self.collected_at else None,
            "is_read": self.is_read,
            "is_bookmarked": self.is_bookmarked,
            "is_used": self.is_used,
            "ai_analyzed": self.ai_analyzed,
            "ai_score": self.ai_score,
            "ai_category": self.ai_category,
            "ai_reason": self.ai_reason,
            "ai_key_points": self.ai_key_points,
            "ai_youtube_potential": self.ai_youtube_potential,
            "ai_analyzed_at": self.ai_analyzed_at.isoformat() if self.ai_analyzed_at else None,
        }


class FilterPreset(Base):
    __tablename__ = "filter_presets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    type = Column(String(20), nullable=False)  # 'keyword' | 'ai' | 'combined'

    # 키워드 필터 설정
    include_keywords = Column(JSON)
    exclude_keywords = Column(JSON)
    sources = Column(JSON)
    categories = Column(JSON)

    # AI 필터 설정
    ai_prompt = Column(Text)
    ai_min_score = Column(Integer, default=70)

    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "include_keywords": self.include_keywords,
            "exclude_keywords": self.exclude_keywords,
            "sources": self.sources,
            "categories": self.categories,
            "ai_prompt": self.ai_prompt,
            "ai_min_score": self.ai_min_score,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class AIAnalysisLog(Base):
    __tablename__ = "ai_analysis_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    news_id = Column(Integer, ForeignKey("news.id"))
    model = Column(String(50), default="gemini-2.0-flash")
    api_key_index = Column(Integer, default=0)  # Which key was used (0, 1, 2...)
    input_chars = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
