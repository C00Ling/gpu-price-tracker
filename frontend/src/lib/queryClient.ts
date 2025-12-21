// React Query configuration
import { QueryClient } from '@tanstack/react-query';
import { config } from './config';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: config.cache.staleTime,
      gcTime: config.cache.cacheTime,
      retry: 2,
      refetchOnWindowFocus: false,
      refetchOnMount: true,
    },
    mutations: {
      retry: 1,
    },
  },
});

// Query keys for better organization
export const queryKeys = {
  listings: {
    all: ['listings'] as const,
    list: (params?: any) => ['listings', 'list', params] as const,
    byModel: (model: string) => ['listings', 'model', model] as const,
    count: ['listings', 'count'] as const,
    models: ['listings', 'models'] as const,
  },
  stats: {
    all: ['stats'] as const,
    summary: ['stats', 'summary'] as const,
    byModel: (model: string) => ['stats', 'model', model] as const,
  },
  value: {
    all: ['value'] as const,
    top: (n: number) => ['value', 'top', n] as const,
  },
  websocket: {
    connections: ['websocket', 'connections'] as const,
  },
  health: ['health'] as const,
} as const;
