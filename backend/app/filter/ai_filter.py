import json
from typing import Optional, Tuple
from datetime import datetime

from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.filter.api_key_manager import get_api_key_manager

settings = get_settings()


# 유튜브 바이럴 스코어카드 v2.0
VIRAL_SCORECARD_PROMPT = """# 유튜브 소재/주제 바이럴 예측 스코어카드 v2.0

다음 뉴스가 유튜브 콘텐츠로서 바이럴 잠재력이 있는지 평가해주세요.

## 점수 체계 (총 100점)

### A. 기본 항목 (65점)

1. **브랜드 인지도** (Max 15점)
   - 15점: 국민 브랜드 - 전 국민이 알며, 매장/제품 경험이 보편적 (전국 체인, 세대불문)
   - 10점: 세대별 레전드/전국구 유행 - 특정 세대·시기에 전국적으로 유명했으나 지금은 체감이 줄어든 경우
   - 5점: B2B/로컬/소기업 - 일반 대중에게 생소하거나 특정 지역/전문가 중심

2. **서사의 낙차** (Max 15점)
   - 15점: 극적 반전 - 전성기→갑작스러운 몰락 또는 망하기 직전→기적적 부활
   - 8점: 점진적 하락/평범한 위기 - 경쟁 심화나 시장 변화로 점유율이 꾸준히 하락
   - 0점: 굴곡 없는 성공 - 위기나 몰락 없이 순탄하게 성장만 한 스토리

3. **감정적 대립 구도** (Max 15점)
   - 15점: 선악 구도 - 정직한 쪽 vs 꼼수·탐욕의 빌런 구도가 명확
   - 8점: 구조적 대립 - 특정 악당보다는 구조적 모순/딜레마
   - 0점: 갈등 부재 - 대립각 없이 정보 소개 위주

4. **국뽕 및 해외 반응** (Max 10점)
   - 10점: 역수출/기술 역전 - 한국에서 저평가되던 것이 해외에서 대박, 생활/지갑과도 연결
   - 5점: 단순 칭찬/관광객 유입 - "외국인이 좋아한다" 수준
   - 0점: 국내 한정 이슈 또는 국뽕과 무관

5. **실용성 및 비밀** (Max 10점)
   - 10점: 돈/생활 꿀팁 - 시청자의 지갑/식생활에 직접적 도움이나 충격을 주는 정보
   - 5점: 잡학/트리비아 - 몰라도 사는 데 지장 없지만 '아는 척'하고 싶은 지식
   - 0점: 뻔한 정보 - 이미 널리 알려진 상식 수준

### B. 바이럴 부스터 (35점)

1. **공공의 적** (+10점): 댓글창을 욕설·분노·토론으로 폭발시키는 빌런이 명확히 존재 (탐욕 사모펀드, 슈링크플레이션, 갑질 등)
2. **극적 아이러니** (+10점): 상식적으로 말이 안 되는 반전·대비 (망작→해외 대박, 버리던 것→황금알)
3. **시의성/논쟁** (+8점): 지금 당장 뉴스/커뮤니티에서 뜨거운 이슈이거나 찬반 논쟁이 붙은 주제
4. **생활 가격/지갑 임팩트** (+7점): "당장 내 지갑/밥상/동네 상권과 직결된다"고 느끼는 소재

### C. 감점 요인

1. **단순 잡학/역사** (-15점): 현재 삶·가격·소비와 연결고리 없이 과거 역사나 단순 유래에만 집중
2. **타이밍 상실** (-8점): 이미 한물간 이슈를 뒤늦게 다루는 경우
3. **B2B/공급망 중심** (-7점): 일반 소비자가 체감하기 힘든 이야기만 있고 최종 소비자 경험과 연결 약함

---

## 등급 기준
- 80점 이상: S급 (초대박) - 무조건 제작해야 함
- 65~79점: A급 (대박) - 매우 훌륭한 소재
- 45~64점: B급 (평타) - 보완이 필요함
- 44점 이하: C급 (반려) - 다른 소재를 찾는 것이 좋음

---

## 2040 남성 체크 기준
- ⭕: 퇴근 후 치맥하면서 "야 이거 알아?" 하고 꺼낼 얘기 / 디시·에펨코리아에 글 올리면 댓글 달릴 소재
- 🔺: 관심은 있는데 먼저 꺼내진 않음
- ❌: "그래서?" 반응, 관심 밖"""


# 기존 프리셋 (하위 호환성 유지)
AI_PRESETS = {
    "viral_scorecard": {
        "name": "바이럴 스코어카드 v2.0",
        "prompt": VIRAL_SCORECARD_PROMPT
    },
    "brand_failure": {
        "name": "브랜드 실패 스토리 (레거시)",
        "prompt": VIRAL_SCORECARD_PROMPT  # 이제 모두 스코어카드 사용
    },
    "brand_success": {
        "name": "브랜드 성공/떡상 스토리 (레거시)",
        "prompt": VIRAL_SCORECARD_PROMPT
    },
    "brand_comeback": {
        "name": "브랜드 부활 스토리 (레거시)",
        "prompt": VIRAL_SCORECARD_PROMPT
    },
    "franchise_story": {
        "name": "프랜차이즈 스토리 (레거시)",
        "prompt": VIRAL_SCORECARD_PROMPT
    }
}


class AIFilter:
    def __init__(self):
        self._clients = {}  # Cache clients per key
        self.model = settings.ai_model
        self.key_manager = get_api_key_manager()

    def _get_client(self, api_key: str):
        """Get or create a client for the given API key"""
        if api_key not in self._clients:
            self._clients[api_key] = genai.Client(api_key=api_key)
        return self._clients[api_key]

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
                "score": 0,
                "grade": "C",
                "breakdown": {},
                "reason": "파싱 실패",
                "male_2040_check": "❌",
                "key_points": []
            }

    async def analyze(
        self,
        news_title: str,
        news_summary: str,
        prompt: str,
        session: Optional[AsyncSession] = None
    ) -> Tuple[dict, int]:
        """단일 뉴스 AI 분석
        Returns: (result_dict, key_index_used)
        """
        full_prompt = f"""{prompt}

---

## 분석 대상 뉴스

**제목:** {news_title}
**요약:** {news_summary}

---

## 응답 형식

반드시 아래 JSON 형식으로만 응답하세요:
{{
    "score": 0부터 100 사이 정수 (총점),
    "grade": "S" 또는 "A" 또는 "B" 또는 "C",
    "breakdown": {{
        "brand_recognition": 0-15,
        "narrative_gap": 0-15,
        "emotional_conflict": 0-15,
        "national_pride": 0-10,
        "practicality": 0-10,
        "villain_bonus": 0-10,
        "irony_bonus": 0-10,
        "trend_bonus": 0-8,
        "wallet_impact": 0-7,
        "penalty_trivia": 0 또는 -15,
        "penalty_timing": 0 또는 -8,
        "penalty_b2b": 0 또는 -7
    }},
    "reason": "판단 이유를 2-3문장으로",
    "male_2040_check": "⭕" 또는 "🔺" 또는 "❌",
    "male_2040_reason": "2040 남성 체크 이유를 한 문장으로",
    "key_points": ["핵심포인트1", "핵심포인트2", "핵심포인트3"],
    "suggested_title": "유튜브 썸네일/제목 제안 (선택)"
}}"""

        # Get available API key
        if session:
            api_key, key_index = await self.key_manager.get_available_key(session)
        else:
            api_key = self.key_manager.get_current_key()
            key_index = self.key_manager.current_key_index

        if not api_key:
            return {
                "score": 0,
                "grade": "C",
                "breakdown": {},
                "reason": "모든 API 키의 일일 한도가 초과되었습니다",
                "male_2040_check": "❌",
                "key_points": []
            }, -1

        try:
            client = self._get_client(api_key)
            response = client.models.generate_content(
                model=self.model,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    max_output_tokens=settings.ai_max_tokens,
                    temperature=0.3,
                )
            )

            result = self._parse_response(response.text)

            # 하위 호환성: 기존 필드 매핑
            result["is_relevant"] = result.get("score", 0) >= 45
            result["category"] = self._grade_to_category(result.get("grade", "C"))
            result["youtube_potential"] = self._grade_to_potential(result.get("grade", "C"))

            return result, key_index

        except Exception as e:
            error_msg = str(e)
            print(f"[AI Filter] API error with key {key_index}: {e}")

            # Check if it's a rate limit error, try next key
            if "429" in error_msg or "quota" in error_msg.lower() or "rate" in error_msg.lower():
                if session and key_index >= 0:
                    # Mark current key as exhausted by trying next one
                    next_key, next_index = await self.key_manager.get_available_key(session)
                    if next_key and next_index != key_index:
                        print(f"[AI Filter] Retrying with key {next_index}")
                        return await self.analyze(news_title, news_summary, prompt, session)

            return {
                "score": 0,
                "grade": "C",
                "breakdown": {},
                "reason": f"API 오류: {error_msg}",
                "male_2040_check": "❌",
                "key_points": []
            }, key_index

    def _grade_to_category(self, grade: str) -> str:
        """등급을 카테고리로 변환 (하위 호환성)"""
        mapping = {
            "S": "viral_hit",
            "A": "high_potential",
            "B": "moderate",
            "C": "low_potential"
        }
        return mapping.get(grade, "other")

    def _grade_to_potential(self, grade: str) -> str:
        """등급을 유튜브 잠재력으로 변환 (하위 호환성)"""
        mapping = {
            "S": "높음",
            "A": "높음",
            "B": "중간",
            "C": "낮음"
        }
        return mapping.get(grade, "낮음")

    async def batch_analyze(
        self,
        news_list: list,
        prompt: str,
        session: Optional[AsyncSession] = None
    ) -> list:
        """여러 뉴스 배치 분석"""
        results = []

        for news in news_list:
            result, key_index = await self.analyze(
                news.get("title", ""),
                news.get("summary", ""),
                prompt,
                session
            )
            result["news_id"] = news.get("id")
            result["key_index"] = key_index
            results.append(result)

        return results

    def get_preset_prompt(self, preset_key: str) -> Optional[str]:
        """프리셋 키로 프롬프트 조회"""
        preset = AI_PRESETS.get(preset_key)
        return preset["prompt"] if preset else None

    def get_default_prompt(self) -> str:
        """기본 스코어카드 프롬프트 반환"""
        return VIRAL_SCORECARD_PROMPT


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


def get_viral_scorecard_prompt() -> str:
    """바이럴 스코어카드 프롬프트 반환"""
    return VIRAL_SCORECARD_PROMPT
