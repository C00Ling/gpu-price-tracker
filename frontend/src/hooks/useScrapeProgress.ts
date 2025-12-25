// Hook for scraper progress with automatic WebSocket → Polling fallback
import { useState, useEffect, useRef, useCallback } from 'react';
import { useWebSocket } from './useWebSocket';

interface ScrapeProgressState {
  isRunning: boolean;
  progress: number;
  status: string;
  error: string | null;
  startedAt: string | null;
  completedAt: string | null;
}

interface UseScrapeProgressOptions {
  pollingInterval?: number; // ms between polls (default: 2000ms)
  wsFailoverTimeout?: number; // ms to wait before falling back to polling (default: 5000ms)
}

export function useScrapeProgress(options: UseScrapeProgressOptions = {}) {
  const {
    pollingInterval = 2000,
    wsFailoverTimeout = 5000
  } = options;

  const [state, setState] = useState<ScrapeProgressState>({
    isRunning: false,
    progress: 0,
    status: 'idle',
    error: null,
    startedAt: null,
    completedAt: null
  });

  const [usePolling, setUsePolling] = useState(false);
  const pollingTimeoutRef = useRef<number | undefined>(undefined);
  const wsFailoverTimerRef = useRef<number | undefined>(undefined);
  const lastUpdateRef = useRef<number>(Date.now());

  // Memoize callbacks to prevent infinite reconnection loop
  const handleMessage = useCallback((message: any) => {
    console.log('[useScrapeProgress] WebSocket message:', message);

    // Reset failover timer on successful message
    lastUpdateRef.current = Date.now();
    if (wsFailoverTimerRef.current) {
      clearTimeout(wsFailoverTimerRef.current);
      wsFailoverTimerRef.current = undefined;
    }

    switch (message.type) {
      case 'scrape_started':
        setState({
          isRunning: true,
          progress: 0,
          status: 'Започване...',
          error: null,
          startedAt: new Date().toISOString(),
          completedAt: null
        });
        // Don't use polling if WebSocket is working
        setUsePolling(false);
        break;

      case 'scrape_progress':
        setState(prev => ({
          ...prev,
          progress: message.progress ?? prev.progress,
          status: message.status ?? prev.status,
          isRunning: true
        }));
        break;

      case 'scrape_completed':
        setState(prev => ({
          ...prev,
          isRunning: false,
          progress: 100,
          status: 'Завършено! ✅',
          completedAt: new Date().toISOString()
        }));
        break;
    }
  }, []);

  const handleOpen = useCallback(() => {
    console.log('[useScrapeProgress] WebSocket connected');
    // Reset failover when connection opens
    lastUpdateRef.current = Date.now();
  }, []);

  const handleClose = useCallback(() => {
    console.log('[useScrapeProgress] WebSocket disconnected');
  }, []);

  // WebSocket connection
  const { isConnected, connectionCount } = useWebSocket({
    onMessage: handleMessage,
    onOpen: handleOpen,
    onClose: handleClose
  });

  // Poll scraper status from /api/scrape/status
  const pollStatus = async () => {
    try {
      const response = await fetch('/api/scrape/status');
      const data = await response.json();

      console.log('[useScrapeProgress] Poll status:', data);

      setState({
        isRunning: data.is_running ?? false,
        progress: data.progress ?? 0,
        status: data.status ?? 'idle',
        error: data.error ?? null,
        startedAt: data.started_at ?? null,
        completedAt: data.completed_at ?? null
      });

      // Continue polling if scraper is running
      if (data.is_running && usePolling) {
        pollingTimeoutRef.current = setTimeout(pollStatus, pollingInterval);
      }
    } catch (error) {
      console.error('[useScrapeProgress] Polling error:', error);
      // Retry polling
      if (usePolling) {
        pollingTimeoutRef.current = setTimeout(pollStatus, pollingInterval);
      }
    }
  };

  // Start polling when enabled
  useEffect(() => {
    if (usePolling) {
      console.log('[useScrapeProgress] Starting polling fallback');
      pollStatus();
    }

    return () => {
      if (pollingTimeoutRef.current) {
        clearTimeout(pollingTimeoutRef.current);
      }
    };
  }, [usePolling]);

  // Detect WebSocket failure and fall back to polling
  useEffect(() => {
    if (!isConnected || connectionCount === 0) {
      // WebSocket is not connected, start failover timer
      if (!wsFailoverTimerRef.current && !usePolling) {
        console.log('[useScrapeProgress] WebSocket not connected, starting failover timer');
        wsFailoverTimerRef.current = setTimeout(() => {
          console.log('[useScrapeProgress] Falling back to polling');
          setUsePolling(true);
        }, wsFailoverTimeout);
      }
    } else {
      // WebSocket is connected, clear failover timer
      if (wsFailoverTimerRef.current) {
        clearTimeout(wsFailoverTimerRef.current);
        wsFailoverTimerRef.current = undefined;
      }
    }

    return () => {
      if (wsFailoverTimerRef.current) {
        clearTimeout(wsFailoverTimerRef.current);
      }
    };
  }, [isConnected, connectionCount, usePolling, wsFailoverTimeout]);

  // Watch for stale WebSocket (no updates for too long while scraping)
  useEffect(() => {
    if (state.isRunning && !usePolling && isConnected) {
      const checkInterval = setInterval(() => {
        const timeSinceLastUpdate = Date.now() - lastUpdateRef.current;
        if (timeSinceLastUpdate > wsFailoverTimeout) {
          console.log('[useScrapeProgress] WebSocket stale, falling back to polling');
          setUsePolling(true);
        }
      }, 1000);

      return () => clearInterval(checkInterval);
    }
  }, [state.isRunning, usePolling, isConnected, wsFailoverTimeout]);

  return {
    ...state,
    isConnected,
    usePolling,
  };
}
