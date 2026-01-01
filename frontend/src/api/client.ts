import axios from 'axios';
import type {
  News,
  NewsListResponse,
  FilterPreset,
  AIPreset,
  AIAnalysisResult,
  CollectorStatus,
  RSSSource,
  NewsFilter,
  AIUsage,
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

  getSources: async (): Promise<string[]> => {
    const response = await api.get('/news/sources');
    return response.data.sources;
  },

  getCategories: async (): Promise<string[]> => {
    const response = await api.get('/news/categories');
    return response.data.categories;
  },
};

// Collector API
export const collectorApi = {
  run: async (): Promise<{ message: string; collected_count: number; saved_count: number }> => {
    const response = await api.post('/collector/run');
    return response.data;
  },

  getStatus: async (): Promise<CollectorStatus> => {
    const response = await api.get('/collector/status');
    return response.data;
  },

  getSources: async (): Promise<RSSSource[]> => {
    const response = await api.get('/collector/sources');
    return response.data.sources;
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

  searchKeywords: async (keywords: string[], maxPerKeyword: number = 50): Promise<{
    keywords: string[];
    total_found: number;
    saved_count: number;
  }> => {
    const response = await api.post('/search/naver/keywords', keywords, {
      params: { max_per_keyword: maxPerKeyword, save_to_db: true }
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

export default api;
