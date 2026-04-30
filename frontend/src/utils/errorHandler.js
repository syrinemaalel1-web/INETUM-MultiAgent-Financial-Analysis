/**
 * Error handling utilities for API requests
 */

export const ERROR_TYPES = {
  NETWORK_ERROR: 'NETWORK_ERROR',
  SERVER_ERROR: 'SERVER_ERROR',
  CLIENT_ERROR: 'CLIENT_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  UNKNOWN_ERROR: 'UNKNOWN_ERROR'
};

export const ERROR_MESSAGES = {
  [ERROR_TYPES.NETWORK_ERROR]: 'Impossible de se connecter au serveur. Vérifiez votre connexion internet.',
  [ERROR_TYPES.SERVER_ERROR]: 'Erreur du serveur. Veuillez réessayer plus tard.',
  [ERROR_TYPES.CLIENT_ERROR]: 'Erreur de requête. Vérifiez les données envoyées.',
  [ERROR_TYPES.TIMEOUT_ERROR]: 'La requête a pris trop de temps. Veuillez réessayer.',
  [ERROR_TYPES.UNKNOWN_ERROR]: 'Une erreur inattendue s\'est produite.'
};

/**
 * Analyzes an error and returns structured error information
 * @param {Error|Response} error - The error to analyze
 * @returns {Object} Structured error information
 */
export const analyzeError = async (error) => {
  // Network/Connection errors (fetch failed)
  if (error instanceof TypeError && error.message.includes('fetch')) {
    return {
      type: ERROR_TYPES.NETWORK_ERROR,
      message: ERROR_MESSAGES[ERROR_TYPES.NETWORK_ERROR],
      isServerReachable: false,
      canRetry: true,
      originalError: error
    };
  }

  // AbortError (timeout)
  if (error.name === 'AbortError') {
    return {
      type: ERROR_TYPES.TIMEOUT_ERROR,
      message: ERROR_MESSAGES[ERROR_TYPES.TIMEOUT_ERROR],
      isServerReachable: false,
      canRetry: true,
      originalError: error
    };
  }

  // HTTP Response errors
  if (error instanceof Response) {
    const status = error.status;
    let errorData = null;
    
    try {
      errorData = await error.json();
    } catch {
      // Response body is not JSON
    }

    if (status >= 500) {
      return {
        type: ERROR_TYPES.SERVER_ERROR,
        message: errorData?.detail || ERROR_MESSAGES[ERROR_TYPES.SERVER_ERROR],
        isServerReachable: true,
        canRetry: true,
        status,
        originalError: error
      };
    }

    if (status >= 400) {
      return {
        type: ERROR_TYPES.CLIENT_ERROR,
        message: errorData?.detail || ERROR_MESSAGES[ERROR_TYPES.CLIENT_ERROR],
        isServerReachable: true,
        canRetry: false,
        status,
        originalError: error
      };
    }
  }

  // Unknown error
  return {
    type: ERROR_TYPES.UNKNOWN_ERROR,
    message: error.message || ERROR_MESSAGES[ERROR_TYPES.UNKNOWN_ERROR],
    isServerReachable: false,
    canRetry: true,
    originalError: error
  };
};

/**
 * Enhanced fetch wrapper with timeout and error handling
 * @param {string} url - The URL to fetch
 * @param {Object} options - Fetch options
 * @param {number} timeout - Timeout in milliseconds (default: 10000)
 * @returns {Promise} Enhanced fetch promise
 */
export const fetchWithTimeout = async (url, options = {}, timeout = 10000) => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      throw response;
    }

    return response;
  } catch (error) {
    clearTimeout(timeoutId);
    throw error;
  }
};

/**
 * Retry mechanism for failed requests
 * @param {Function} requestFn - Function that returns a promise
 * @param {number} maxRetries - Maximum number of retries
 * @param {number} delay - Delay between retries in milliseconds
 * @returns {Promise} Promise that resolves with the result or rejects with the last error
 */
export const retryRequest = async (requestFn, maxRetries = 3, delay = 1000) => {
  let lastError;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      lastError = error;
      
      if (attempt === maxRetries) {
        break;
      }

      // Don't retry client errors (4xx)
      const errorInfo = await analyzeError(error);
      if (errorInfo.type === ERROR_TYPES.CLIENT_ERROR) {
        break;
      }

      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, attempt)));
    }
  }

  throw lastError;
};