import { useEffect, useRef, useCallback, useState } from 'react';
import { getWsUrl, API_CONFIG } from '../config/api';

/**
 * Custom hook for managing WebSocket connections with automatic reconnection
 * @param {Object} options - Configuration options
 * @param {function} options.onMessage - Message handler function
 * @param {function} options.onConnect - Connection established handler
 * @param {function} options.onDisconnect - Connection lost handler
 * @param {function} options.onError - Error handler
 * @param {number} options.reconnectInterval - Reconnection interval in ms (default: 3000)
 * @param {number} options.maxReconnectAttempts - Max reconnection attempts (default: 10)
 * @param {boolean} options.autoConnect - Auto connect on mount (default: true)
 * @returns {Object} WebSocket connection state and controls
 */
export const useWebSocket = (options = {}) => {
  const {
    onMessage,
    onConnect,
    onDisconnect,
    onError,
    reconnectInterval = 3000,
    maxReconnectAttempts = 10,
    autoConnect = true
  } = options;

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttemptsRef = useRef(0);
  const isManuallyClosedRef = useRef(false);
  const mountedRef = useRef(true);

  const [connectionState, setConnectionState] = useState({
    isConnected: false,
    isConnecting: false,
    isReconnecting: false,
    reconnectAttempts: 0,
    lastError: null
  });

  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  const updateConnectionState = useCallback((updates) => {
    if (mountedRef.current) {
      setConnectionState(prev => ({ ...prev, ...updates }));
    }
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      return; // Already connecting
    }

    try {
      updateConnectionState({ 
        isConnecting: true, 
        lastError: null 
      });

      const wsUrl = getWsUrl(API_CONFIG.ENDPOINTS.WEBSOCKET);
      console.log(`🔌 Connecting to WebSocket: ${wsUrl}`);
      
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onopen = () => {
        if (!mountedRef.current) return;
        
        console.log('✅ WebSocket connected');
        reconnectAttemptsRef.current = 0;
        isManuallyClosedRef.current = false;
        
        updateConnectionState({
          isConnected: true,
          isConnecting: false,
          isReconnecting: false,
          reconnectAttempts: 0,
          lastError: null
        });

        onConnect?.();
      };

      wsRef.current.onmessage = (event) => {
        if (!mountedRef.current) return;
        
        try {
          const data = JSON.parse(event.data);
          onMessage?.(data, event);
        } catch (error) {
          console.error('❌ WebSocket message parsing error:', error);
          onError?.(error);
        }
      };

      wsRef.current.onclose = (event) => {
        if (!mountedRef.current) return;

        console.log(`🔌 WebSocket closed: ${event.code} - ${event.reason}`);
        
        updateConnectionState({
          isConnected: false,
          isConnecting: false
        });

        onDisconnect?.(event);

        // Only attempt reconnection if not manually closed and within attempt limits
        if (!isManuallyClosedRef.current && 
            reconnectAttemptsRef.current < maxReconnectAttempts &&
            mountedRef.current) {
          
          reconnectAttemptsRef.current += 1;
          
          updateConnectionState({
            isReconnecting: true,
            reconnectAttempts: reconnectAttemptsRef.current
          });

          console.log(`🔄 Attempting reconnection ${reconnectAttemptsRef.current}/${maxReconnectAttempts} in ${reconnectInterval}ms`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current && !isManuallyClosedRef.current) {
              connect();
            }
          }, reconnectInterval);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          console.error('❌ Max reconnection attempts reached');
          updateConnectionState({
            isReconnecting: false,
            lastError: new Error('Max reconnection attempts reached')
          });
        }
      };

      wsRef.current.onerror = (error) => {
        if (!mountedRef.current) return;
        
        console.error('❌ WebSocket error:', error);
        
        updateConnectionState({
          lastError: error,
          isConnecting: false
        });

        onError?.(error);
      };

    } catch (error) {
      console.error('❌ WebSocket connection error:', error);
      updateConnectionState({
        isConnecting: false,
        lastError: error
      });
      onError?.(error);
    }
  }, [onMessage, onConnect, onDisconnect, onError, reconnectInterval, maxReconnectAttempts, updateConnectionState]);

  const disconnect = useCallback(() => {
    console.log('🔌 Manually disconnecting WebSocket');
    isManuallyClosedRef.current = true;
    clearReconnectTimeout();
    
    if (wsRef.current) {
      wsRef.current.close(1000, 'Manual disconnect');
      wsRef.current = null;
    }
    
    updateConnectionState({
      isConnected: false,
      isConnecting: false,
      isReconnecting: false,
      reconnectAttempts: 0
    });
  }, [clearReconnectTimeout, updateConnectionState]);

  const reconnect = useCallback(() => {
    console.log('🔄 Manual reconnection requested');
    reconnectAttemptsRef.current = 0;
    isManuallyClosedRef.current = false;
    disconnect();
    setTimeout(connect, 100); // Small delay to ensure clean disconnect
  }, [connect, disconnect]);

  const sendMessage = useCallback((data) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      try {
        const message = typeof data === 'string' ? data : JSON.stringify(data);
        wsRef.current.send(message);
        return true;
      } catch (error) {
        console.error('❌ WebSocket send error:', error);
        onError?.(error);
        return false;
      }
    } else {
      console.warn('⚠️ WebSocket not connected, cannot send message');
      return false;
    }
  }, [onError]);

  // Auto-connect on mount
  useEffect(() => {
    if (autoConnect) {
      connect();
    }

    return () => {
      mountedRef.current = false;
      clearReconnectTimeout();
      if (wsRef.current) {
        isManuallyClosedRef.current = true;
        wsRef.current.close(1000, 'Component unmounting');
      }
    };
  }, [autoConnect, connect, clearReconnectTimeout]);

  return {
    // Connection state
    ...connectionState,
    
    // Connection controls
    connect,
    disconnect,
    reconnect,
    sendMessage,
    
    // WebSocket instance (for advanced usage)
    ws: wsRef.current
  };
};