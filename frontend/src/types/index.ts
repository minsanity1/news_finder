export interface AIBreakdown {
  brand_recognition?: number;
  narrative_gap?: number;
  emotional_conflict?: number;
  national_pride?: number;
  practicality?: number;
  villain_bonus?: number;
  irony_bonus?: number;
  trend_bonus?: number;
  wallet_impact?: number;
  penalty_trivia?: number;
  penalty_timing?: number;
  penalty_b2b?: number;
}

export type SourceType = 'news' | 'community';

export interface News {
  id: number;
  title: string;
  summary: string | null;
  content: string | null;
  url: string;
  source: string | null;
  category: string | null;
  published_at: string | null;
  collected_at: string | null;
  // 소스 타입
  source_type: SourceType | null;
  // 커뮤니티 전용 메타
  view_count: number | null;
  comment_count: number | null;
  like_count: number | null;
  author: string | null;
  // 상태
  is_read: boolean;
  is_bookmarked: boolean;
  is_used: boolean;
  ai_analyzed: boolean;
  ai_score: number | null;
  ai_grade: string | null;  // S, A, B, C
  ai_category: string | null;
  ai_reason: string | null;
  ai_key_points: string[] | null;
  ai_breakdown: AIBreakdown | null;
  ai_youtube_potential: string | null;
  ai_male_2040_check: string | null;  // ⭕, 🔺, ❌
  ai_male_2040_reason: string | null;
  ai_suggested_title: string | null;
  ai_analyzed_at: string | null;
}

export interface NewsListResponse {
  items: News[];
  total: number;
  page: number;
  limit: number;
  total_pages: number;
}

export interface FilterPreset {
  id: number;
  name: string;
  type: 'keyword' | 'ai' | 'combined';
  include_keywords: string[] | null;
  exclude_keywords: string[] | null;
  sources: string[] | null;
  categories: string[] | null;
  ai_prompt: string | null;
  ai_min_score: number | null;
  is_default: boolean;
  created_at: string | null;
  updated_at: string | null;
}

export interface AIPreset {
  key: string;
  name: string;
  prompt?: string;
}

export interface AIAnalysisResult {
  news_id: number;
  score: number;
  grade: string;
  breakdown: AIBreakdown | null;
  reason: string;
  male_2040_check: string;
  male_2040_reason: string | null;
  key_points: string[];
  suggested_title: string | null;
  // 하위 호환성
  is_relevant?: boolean;
  category?: string;
  youtube_potential?: string;
}

export interface NewsFilter {
  keyword?: string;
  include_keywords?: string[];
  exclude_keywords?: string[];
  source?: string;
  source_type?: SourceType;  // news / community
  category?: string;
  ai_min_score?: number;
  ai_category?: string;
  from_date?: string;
  to_date?: string;
  is_bookmarked?: boolean;
  is_read?: boolean;
  page: number;
  limit: number;
}

export interface APIKeyUsage {
  index: number;
  used: number;
  remaining: number;
  is_current: boolean;
  key_preview: string;
}

export interface AIUsage {
  today: number;
  total: number;
  daily_limit: number;
  remaining: number;
  api_key_configured: boolean;
  keys?: APIKeyUsage[];
  total_keys?: number;
  current_key_index?: number;
}

// 커뮤니티 관련 타입
export interface CommunityBoard {
  id: string;
  priority: number;
  collect_limit: number;
}

export interface CommunitySource {
  name: string;
  enabled: boolean;
  boards: CommunityBoard[];
}

export interface CommunityCollectResponse {
  source: string;
  board: string;
  collected: number;
  saved: number;
  duplicates: number;
}
