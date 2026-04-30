import React from 'react';

const LoadingState = ({ 
  message = 'Chargement...', 
  size = 'normal',
  showSpinner = true,
  className = '' 
}) => {
  const isCompact = size === 'compact';
  
  return (
    <div className={`flex items-center justify-center ${isCompact ? 'py-4' : 'py-10'} ${className}`}>
      <div className="flex items-center space-x-3">
        {showSpinner && (
          <div className={`animate-spin rounded-full border-2 border-blue-200 border-t-blue-600 ${
            isCompact ? 'w-4 h-4' : 'w-6 h-6'
          }`}></div>
        )}
        <span className={`text-gray-600 ${isCompact ? 'text-sm' : 'text-base'}`}>
          {message}
        </span>
      </div>
    </div>
  );
};

export default LoadingState;