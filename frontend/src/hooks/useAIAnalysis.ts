import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { aiApi, collectorApi } from '../api/client';

export function useAIAnalyze() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ newsId, prompt, presetKey }: { newsId: number; prompt?: string; presetKey?: string }) =>
      aiApi.analyze(newsId, prompt, presetKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });
}

export function useBatchAIAnalyze() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ newsIds, prompt, presetKey }: { newsIds: number[]; prompt?: string; presetKey?: string }) =>
      aiApi.batchAnalyze(newsIds, prompt, presetKey),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['news'] });
    },
  });
}

export function useAIUsage() {
  return useQuery({
    queryKey: ['aiUsage'],
    queryFn: () => aiApi.getUsage(),
    refetchInterval: 1000 * 60, // 1분마다 갱신
  });
}

export function useAnalyzeUnanalyzed() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ presetKey, limit }: { presetKey?: string; limit?: number }) =>
      aiApi.analyzeUnanalyzed(presetKey, limit),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['news'] });
      queryClient.invalidateQueries({ queryKey: ['aiUsage'] });
    },
  });
}

export function useCollectorRun() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => collectorApi.run(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['news'] });
      queryClient.invalidateQueries({ queryKey: ['collectorStatus'] });
    },
  });
}

export function useCollectorStatus() {
  return useQuery({
    queryKey: ['collectorStatus'],
    queryFn: () => collectorApi.getStatus(),
    refetchInterval: 1000 * 30, // 30초마다 갱신
  });
}

export function useCollectorSources() {
  return useQuery({
    queryKey: ['collectorSources'],
    queryFn: () => collectorApi.getSources(),
    staleTime: Infinity,
  });
}
