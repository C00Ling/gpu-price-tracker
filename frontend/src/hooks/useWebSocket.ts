// WebSocket hook for real-time updates
import { useEffect, useRef, useState, useCallback } from 'react';
import type { WebSocketMessage } from '../types';

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  reconnect?: boolean;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
}

export function useWebSocket(options: UseWebSocketOptions = {}) {
  const {
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnect = true,
    reconnectInterval = 3000,
    maxReconnectAttempts = 5,
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [connectionCount, setConnectionCount] = useState(0);
  const ws = useRef<WebSocket | null>(null);
  const reconnectAttempts = useRef(0);
  const reconnectTimeout = useRef<number | undefined>(undefined);

  const connect = useCallback(() => {
    try {
      // Get WebSocket URL at runtime based on hostname
      const isLocal = window.location.hostname === 'localhost' || 
                      window.location.hostname === '127.0.0.1';
      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsHost = isLocal ? 'localhost:8000' : window.location.host;
      const wsUrl = `${wsProtocol}//${wsHost}/api/ws`;
      
      console.log('📡 Connecting to WebSocket:', wsUrl);

      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
        setConnectionCount((c) => c + 1);
        reconnectAttempts.current = 0;
        onOpen?.();
      };

      ws.current.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          console.log('📨 WebSocket message:', message);
          onMessage?.(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.current.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        onError?.(error);
      };

      ws.current.onclose = () => {
        console.log('🔌 WebSocket closed');
        setIsConnected(false);
        onClose?.();

        // Attempt to reconnect
        if (reconnect && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectAttempts.current++;
          console.log(
            `⏳ Reconnecting... (${reconnectAttempts.current}/${maxReconnectAttempts})`
          );
          reconnectTimeout.current = setTimeout(connect, reconnectInterval);
        }
      };
    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
    }
  }, [onMessage, onOpen, onClose, onError, reconnect, reconnectInterval, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current !== undefined) {
      clearTimeout(reconnectTimeout.current);
    }
    if (ws.current) {
      ws.current.close();
      ws.current = null;
    }
  }, []);

  const send = useCallback((data: any) => {
    if (ws.current && ws.current.readyState === WebSocket.OPEN) {
      ws.current.send(typeof data === 'string' ? data : JSON.stringify(data));
    } else {
      console.warn('WebSocket is not connected');
    }
  }, []);

  useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return {
    isConnected,
    connectionCount,
    send,
    disconnect,
    reconnect: connect,
  };
}
