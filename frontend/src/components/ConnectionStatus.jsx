import React from 'react';
import { useWebSocketContext } from '../contexts/WebSocketContext';

const ConnectionStatus = ({ className = '' }) => {
  const { 
    isConnected, 
    isConnecting, 
    isReconnecting, 
    reconnectAttempts,
    lastError,
    reconnect,
    connectionStatus 
  } = useWebSocketContext();

  const getStatusInfo = () => {
    if (isConnected) {
      return {
        color: 'bg-green-500',
        text: 'Connecté',
        description: 'Mises à jour en temps réel actives'
      };
    }
    
    if (isConnecting) {
      return {
        color: 'bg-yellow-500 animate-pulse',
        text: 'Connexion...',
        description: 'Établissement de la connexion'
      };
    }
    
    if (isReconnecting) {
      return {
        color: 'bg-orange-500 animate-pulse',
        text: 'Reconnexion...',
        description: `Tentative ${reconnectAttempts}/10`
      };
    }
    
    return {
      color: 'bg-red-500',
      text: 'Déconnecté',
      description: lastError ? 'Erreur de connexion' : 'Pas de connexion temps réel'
    };
  };

  const status = getStatusInfo();

  const handleReconnect = () => {
    reconnect();
  };

  return (
    <div className={`p-4 bg-slate-800 rounded-xl border border-slate-700 ${className}`}>
      <p className="text-xs text-gray-400 mb-2">Status Serveur</p>
      <div className="flex items-center justify-between">
        <div className="flex items-center">
          <div className={`w-2 h-2 ${status.color} rounded-full mr-2`}></div>
          <span className="text-sm font-medium text-white">{status.text}</span>
        </div>
        
        {!isConnected && !isConnecting && !isReconnecting && (
          <button
            onClick={handleReconnect}
            className="text-xs text-blue-400 hover:text-blue-300 underline"
            title="Cliquez pour reconnecter"
          >
            Reconnecter
          </button>
        )}
      </div>
      
      <p className="text-xs text-gray-500 mt-1">{status.description}</p>
      
      {/* Show additional info in development */}
      {import.meta.env.DEV && (
        <div className="mt-2 pt-2 border-t border-slate-700">
          <p className="text-xs text-gray-500">
            {connectionStatus.lastConnected && (
              <>Dernière connexion: {connectionStatus.lastConnected.toLocaleTimeString()}</>
            )}
          </p>
          {lastError && (
            <p className="text-xs text-red-400 mt-1">
              Erreur: {lastError.message || 'Connexion échouée'}
            </p>
          )}
        </div>
      )}
    </div>
  );
};

export default ConnectionStatus;