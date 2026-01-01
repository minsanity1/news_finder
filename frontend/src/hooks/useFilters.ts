import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { filterApi } from '../api/client';
import type { FilterPreset } from '../types';

export function useFilterPresets() {
  return useQuery({
    queryKey: ['filterPresets'],
    queryFn: () => filterApi.getPresets(),
  });
}

export function useCreateFilterPreset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (preset: Omit<FilterPreset, 'id' | 'created_at' | 'updated_at'>) =>
      filterApi.createPreset(preset),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filterPresets'] });
    },
  });
}

export function useUpdateFilterPreset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, preset }: { id: number; preset: Partial<FilterPreset> }) =>
      filterApi.updatePreset(id, preset),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filterPresets'] });
    },
  });
}

export function useDeleteFilterPreset() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: number) => filterApi.deletePreset(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['filterPresets'] });
    },
  });
}

export function useDefaultKeywords() {
  return useQuery({
    queryKey: ['defaultKeywords'],
    queryFn: () => filterApi.getDefaultKeywords(),
    staleTime: Infinity,
  });
}

export function useAIPresets() {
  return useQuery({
    queryKey: ['aiPresets'],
    queryFn: () => filterApi.getAIPresets(),
    staleTime: Infinity,
  });
}

export function useAIPresetDetail(key: string) {
  return useQuery({
    queryKey: ['aiPreset', key],
    queryFn: () => filterApi.getAIPresetDetail(key),
    enabled: !!key,
    staleTime: Infinity,
  });
}
