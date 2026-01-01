import json
from typing import Optional
from datetime import datetime

from google import genai
from google.genai import types

from app.config import get_settings

settings = get_settings()


# AI 프리셋
AI_PRESETS = {
    "brand_failure": {
        "name": "브랜드 실패 스토리",
        "prompt": """다음 뉴스가 "브랜드나 기업이 실패/몰락한 이유를 분석하거나 설명하는 콘텐츠"인지 판단해주세요.

판단 기준:
- 단순 실적 발표나 주가 하락 뉴스가 아닌, "왜" 실패했는지 원인 분석이 있어야 함
- 경영 전략 실수, 시장 변화 대응 실패, 내부 문제 등 구체적 원인이 언급되어야 함
- YouTube 비즈니스 분석 콘텐츠 (10분 이상)로 제작 가능한 깊이가 있어야 함

높은 점수 예시: "노키아가 스마트폰 시대에 몰락한 3가지 이유"
낮은 점수 예시: "A기업 3분기 적자 전환" (단순 실적 발표)"""
    },

    "brand_success": {
        "name": "브랜드 성공/떡상 스토리",
        "prompt": """다음 뉴스가 "브랜드나 제품이 크게 성공한 이유, 흥행 비결을 분석하는 콘텐츠"인지 판단해주세요.

판단 기준:
- 단순 매출/실적 발표가 아닌, "왜" 성공했는지 요인 분석이 있어야 함
- 마케팅 전략, 제품 혁신, 타이밍, 소비자 니즈 파악 등 구체적 성공 요인이 언급되어야 함
- YouTube 비즈니스 분석 콘텐츠로 제작 가능한 스토리가 있어야 함

높은 점수 예시: "성심당이 지역 빵집에서 전국구 브랜드가 된 비결"
낮은 점수 예시: "B기업 매출 신기록 달성" (단순 실적 발표)"""
    },

    "brand_comeback": {
        "name": "브랜드 부활 스토리",
        "prompt": """다음 뉴스가 "위기에 빠졌다가 다시 살아난 기업/브랜드의 턴어라운드 스토리"인지 판단해주세요.

판단 기준:
- 과거 위기/실패 → 현재 회복/성공의 스토리 구조가 있어야 함
- 어떻게 위기를 극복했는지 구체적 전략/변화가 언급되어야 함
- 드라마틱한 반전이 있어 시청자 흥미를 끌 수 있어야 함

높은 점수 예시: "파산 직전 레고, 어떻게 세계 1위 장난감 회사가 됐나"
낮은 점수 예시: "C기업 흑자전환" (단순 실적 개선)"""
    },

    "franchise_story": {
        "name": "프랜차이즈 스토리",
        "prompt": """다음 뉴스가 "프랜차이즈 브랜드(치킨, 커피, 편의점, 외식 등)의 성공/실패/부활 스토리"인지 판단해주세요.

판단 기준:
- 국내 프랜차이즈 브랜드 관련 깊이 있는 분석 기사
- 가맹점 확장/축소, 브랜드 전략 변화, 경쟁 구도 분석 등
- 예비 창업자나 일반 시청자가 관심 가질 만한 인사이트가 있어야 함"""
    }
}


class AIFilter:
    def __init__(self):
        self.client = None
        self.model = settings.ai_model

    def _get_client(self):
        if self.client is None:
            self.client = genai.Client(api_key=settings.google_api_key)
        return self.client

    def _parse_response(self, text: str) -> dict:
        """AI 응답에서 JSON 파싱"""
        try:
            # ```json ... ``` 형태 처리
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            return json.loads(text.strip())
        except Exception as e:
            print(f"[AI Filter] Parse error: {e}")
            return {
                "is_relevant": False,
                "score": 0,
                "category": "other",
                "reason": "파싱 실패",
                "youtube_potential": "낮음",
                "key_points": []
            }

    async def analyze(
        self,
        news_title: str,
        news_summary: str,
        prompt: str
    ) -> dict:
        """단일 뉴스 AI 분석"""
        full_prompt = f"""{prompt}

뉴스 제목: {news_title}
뉴스 요약: {news_summary}

반드시 아래 JSON 형식으로만 응답하세요:
{{
    "is_relevant": true 또는 false,
    "score": 0부터 100 사이 정수,
    "category": "failure" 또는 "success" 또는 "comeback" 또는 "other",
    "reason": "판단 이유를 한 문장으로",
    "youtube_potential": "높음" 또는 "중간" 또는 "낮음",
    "key_points": ["핵심포인트1", "핵심포인트2", "핵심포인트3"]
}}"""

        try:
            client = self._get_client()
            response = client.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=settings.ai_max_tokens,
                    temperature=0.3,
                )
            )

            return self._parse_response(response.text)

        except Exception as e:
            print(f"[AI Filter] API error: {e}")
            return {
                "is_relevant": False,
                "score": 0,
                "category": "other",
                "reason": f"API 오류: {str(e)}",
                "youtube_potential": "낮음",
                "key_points": []
            }

    async def batch_analyze(
        self,
        news_list: list,
        prompt: str
    ) -> list:
        """여러 뉴스 배치 분석"""
        results = []

        for news in news_list:
            result = await self.analyze(
                news.get("title", ""),
                news.get("summary", ""),
                prompt
            )
            result["news_id"] = news.get("id")
            results.append(result)

        return results

    def get_preset_prompt(self, preset_key: str) -> Optional[str]:
        """프리셋 키로 프롬프트 조회"""
        preset = AI_PRESETS.get(preset_key)
        return preset["prompt"] if preset else None


def get_ai_presets() -> dict:
    """AI 프리셋 목록 반환"""
    return {
        key: {"name": value["name"], "key": key}
        for key, value in AI_PRESETS.items()
    }


def get_ai_preset_detail(preset_key: str) -> Optional[dict]:
    """AI 프리셋 상세 정보 반환"""
    preset = AI_PRESETS.get(preset_key)
    if preset:
        return {
            "key": preset_key,
            "name": preset["name"],
            "prompt": preset["prompt"]
        }
    return None
