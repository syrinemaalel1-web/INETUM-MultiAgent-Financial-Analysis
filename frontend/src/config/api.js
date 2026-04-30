// API Configuration
// This file centralizes all API endpoint configurations

// Get environment variables with fallbacks
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';

// Remove trailing slashes if present
const cleanUrl = (url) => url.replace(/\/$/, '');

export const API_CONFIG = {
  BASE_URL: cleanUrl(API_BASE_URL),
  WS_URL: cleanUrl(WS_BASE_URL),
  
  // API Endpoints
  ENDPOINTS: {
    STATS: '/stats',
    DOCUMENTS: '/documents',
    SCRAPE: '/scrape',
    PROCESS: (filename) => `/process/${filename}`,
    REPORT: (filename) => `/report/${filename}`,
    KPIS: (filename) => `/kpis/${filename}`,
    UPLOAD: '/upload',
    WEBSOCKET: '/ws'
  }
};

// Helper functions for building full URLs
export const getApiUrl = (endpoint) => `${API_CONFIG.BASE_URL}${endpoint}`;
export const getWsUrl = (endpoint = '') => `${API_CONFIG.WS_URL}${endpoint}`;

// Export commonly used URLs
export const API_URL = API_CONFIG.BASE_URL;
export const WS_URL = API_CONFIG.WS_URL;