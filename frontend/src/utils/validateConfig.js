// Configuration validation utility
import { API_CONFIG } from '../config/api';

export const validateConfiguration = () => {
  const issues = [];
  
  // Check if environment variables are properly loaded
  if (!import.meta.env.VITE_API_URL) {
    issues.push('VITE_API_URL environment variable is not set');
  }
  
  if (!import.meta.env.VITE_WS_URL) {
    issues.push('VITE_WS_URL environment variable is not set');
  }
  
  // Check if URLs are valid
  try {
    new URL(API_CONFIG.BASE_URL);
  } catch (error) {
    issues.push(`Invalid API_BASE_URL: ${API_CONFIG.BASE_URL}`);
  }
  
  // Check if WebSocket URL is valid
  if (!API_CONFIG.WS_URL.startsWith('ws://') && !API_CONFIG.WS_URL.startsWith('wss://')) {
    issues.push(`Invalid WebSocket URL format: ${API_CONFIG.WS_URL}`);
  }
  
  return {
    isValid: issues.length === 0,
    issues,
    config: {
      apiUrl: API_CONFIG.BASE_URL,
      wsUrl: API_CONFIG.WS_URL,
      environment: import.meta.env.MODE
    }
  };
};

// Log configuration on development
if (import.meta.env.DEV) {
  const validation = validateConfiguration();
  console.log('🔧 Frontend Configuration:', validation.config);
  
  if (!validation.isValid) {
    console.warn('⚠️ Configuration Issues:', validation.issues);
  } else {
    console.log('✅ Configuration is valid');
  }
}