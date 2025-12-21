// Custom hooks for GPU data fetching
import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';
import { queryKeys } from '../lib/queryClient';

export function useListings(params?: { page?: number; size?: number }) {
  return useQuery({
    queryKey: queryKeys.listings.list(params),
    queryFn: () => api.listings.getAll(params),
  });
}

export function useListingsByModel(model: string) {
  return useQuery({
    queryKey: queryKeys.listings.byModel(model),
    queryFn: () => api.listings.getByModel(model),
    enabled: !!model,
  });
}

export function useListingsCount() {
  return useQuery({
    queryKey: queryKeys.listings.count,
    queryFn: () => api.listings.getCount(),
  });
}

export function useAvailableModels() {
  return useQuery({
    queryKey: queryKeys.listings.models,
    queryFn: () => api.listings.getModels(),
  });
}

export function useStats() {
  return useQuery({
    queryKey: queryKeys.stats.all,
    queryFn: () => api.stats.getAll(),
  });
}

export function useSummaryStats() {
  return useQuery({
    queryKey: queryKeys.stats.summary,
    queryFn: () => api.stats.getSummary(),
  });
}

export function useValueAnalysis() {
  return useQuery({
    queryKey: queryKeys.value.all,
    queryFn: () => api.value.getAll(),
  });
}

export function useTopValue(n: number = 10) {
  return useQuery({
    queryKey: queryKeys.value.top(n),
    queryFn: () => api.value.getTopN(n),
  });
}

export function useWebSocketConnections() {
  return useQuery({
    queryKey: queryKeys.websocket.connections,
    queryFn: () => api.websocket.getConnections(),
    refetchInterval: 30000, // Refresh every 30 seconds
  });
}

export function useHealth() {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: () => api.health(),
    refetchInterval: 60000, // Refresh every minute
  });
}
