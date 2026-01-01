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
  is_read: boolean;
  is_bookmarked: boolean;
  is_used: boolean;
  ai_analyzed: boolean;
  ai_score: number | null;
  ai_category: string | null;
  ai_reason: string | null;
  ai_key_points: string[] | null;
  ai_youtube_potential: string | null;
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
  is_relevant: boolean;
  score: number;
  category: string;
  reason: string;
  youtube_potential: string;
  key_points: string[];
}

export interface CollectorStatus {
  is_running: boolean;
  last_run: string | null;
  last_collected_count: number;
}

export interface RSSSource {
  name: string;
  url: string;
  category: string;
  enabled: boolean;
}

export interface NewsFilter {
  keyword?: string;
  include_keywords?: string[];
  exclude_keywords?: string[];
  source?: string;
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

export interface AIUsage {
  today: number;
  total: number;
  daily_limit: number;
  remaining: number;
}
