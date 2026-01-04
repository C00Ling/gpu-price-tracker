// API service layer for backend communication
import type {
  GPU,
  ModelStats,
  SummaryStats,
  ValueAnalysis,
  PaginationParams,
} from '../types';

// Get baseUrl at runtime - check hostname directly
const getBaseUrl = () => {
  // Check if running locally
  const isLocal = window.location.hostname === 'localhost' || 
                  window.location.hostname === '127.0.0.1';
  
  if (isLocal) {
    return 'http://localhost:8000';
  }
  
  // In production, use same origin
  return window.location.origin;
};

const getTimeout = () => 30000; // 30 seconds

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
  const timeoutId = setTimeout(() => controller.abort(), getTimeout());

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

      const url = `${getBaseUrl()}/api/listings/?${queryParams}`;
      const response = await fetchWithTimeout(url);
      return response.json();
    },

    getByModel: async (model: string): Promise<GPU[]> => {
      const url = `${getBaseUrl()}/api/listings/${encodeURIComponent(model)}`;
      const response = await fetchWithTimeout(url);
      return response.json();
    },

    getCount: async (): Promise<{ total: number }> => {
      const response = await fetchWithTimeout(`${getBaseUrl()}/api/listings/count/total`);
      return response.json();
    },

    getModels: async (): Promise<{ models: string[]; count: number }> => {
      const response = await fetchWithTimeout(`${getBaseUrl()}/api/listings/models/list`);
      return response.json();
    },
  },

  // Statistics endpoints
  stats: {
    getAll: async (): Promise<ModelStats> => {
      const response = await fetchWithTimeout(`${getBaseUrl()}/api/stats/`);
      return response.json();
    },

    getSummary: async (): Promise<SummaryStats> => {
      const response = await fetchWithTimeout(`${getBaseUrl()}/api/stats/summary`);
      return response.json();
    },

    getByModel: async (model: string): Promise<any> => {
      const url = `${getBaseUrl()}/api/stats/${encodeURIComponent(model)}`;
      const response = await fetchWithTimeout(url);
      return response.json();
    },
  },

  // Value analysis endpoints
  value: {
    getAll: async (minVram?: number): Promise<ValueAnalysis[]> => {
      const queryParams = new URLSearchParams();
      if (minVram !== undefined && minVram !== null) {
        queryParams.append('min_vram', minVram.toString());
      }
      const url = `${getBaseUrl()}/api/value/?${queryParams}`;
      const response = await fetchWithTimeout(url);
      return response.json();
    },

    getTopN: async (n: number = 10): Promise<ValueAnalysis[]> => {
      const response = await fetchWithTimeout(`${getBaseUrl()}/api/value/top/${n}`);
      return response.json();
    },
  },

  // WebSocket connection status
  websocket: {
    getConnections: async (): Promise<{ active_connections: number; total_connections: number }> => {
      const response = await fetchWithTimeout(`${getBaseUrl()}/api/ws/connections`);
      return response.json();
    },
  },

  // Health check
  health: async (): Promise<any> => {
    const response = await fetchWithTimeout(`${getBaseUrl()}/health`);
    return response.json();
  },

  // Admin endpoints
  admin: {
    triggerScrape: async (): Promise<{ status: string; message: string; note?: string }> => {
      const response = await fetchWithTimeout(`${getBaseUrl()}/api/trigger-scrape`, {
        method: 'POST',
      });
      return response.json();
    },
  },

  // Utility methods
  getBaseUrl: () => getBaseUrl(),
};

export default api;
export { ApiError };
