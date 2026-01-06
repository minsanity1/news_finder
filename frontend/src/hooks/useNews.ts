import { useEffect, useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { newsApi, rankingApi } from '../api/client';
import type { NewsFilter, News } from '../types';

export function useNewsList(filter: NewsFilter) {
  return useQuery({
    queryKey: ['news', filter],
    queryFn: () => newsApi.getList(filter),
  });
}

export function useNewsDetail(id: number) {
  return useQuery({
    queryKey: ['news', id],
    queryFn: () => newsApi.getById(id),
    enabled: id > 0,
  });
}

export function useUpdateNews() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Pick<News, 'is_read' | 'is_bookmarked' | 'is_used'>> }) =>
      newsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });
}

export function useDeleteNews() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => newsApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });
}

export function useNewsSources(sourceType?: string) {
  return useQuery({
    queryKey: ['news', 'sources', sourceType],
    queryFn: () => newsApi.getSources(sourceType),
    staleTime: 1000 * 60 * 30, // 30분
  });
}

export function useNewsCategories(sourceType?: string) {
  return useQuery({
    queryKey: ['news', 'categories', sourceType],
    queryFn: () => newsApi.getCategories(sourceType),
    staleTime: 1000 * 60 * 30, // 30분
  });
}

// 앱 시작 시 자동 수집
export function useAutoCollect() {
  const queryClient = useQueryClient();
  const [isCollecting, setIsCollecting] = useState(false);
  const [lastCollected, setLastCollected] = useState<Date | null>(null);

  // 마지막 수집 시간 체크 (로컬스토리지)
  useEffect(() => {
    const stored = localStorage.getItem('lastNewsCollect');
    if (stored) {
      setLastCollected(new Date(stored));
    }
  }, []);

  // 자동 수집 실행
  useEffect(() => {
    const shouldCollect = () => {
      if (!lastCollected) return true; // 처음 실행

      const now = new Date();
      const diff = now.getTime() - lastCollected.getTime();
      const hoursDiff = diff / (1000 * 60 * 60);

      return hoursDiff >= 1; // 1시간마다 자동 수집
    };

    const autoCollect = async () => {
      if (!shouldCollect() || isCollecting) return;

      setIsCollecting(true);
      console.log('[AutoCollect] Starting automatic news collection...');

      try {
        // 랭킹 뉴스 수집 (조회수 + 댓글수 둘 다, 전체 언론사, 10개씩)
        const result = await rankingApi.collect({
          ranking_type: 'all',  // popular + comment 둘 다
          limit_per_press: 10,
          save_to_db: true,
        });

        console.log(`[AutoCollect] Collected: ${result.collected}, Saved: ${result.saved}`);

        // 수집 시간 저장
        const now = new Date();
        localStorage.setItem('lastNewsCollect', now.toISOString());
        setLastCollected(now);

        // 뉴스 목록 새로고침
        queryClient.invalidateQueries({ queryKey: ['news'] });
      } catch (error) {
        console.error('[AutoCollect] Failed:', error);
      } finally {
        setIsCollecting(false);
      }
    };

    autoCollect();
  }, [lastCollected, isCollecting, queryClient]);

  return { isCollecting, lastCollected };
}
