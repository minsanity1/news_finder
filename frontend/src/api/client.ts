import axios from 'axios';
import type {
  News,
  NewsListResponse,
  FilterPreset,
  AIPreset,
  AIAnalysisResult,
  NewsFilter,
  AIUsage,
  CommunitySource,
  CommunityCollectResponse,
} from '../types';

const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// News API
export const newsApi = {
  getList: async (filter: NewsFilter): Promise<NewsListResponse> => {
    const params = new URLSearchParams();

    if (filter.keyword) params.append('keyword', filter.keyword);
    if (filter.include_keywords && filter.include_keywords.length > 0) {
      params.append('include_keywords', filter.include_keywords.join(','));
    }
    if (filter.exclude_keywords && filter.exclude_keywords.length > 0) {
      params.append('exclude_keywords', filter.exclude_keywords.join(','));
    }
    if (filter.source) params.append('source', filter.source);
    if (filter.source_type) params.append('source_type', filter.source_type);
    if (filter.category) params.append('category', filter.category);
    if (filter.ai_min_score !== undefined) params.append('ai_min_score', String(filter.ai_min_score));
    if (filter.ai_category) params.append('ai_category', filter.ai_category);
    if (filter.from_date) params.append('from_date', filter.from_date);
    if (filter.to_date) params.append('to_date', filter.to_date);
    if (filter.is_bookmarked !== undefined) params.append('is_bookmarked', String(filter.is_bookmarked));
    if (filter.is_read !== undefined) params.append('is_read', String(filter.is_read));
    params.append('page', String(filter.page));
    params.append('limit', String(filter.limit));

    const response = await api.get(`/news?${params.toString()}`);
    return response.data;
  },

  getById: async (id: number): Promise<News> => {
    const response = await api.get(`/news/${id}`);
    return response.data;
  },

  update: async (id: number, data: Partial<Pick<News, 'is_read' | 'is_bookmarked' | 'is_used'>>): Promise<News> => {
    const response = await api.patch(`/news/${id}`, data);
    return response.data;
  },

  delete: async (id: number): Promise<void> => {
    await api.delete(`/news/${id}`);
  },

  getSources: async (sourceType?: string): Promise<string[]> => {
    const params = sourceType ? `?source_type=${sourceType}` : '';
    const response = await api.get(`/news/sources${params}`);
    return response.data.sources;
  },

  getCategories: async (sourceType?: string): Promise<string[]> => {
    const params = sourceType ? `?source_type=${sourceType}` : '';
    const response = await api.get(`/news/categories${params}`);
    return response.data.categories;
  },
};

// Filter API
export const filterApi = {
  getPresets: async (): Promise<FilterPreset[]> => {
    const response = await api.get('/filters/presets');
    return response.data.presets;
  },

  createPreset: async (preset: Omit<FilterPreset, 'id' | 'created_at' | 'updated_at'>): Promise<FilterPreset> => {
    const response = await api.post('/filters/presets', preset);
    return response.data;
  },

  updatePreset: async (id: number, preset: Partial<FilterPreset>): Promise<FilterPreset> => {
    const response = await api.put(`/filters/presets/${id}`, preset);
    return response.data;
  },

  deletePreset: async (id: number): Promise<void> => {
    await api.delete(`/filters/presets/${id}`);
  },

  getDefaultKeywords: async (): Promise<{
    include_keywords: Record<string, string[]>;
    exclude_keywords: string[];
  }> => {
    const response = await api.get('/filters/keywords/defaults');
    return response.data;
  },

  getAIPresets: async (): Promise<Record<string, AIPreset>> => {
    const response = await api.get('/filters/ai/presets');
    return response.data.presets;
  },

  getAIPresetDetail: async (key: string): Promise<AIPreset> => {
    const response = await api.get(`/filters/ai/presets/${key}`);
    return response.data;
  },
};

// Search API
export const searchApi = {
  getStatus: async (): Promise<{ naver_api_configured: boolean; naver_api_url?: string }> => {
    const response = await api.get('/search/status');
    return response.data;
  },

  searchNaver: async (query: string, maxResults: number = 100, saveToDb: boolean = true, filterSources: string[] = []): Promise<{
    query: string;
    total_found: number;
    saved_count: number;
    filtered_count: number;
    items: Array<{
      title: string;
      summary: string;
      url: string;
      source: string;
      category: string;
      published_at: string | null;
    }>;
  }> => {
    const response = await api.post('/search/naver', {
      query,
      max_results: maxResults,
      save_to_db: saveToDb,
      filter_sources: filterSources.length > 0 ? filterSources : undefined,
    });
    return response.data;
  },

  searchKeywords: async (
    keywords: string[],
    maxPerKeyword: number = 50,
    filterSources: string[] = []
  ): Promise<{
    keywords: string[];
    total_found: number;
    filtered_count: number;
    saved_count: number;
  }> => {
    const response = await api.post('/search/naver/keywords', {
      keywords,
      max_per_keyword: maxPerKeyword,
      save_to_db: true,
      filter_sources: filterSources.length > 0 ? filterSources : undefined,
    });
    return response.data;
  },
};

// AI API
export const aiApi = {
  analyze: async (newsId: number, prompt?: string, presetKey?: string): Promise<AIAnalysisResult> => {
    const response = await api.post('/ai/analyze', {
      news_id: newsId,
      prompt,
      preset_key: presetKey,
    });
    return response.data;
  },

  batchAnalyze: async (newsIds: number[], prompt?: string, presetKey?: string): Promise<{
    message: string;
    results: AIAnalysisResult[];
  }> => {
    const response = await api.post('/ai/batch-analyze', {
      news_ids: newsIds,
      prompt,
      preset_key: presetKey,
    });
    return response.data;
  },

  getUsage: async (): Promise<AIUsage> => {
    const response = await api.get('/ai/usage');
    return response.data;
  },

  analyzeUnanalyzed: async (presetKey: string = 'brand_failure', limit: number = 10): Promise<{
    message: string;
    count: number;
    results?: AIAnalysisResult[];
  }> => {
    const response = await api.post(`/ai/analyze-unanalyzed?preset_key=${presetKey}&limit=${limit}`);
    return response.data;
  },
};

// Community API
export const communityApi = {
  getSources: async (): Promise<Record<string, CommunitySource>> => {
    const response = await api.get('/community/sources');
    return response.data.sources;
  },

  getStatus: async (): Promise<{
    enabled_sources: string[];
    available_collectors: string[];
    total_boards: number;
  }> => {
    const response = await api.get('/community/status');
    return response.data;
  },

  collect: async (
    source: string,
    board: string,
    limit: number = 20
  ): Promise<CommunityCollectResponse> => {
    const response = await api.post('/community/collect', {
      source,
      board,
      limit,
      save_to_db: true,
      fetch_detail: true,
    });
    return response.data;
  },

  collectAll: async (): Promise<{
    results: Record<string, {
      name: string;
      boards: Record<string, CommunityCollectResponse | { error: string }>;
    }>;
    total_collected: number;
    total_saved: number;
  }> => {
    const response = await api.post('/community/collect/all');
    return response.data;
  },

  test: async (
    source: string = 'ppomppu',
    board: string = '핫게시글',
    limit: number = 5
  ): Promise<{
    success: boolean;
    source: string;
    board: string;
    found?: number;
    posts?: Array<{
      title: string;
      url: string;
      view_count: number;
      comment_count: number;
      like_count: number;
    }>;
    error?: string;
  }> => {
    const response = await api.post(`/community/test?source=${source}&board=${encodeURIComponent(board)}&limit=${limit}`);
    return response.data;
  },
};

// Ranking API (네이버 뉴스 랭킹 수집)
export interface PressInfo {
  id: string;
  name: string;
  category: string;
  priority: number;
  enabled: boolean;
}

export interface RankingCollectResponse {
  collected: number;
  saved: number;
  duplicates: number;
  by_press: Record<string, number>;
}

export const rankingApi = {
  getPressList: async (): Promise<PressInfo[]> => {
    const response = await api.get('/ranking/press-list');
    return response.data;
  },

  getRankingTypes: async (): Promise<Record<string, string>> => {
    const response = await api.get('/ranking/ranking-types');
    return response.data;
  },

  getStatus: async (): Promise<{
    total_press: number;
    enabled_press: number;
    by_category: Record<string, number>;
    ranking_types: string[];
  }> => {
    const response = await api.get('/ranking/status');
    return response.data;
  },

  collect: async (params: {
    press_ids?: string[];
    ranking_type: string;
    target_date?: string;
    limit_per_press?: number;
    save_to_db?: boolean;
  }): Promise<RankingCollectResponse> => {
    const response = await api.post('/ranking/collect', {
      press_ids: params.press_ids,
      ranking_type: params.ranking_type,
      target_date: params.target_date,
      limit_per_press: params.limit_per_press ?? 10,
      save_to_db: params.save_to_db ?? true,
    });
    return response.data;
  },

  preview: async (
    pressId: string,
    rankingType: string = 'popular',
    limit: number = 10
  ): Promise<Array<{
    rank: number;
    title: string;
    url: string;
    source: string;
    category: string;
    ranking_type: string;
    view_count: number | null;
    comment_count: number | null;
  }>> => {
    const response = await api.get(`/ranking/preview/${pressId}?ranking_type=${rankingType}&limit=${limit}`);
    return response.data;
  },
};

export default api;
