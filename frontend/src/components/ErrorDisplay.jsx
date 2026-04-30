import React from 'react';
import { ERROR_TYPES } from '../utils/errorHandler';

const ErrorDisplay = ({ 
  error, 
  onRetry, 
  showRetry = true, 
  className = '',
  size = 'normal' 
}) => {
  if (!error) return null;

  const getErrorIcon = () => {
    switch (error.type) {
      case ERROR_TYPES.NETWORK_ERROR:
        return '🌐';
      case ERROR_TYPES.SERVER_ERROR:
        return '🔧';
      case ERROR_TYPES.CLIENT_ERROR:
        return '⚠️';
      case ERROR_TYPES.TIMEOUT_ERROR:
        return '⏱️';
      default:
        return '❌';
    }
  };

  const getErrorTitle = () => {
    switch (error.type) {
      case ERROR_TYPES.NETWORK_ERROR:
        return 'Problème de connexion';
      case ERROR_TYPES.SERVER_ERROR:
        return 'Erreur du serveur';
      case ERROR_TYPES.CLIENT_ERROR:
        return 'Erreur de requête';
      case ERROR_TYPES.TIMEOUT_ERROR:
        return 'Délai d\'attente dépassé';
      default:
        return 'Erreur inattendue';
    }
  };

  const getSuggestion = () => {
    switch (error.type) {
      case ERROR_TYPES.NETWORK_ERROR:
        return 'Vérifiez que le serveur backend est démarré et accessible.';
      case ERROR_TYPES.SERVER_ERROR:
        return 'Le serveur rencontre des difficultés. Réessayez dans quelques instants.';
      case ERROR_TYPES.CLIENT_ERROR:
        return 'Vérifiez les données de la requête.';
      case ERROR_TYPES.TIMEOUT_ERROR:
        return 'La connexion est lente. Réessayez avec une meilleure connexion.';
      default:
        return 'Contactez le support si le problème persiste.';
    }
  };

  const isCompact = size === 'compact';

  return (
    <div className={`bg-red-50 border border-red-200 rounded-xl p-${isCompact ? '4' : '6'} ${className}`}>
      <div className="flex items-start space-x-3">
        <div className={`text-${isCompact ? 'lg' : '2xl'} flex-shrink-0`}>
          {getErrorIcon()}
        </div>
        
        <div className="flex-1 min-w-0">
          <h3 className={`font-semibold text-red-800 ${isCompact ? 'text-sm' : 'text-base'}`}>
            {getErrorTitle()}
          </h3>
          
          <p className={`text-red-700 mt-1 ${isCompact ? 'text-xs' : 'text-sm'}`}>
            {error.message}
          </p>
          
          {!isCompact && (
            <p className="text-red-600 text-xs mt-2 italic">
              {getSuggestion()}
            </p>
          )}
          
          {showRetry && error.canRetry && onRetry && (
            <button
              onClick={onRetry}
              className={`mt-3 bg-red-600 text-white px-3 py-1 rounded text-xs hover:bg-red-700 transition ${
                isCompact ? 'text-xs px-2 py-1' : 'text-sm px-3 py-1'
              }`}
            >
              Réessayer
            </button>
          )}
          
          {import.meta.env.DEV && error.originalError && (
            <details className="mt-3">
              <summary className="cursor-pointer text-xs text-red-600 hover:text-red-800">
                Détails techniques
              </summary>
              <div className="mt-1 p-2 bg-red-100 rounded text-xs font-mono text-red-800 overflow-auto max-h-20">
                {error.originalError.toString()}
              </div>
            </details>
          )}
        </div>
      </div>
    </div>
  );
};

export default ErrorDisplay;