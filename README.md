# Korean News Filter

한국 주요 언론사의 뉴스를 자동 수집하고, 키워드 필터링 + AI 기반 의미 필터링을 통해 YouTube 콘텐츠 기획에 활용할 수 있는 브랜드/비즈니스 스토리를 발굴하는 프로그램입니다.

## Features

- **뉴스 수집**: RSS 피드를 통한 자동 뉴스 수집 (10개 언론사)
- **키워드 필터링**: 포함/제외 키워드 기반 1차 필터링
- **AI 필터링**: Gemini API를 활용한 의미 기반 2차 필터링
- **프리셋 관리**: 자주 사용하는 필터 조합 저장/불러오기
- **북마크**: 관심 뉴스 저장

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy + SQLite
- Google Gemini API (google-genai)
- APScheduler

### Frontend
- React 18 + TypeScript
- Vite
- TailwindCSS
- TanStack Query
- Zustand

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Google API Key (Gemini)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Run server
uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

### Access

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
korean-news-filter/
├── backend/
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── collector/    # RSS collector
│   │   ├── filter/       # Keyword & AI filters
│   │   ├── database/     # SQLAlchemy models
│   │   └── scheduler/    # Background jobs
│   ├── data/             # SQLite database
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/   # React components
│   │   ├── hooks/        # React Query hooks
│   │   ├── stores/       # Zustand stores
│   │   ├── types/        # TypeScript types
│   │   └── api/          # API client
│   └── package.json
│
└── README.md
```

## AI Presets

Built-in AI analysis presets:

1. **Brand Failure Story** - 브랜드/기업 실패 원인 분석
2. **Brand Success Story** - 브랜드/제품 성공 비결 분석
3. **Brand Comeback Story** - 위기 극복 턴어라운드 스토리
4. **Franchise Story** - 프랜차이즈 브랜드 분석

## RSS Sources

| Name | Category |
|------|----------|
| 연합뉴스 | 종합 |
| 한겨레 | 종합 |
| 조선일보 경제 | 경제 |
| 한국경제 | 경제 |
| 매일경제 | 경제 |
| ZDNet Korea | IT |
| 전자신문 | IT |
| 블로터 | IT |
| 플래텀 | 스타트업 |
| 벤처스퀘어 | 스타트업 |

## API Endpoints

### News
- `GET /api/news` - 뉴스 목록 (필터 적용)
- `GET /api/news/{id}` - 뉴스 상세
- `PATCH /api/news/{id}` - 상태 업데이트

### Collector
- `POST /api/collector/run` - 수동 수집 실행
- `GET /api/collector/status` - 수집 상태
- `GET /api/collector/sources` - 소스 목록

### Filters
- `GET /api/filters/presets` - 프리셋 목록
- `POST /api/filters/presets` - 프리셋 생성
- `GET /api/filters/ai/presets` - AI 프리셋 목록

### AI
- `POST /api/ai/analyze` - 단일 분석
- `POST /api/ai/batch-analyze` - 배치 분석
- `GET /api/ai/usage` - API 사용량

## License

MIT
