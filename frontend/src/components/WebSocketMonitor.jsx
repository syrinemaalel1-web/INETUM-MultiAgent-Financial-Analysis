import React, { useEffect, useRef } from 'react';
import { useWebSocketContext } from '../contexts/WebSocketContext';
import { useNotificationContext } from './NotificationContainer';

/**
 * WebSocket Monitor Component
 * Monitors WebSocket connection status and shows notifications
 */
const WebSocketMonitor = () => {
  const { 
    isConnected, 
    isReconnecting, 
    reconnectAttempts,
    lastError,
    connectionStatus 
  } = useWebSocketContext();
  
  const { showSuccess, showError, showWarning, showInfo } = useNotificationContext();
  const previousConnectionState = useRef(null);
  const hasShownInitialConnection = useRef(false);

  useEffect(() => {
    // Don't show notification on initial connection
    if (isConnected && !hasShownInitialConnection.current) {
      hasShownInitialConnection.current = true;
      return;
    }

    // Show notification when connection is restored after being disconnected
    if (isConnected && previousConnectionState.current === false) {
      showSuccess('Connexion WebSocket rétablie', 3000);
    }
    
    // Show notification when connection is lost
    if (!isConnected && previousConnectionState.current === true) {
      showWarning('Connexion WebSocket perdue - Tentative de reconnexion...', 5000);
    }

    previousConnectionState.current = isConnected;
  }, [isConnected, showSuccess, showWarning]);

  useEffect(() => {
    // Show notification for reconnection attempts
    if (isReconnecting && reconnectAttempts > 0) {
      if (reconnectAttempts === 1) {
        showInfo('Reconnexion en cours...', 3000);
      } else if (reconnectAttempts >= 5) {
        showWarning(`Tentative de reconnexion ${reconnectAttempts}/10`, 4000);
      }
    }
  }, [isReconnecting, reconnectAttempts, showInfo, showWarning]);

  useEffect(() => {
    // Show error notification for connection errors
    if (lastError && !isConnected && !isReconnecting) {
      showError('Impossible de se connecter au serveur', 5000);
    }
  }, [lastError, isConnected, isReconnecting, showError]);

  // This component doesn't render anything visible
  return null;
};

export default WebSocketMonitor;