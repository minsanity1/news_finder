import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { newsApi } from '../api/client';
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

export function useNewsSources() {
  return useQuery({
    queryKey: ['news', 'sources'],
    queryFn: () => newsApi.getSources(),
    staleTime: 1000 * 60 * 30, // 30분
  });
}

export function useNewsCategories() {
  return useQuery({
    queryKey: ['news', 'categories'],
    queryFn: () => newsApi.getCategories(),
    staleTime: 1000 * 60 * 30, // 30분
  });
}
