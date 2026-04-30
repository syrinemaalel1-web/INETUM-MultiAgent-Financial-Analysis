import React, { createContext, useContext, useCallback, useState } from 'react';
import { useWebSocket } from '../hooks/useWebSocket';

const WebSocketContext = createContext(null);

/**
 * WebSocket Provider Component
 * Provides a shared WebSocket connection across the entire application
 */
export const WebSocketProvider = ({ children }) => {
  const [connectionStatus, setConnectionStatus] = useState({
    isOnline: true,
    lastConnected: null,
    lastDisconnected: null
  });

  // Message handlers for different message types
  const [messageHandlers, setMessageHandlers] = useState(new Map());

  const handleMessage = useCallback((data) => {
    console.log('📨 WebSocket message received:', data);
    
    // Call all registered handlers for this message type
    const handlers = messageHandlers.get(data.type) || [];
    handlers.forEach(handler => {
      try {
        handler(data);
      } catch (error) {
        console.error('❌ Error in message handler:', error);
      }
    });

    // Call global handlers (handlers registered for '*')
    const globalHandlers = messageHandlers.get('*') || [];
    globalHandlers.forEach(handler => {
      try {
        handler(data);
      } catch (error) {
        console.error('❌ Error in global message handler:', error);
      }
    });
  }, [messageHandlers]);

  const handleConnect = useCallback(() => {
    console.log('🟢 WebSocket connection established');
    setConnectionStatus(prev => ({
      ...prev,
      isOnline: true,
      lastConnected: new Date()
    }));
  }, []);

  const handleDisconnect = useCallback((event) => {
    console.log('🔴 WebSocket connection lost');
    setConnectionStatus(prev => ({
      ...prev,
      isOnline: false,
      lastDisconnected: new Date()
    }));
  }, []);

  const handleError = useCallback((error) => {
    console.error('❌ WebSocket error:', error);
  }, []);

  const webSocket = useWebSocket({
    onMessage: handleMessage,
    onConnect: handleConnect,
    onDisconnect: handleDisconnect,
    onError: handleError,
    reconnectInterval: 3000,
    maxReconnectAttempts: 10,
    autoConnect: true
  });

  // Subscribe to specific message types
  const subscribe = useCallback((messageType, handler) => {
    setMessageHandlers(prev => {
      const newHandlers = new Map(prev);
      const handlers = newHandlers.get(messageType) || [];
      newHandlers.set(messageType, [...handlers, handler]);
      return newHandlers;
    });

    // Return unsubscribe function
    return () => {
      setMessageHandlers(prev => {
        const newHandlers = new Map(prev);
        const handlers = newHandlers.get(messageType) || [];
        const filteredHandlers = handlers.filter(h => h !== handler);
        
        if (filteredHandlers.length === 0) {
          newHandlers.delete(messageType);
        } else {
          newHandlers.set(messageType, filteredHandlers);
        }
        
        return newHandlers;
      });
    };
  }, []);

  // Convenience methods for common message types
  const subscribeToStatus = useCallback((handler) => {
    return subscribe('status', handler);
  }, [subscribe]);

  const subscribeToScrapeStatus = useCallback((handler) => {
    return subscribe('scrape_status', handler);
  }, [subscribe]);

  const subscribeToAll = useCallback((handler) => {
    return subscribe('*', handler);
  }, [subscribe]);

  const contextValue = {
    // WebSocket connection state
    ...webSocket,
    
    // Connection status
    connectionStatus,
    
    // Subscription methods
    subscribe,
    subscribeToStatus,
    subscribeToScrapeStatus,
    subscribeToAll,
    
    // Send message method
    sendMessage: webSocket.sendMessage
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
};

/**
 * Hook to use WebSocket context
 */
export const useWebSocketContext = () => {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error('useWebSocketContext must be used within a WebSocketProvider');
  }
  return context;
};

/**
 * Hook for subscribing to specific WebSocket message types
 * @param {string} messageType - The message type to subscribe to
 * @param {function} handler - The handler function
 * @param {Array} deps - Dependencies array for the handler
 */
export const useWebSocketSubscription = (messageType, handler, deps = []) => {
  const { subscribe } = useWebSocketContext();
  
  React.useEffect(() => {
    const unsubscribe = subscribe(messageType, handler);
    return unsubscribe;
  }, [subscribe, messageType, ...deps]);
};