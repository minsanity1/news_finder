import { create } from 'zustand';
import type { NewsFilter } from '../types';

interface FilterState {
  filter: NewsFilter;
  setFilter: (filter: Partial<NewsFilter>) => void;
  resetFilter: () => void;
  setPage: (page: number) => void;
}

const defaultFilter: NewsFilter = {
  keyword: '',
  include_keywords: undefined,
  exclude_keywords: undefined,
  source: '',
  source_type: undefined,  // undefined = 전체, 'news' = 뉴스만, 'community' = 커뮤니티만
  category: '',
  ai_min_score: undefined,
  ai_category: '',
  from_date: '',
  to_date: '',
  is_bookmarked: undefined,
  is_read: undefined,
  page: 1,
  limit: 20,
};

export const useFilterStore = create<FilterState>((set) => ({
  filter: defaultFilter,

  setFilter: (newFilter) =>
    set((state) => ({
      filter: { ...state.filter, ...newFilter, page: 1 },
    })),

  resetFilter: () =>
    set(() => ({
      filter: defaultFilter,
    })),

  setPage: (page) =>
    set((state) => ({
      filter: { ...state.filter, page },
    })),
}));

// AI 필터 모달 상태
interface AIFilterModalState {
  isOpen: boolean;
  selectedPresetKey: string;
  customPrompt: string;
  minScore: number;
  openModal: () => void;
  closeModal: () => void;
  setPresetKey: (key: string) => void;
  setCustomPrompt: (prompt: string) => void;
  setMinScore: (score: number) => void;
}

export const useAIFilterModalStore = create<AIFilterModalState>((set) => ({
  isOpen: false,
  selectedPresetKey: 'brand_failure',
  customPrompt: '',
  minScore: 70,

  openModal: () => set({ isOpen: true }),
  closeModal: () => set({ isOpen: false }),
  setPresetKey: (key) => set({ selectedPresetKey: key }),
  setCustomPrompt: (prompt) => set({ customPrompt: prompt }),
  setMinScore: (score) => set({ minScore: score }),
}));

// 선택된 뉴스 상태
interface SelectedNewsState {
  selectedIds: number[];
  toggleSelect: (id: number) => void;
  selectAll: (ids: number[]) => void;
  clearSelection: () => void;
}

export const useSelectedNewsStore = create<SelectedNewsState>((set) => ({
  selectedIds: [],

  toggleSelect: (id) =>
    set((state) => ({
      selectedIds: state.selectedIds.includes(id)
        ? state.selectedIds.filter((i) => i !== id)
        : [...state.selectedIds, id],
    })),

  selectAll: (ids) =>
    set(() => ({
      selectedIds: ids,
    })),

  clearSelection: () =>
    set(() => ({
      selectedIds: [],
    })),
}));
