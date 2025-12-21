// API service layer for backend communication
import { config } from '../lib/config';
import type {
  GPU,
  ModelStats,
  SummaryStats,
  ValueAnalysis,
  PaginationParams,
} from '../types';

const { baseUrl, timeout } = config.api;

class ApiError extends Error {
  status?: number;
  data?: any;

  constructor(message: string, status?: number, data?: any) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

async function fetchWithTimeout(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      throw new ApiError(
        `HTTP error! status: ${response.status}`,
        response.status,
        await response.json().catch(() => null)
      );
    }

    return response;
  } finally {
    clearTimeout(timeoutId);
  }
}

export const api = {
  // Listings endpoints
  listings: {
    getAll: async (params?: PaginationParams): Promise<GPU[]> => {
      const queryParams = new URLSearchParams();
      if (params?.page) queryParams.append('page', params.page.toString());
      if (params?.size) queryParams.append('size', params.size.toString());

      const url = `${baseUrl}/api/listings/?${queryParams}`;
      const response = await fetchWithTimeout(url);
      return response.json();
    },

    getByModel: async (model: string): Promise<GPU[]> => {
      const url = `${baseUrl}/api/listings/${encodeURIComponent(model)}`;
      const response = await fetchWithTimeout(url);
      return response.json();
    },

    getCount: async (): Promise<{ total: number }> => {
      const response = await fetchWithTimeout(`${baseUrl}/api/listings/count/total`);
      return response.json();
    },

    getModels: async (): Promise<{ models: string[]; count: number }> => {
      const response = await fetchWithTimeout(`${baseUrl}/api/listings/models/list`);
      return response.json();
    },
  },

  // Statistics endpoints
  stats: {
    getAll: async (): Promise<ModelStats> => {
      const response = await fetchWithTimeout(`${baseUrl}/api/stats/`);
      return response.json();
    },

    getSummary: async (): Promise<SummaryStats> => {
      const response = await fetchWithTimeout(`${baseUrl}/api/stats/summary`);
      return response.json();
    },

    getByModel: async (model: string): Promise<any> => {
      const url = `${baseUrl}/api/stats/${encodeURIComponent(model)}`;
      const response = await fetchWithTimeout(url);
      return response.json();
    },
  },

  // Value analysis endpoints
  value: {
    getAll: async (): Promise<ValueAnalysis[]> => {
      const response = await fetchWithTimeout(`${baseUrl}/api/value/`);
      return response.json();
    },

    getTopN: async (n: number = 10): Promise<ValueAnalysis[]> => {
      const response = await fetchWithTimeout(`${baseUrl}/api/value/top/${n}`);
      return response.json();
    },
  },

  // WebSocket connection status
  websocket: {
    getConnections: async (): Promise<{ active_connections: number; total_connections: number }> => {
      const response = await fetchWithTimeout(`${baseUrl}/api/ws/connections`);
      return response.json();
    },
  },

  // Health check
  health: async (): Promise<any> => {
    const response = await fetchWithTimeout(`${baseUrl}/health`);
    return response.json();
  },
};

export { ApiError };
