import React, { useState, useEffect } from 'react';
import Dashboard from './components/Dashboard';
import DocumentList from './components/DocumentList';
import ScraperControl from './components/ScraperControl';
import ReportView from './components/ReportView';
import KPIDashboard from './components/KPIDashboard';
import ConnectionStatus from './components/ConnectionStatus';
import ErrorBoundary from './components/ErrorBoundary';
import { NotificationProvider } from './components/NotificationContainer';
import WebSocketMonitor from './components/WebSocketMonitor';
import { WebSocketProvider, useWebSocketSubscription } from './contexts/WebSocketContext';
import { getApiUrl, API_CONFIG } from './config/api';
import { analyzeError, fetchWithTimeout } from './utils/errorHandler';
import './utils/validateConfig'; // Import validation (runs automatically in dev mode)

// Main App Component (wrapped by WebSocketProvider)
const AppContent = () => {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [stats, setStats] = useState({ raw_pdfs: 0, processed_mds: 0, reports_generated: 0, is_scraping: false });
  const [statsError, setStatsError] = useState(null);
  const [selectedReport, setSelectedReport] = useState(null);

  const fetchStats = async () => {
    try {
      const response = await fetchWithTimeout(getApiUrl(API_CONFIG.ENDPOINTS.STATS));
      const data = await response.json();
      setStats(data);
      setStatsError(null);
    } catch (err) {
      console.error("Failed to fetch stats", err);
      const errorInfo = await analyzeError(err);
      setStatsError(errorInfo);
      
      // Keep previous stats if available, don't reset to zero
      if (stats.raw_pdfs === 0 && stats.processed_mds === 0) {
        // Only show error state if we have no previous data
        console.warn('Stats unavailable:', errorInfo.message);
      }
    }
  };

  // Subscribe to WebSocket messages that should trigger stats refresh
  useWebSocketSubscription('status', (data) => {
    console.log('📊 Status update received:', data);
    fetchStats();
  }, []);

  useWebSocketSubscription('scrape_status', (data) => {
    console.log('🔍 Scrape status update received:', data);
    fetchStats();
  }, []);

  useEffect(() => {
    fetchStats();
  }, []);

  return (
    <div className="min-h-screen bg-gray-50 font-sans text-gray-900">
      {/* WebSocket Monitor for connection notifications */}
      <WebSocketMonitor />
      
      {/* Sidebar */}
      <nav className="fixed top-0 left-0 h-full w-64 bg-slate-900 text-white p-6 shadow-xl">
        <div className="mb-10">
          <h1 className="text-2xl font-bold text-blue-400">CMF Analyse</h1>
          <p className="text-xs text-gray-400 uppercase tracking-widest mt-1">Intelligence Financière</p>
        </div>
        
        <div className="space-y-2">
          <button 
            onClick={() => setActiveTab('dashboard')}
            className={`w-full text-left px-4 py-3 rounded-lg transition ${activeTab === 'dashboard' ? 'bg-blue-600' : 'hover:bg-slate-800'}`}
          >
            Dashboard
          </button>
          <button 
            onClick={() => setActiveTab('documents')}
            className={`w-full text-left px-4 py-3 rounded-lg transition ${activeTab === 'documents' ? 'bg-blue-600' : 'hover:bg-slate-800'}`}
          >
            Documents
          </button>
          <button 
            onClick={() => setActiveTab('scraper')}
            className={`w-full text-left px-4 py-3 rounded-lg transition ${activeTab === 'scraper' ? 'bg-blue-600' : 'hover:bg-slate-800'}`}
          >
            Collecte (Scraper)
          </button>
        </div>

        <div className="absolute bottom-10 left-6 right-6">
          <ConnectionStatus />
        </div>
      </nav>

      {/* Main Content */}
      <main className="ml-64 p-8">
        <header className="flex justify-between items-center mb-8">
          <h2 className="text-3xl font-bold text-slate-800 capitalize">{activeTab}</h2>
          <div className="flex items-center space-x-4">
            <span className="text-sm text-gray-500">{new Date().toLocaleDateString('fr-FR')}</span>
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center text-blue-600 font-bold">
              ST
            </div>
          </div>
        </header>

        {activeTab === 'dashboard' && <Dashboard stats={stats} statsError={statsError} />}
        {activeTab === 'documents' && <DocumentList 
          onSelectReport={(name) => { setSelectedReport(name); setActiveTab('report'); }} 
          onSelectKPIs={(name) => { setSelectedReport(name); setActiveTab('kpis'); }}
        />}
        {activeTab === 'scraper' && <ScraperControl isScraping={stats.is_scraping} onUpdate={fetchStats} />}
        {activeTab === 'report' && <ReportView filename={selectedReport} onBack={() => setActiveTab('documents')} />}
        {activeTab === 'kpis' && <KPIDashboard filename={selectedReport} onBack={() => setActiveTab('documents')} />}
      </main>
    </div>
  );
};

function App() {
  return (
    <ErrorBoundary>
      <WebSocketProvider>
        <NotificationProvider>
          <AppContent />
        </NotificationProvider>
      </WebSocketProvider>
    </ErrorBoundary>
  );
}

export default App;
