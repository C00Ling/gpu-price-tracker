// Application configuration
// Dynamically determine API URL based on environment
const getApiUrl = () => {
  // Use environment variable if set
  if (import.meta.env.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  
  // Check if running locally (localhost or 127.0.0.1)
  const isLocal = window.location.hostname === 'localhost' || 
                  window.location.hostname === '127.0.0.1';
  
  if (isLocal) {
    return 'http://localhost:8000';
  }
  
  // In production, use same origin (same domain)
  return window.location.origin;
};

const getWsUrl = () => {
  // Use environment variable if set
  if (import.meta.env.VITE_WS_URL) {
    return import.meta.env.VITE_WS_URL;
  }
  
  // Check if running locally
  const isLocal = window.location.hostname === 'localhost' || 
                  window.location.hostname === '127.0.0.1';
  
  if (isLocal) {
    return 'ws://localhost:8000';
  }
  
  // In production, use same origin with ws protocol
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}`;
};

export const config = {
  api: {
    baseUrl: getApiUrl(),
    wsUrl: getWsUrl(),
    timeout: 30000,
  },
  app: {
    name: 'GPU Market',
    description: 'Анализ на цени на видео карти в България',
    version: '1.2.0',
  },
  cache: {
    staleTime: 5 * 60 * 1000, // 5 minutes
    cacheTime: 10 * 60 * 1000, // 10 minutes
  },
} as const;
