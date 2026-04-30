import React, { useState, useEffect } from 'react';
import { getApiUrl, API_CONFIG } from '../config/api';
import { useWebSocketSubscription } from '../contexts/WebSocketContext';
import { useNotificationContext } from './NotificationContainer';
import { analyzeError, fetchWithTimeout, retryRequest } from '../utils/errorHandler';
import ErrorDisplay from './ErrorDisplay';
import LoadingState from './LoadingState';
import EngineSelector from './EngineSelector';
import useEnginePreference from '../hooks/useEnginePreference';

const DocumentList = ({ onSelectReport, onSelectKPIs }) => {
  const [docs, setDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showOptions, setShowOptions] = useState(null);
  const [showEngineModal, setShowEngineModal] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState(null);
  const { showError, showSuccess } = useNotificationContext();
  const { preference, updatePreference } = useEnginePreference();

  const fetchDocs = async (showLoadingState = true) => {
    if (showLoadingState) {
      setLoading(true);
    }
    setError(null);

    try {
      const response = await retryRequest(
        () => fetchWithTimeout(getApiUrl(API_CONFIG.ENDPOINTS.DOCUMENTS)),
        2, // Max 2 retries
        1000 // 1 second delay
      );
      
      const data = await response.json();
      setDocs(data);
      setError(null);
    } catch (err) {
      console.error('Failed to fetch documents:', err);
      const errorInfo = await analyzeError(err);
      setError(errorInfo);
      
      // Show notification for network errors
      if (!errorInfo.isServerReachable) {
        showError('Impossible de charger les documents. Vérifiez la connexion au serveur.', 5000);
      }
    } finally {
      setLoading(false);
    }
  };

  // Subscribe to WebSocket status updates
  useWebSocketSubscription('status', (data) => {
    console.log("📄 Document status update received:", data);
    fetchDocs(false); // Reload without showing loading state
    
    // Show success notification for completed analysis
    if (data.status === 'completed') {
      showSuccess(`Analyse terminée pour ${data.filename}`, 4000);
    }
  }, []);

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleProcess = async (filename, mode) => {
    // Ouvrir le modal de sélection de moteur
    setSelectedDoc({ filename, mode });
    setShowEngineModal(true);
    setShowOptions(null);
  };

  const handleConfirmProcess = async () => {
    if (!selectedDoc) return;

    try {
      const response = await fetchWithTimeout(
        getApiUrl(API_CONFIG.ENDPOINTS.PROCESS(selectedDoc.filename)), 
        { 
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            engine_mode: preference.mode,
            selected_engine: preference.selected_engine
          })
        }
      );
      
      if (response.ok) {
        const result = await response.json();
        setShowEngineModal(false);
        setSelectedDoc(null);
        
        const engineInfo = preference.mode === 'manual' && preference.selected_engine
          ? ` avec ${preference.selected_engine === 'crewai' ? 'CrewAI ⚡' : 'Agno 🧠'}`
          : ' en mode automatique 🤖';
        
        showSuccess(`Analyse lancée${engineInfo}! La liste se mettra à jour automatiquement.`, 5000);
      }
    } catch (err) {
      console.error('Failed to start processing:', err);
      const errorInfo = await analyzeError(err);
      showError(`Erreur lors du lancement: ${errorInfo.message}`, 5000);
    }
  };

  const handleRetry = () => {
    fetchDocs();
  };

  // Show loading state
  if (loading) {
    return <LoadingState message="Chargement des documents..." />;
  }

  // Show error state
  if (error) {
    return (
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <ErrorDisplay 
          error={error} 
          onRetry={handleRetry}
          showRetry={true}
        />
      </div>
    );
  }

  return (
    <>
      <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
        <table className="w-full text-left">
          <thead className="bg-gray-50 border-b border-gray-100">
            <tr>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">Fichier PDF</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">Status Extraction</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">Rapport IA</th>
              <th className="px-6 py-4 text-sm font-semibold text-gray-600">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {docs.map((doc, i) => (
              <tr key={i} className="hover:bg-gray-50 transition">
                <td className="px-6 py-4">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-red-50 rounded flex items-center justify-center text-white font-bold text-xs mr-3">PDF</div>
                    <span className="text-sm font-medium text-gray-800">{doc.filename}</span>
                  </div>
                </td>
                <td className="px-6 py-4">
                  {doc.has_md ? (
                    <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-semibold">Markdown Prêt</span>
                  ) : (
                    <span className="px-2 py-1 bg-gray-100 text-gray-500 rounded-full text-xs font-semibold">Brut</span>
                  )}
                </td>
                <td className="px-6 py-4">
                  {doc.status === 'completed' ? (
                    <span className="px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-semibold">Analysé ✓</span>
                  ) : doc.status === 'processing' ? (
                    <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold animate-pulse">En cours...</span>
                  ) : (
                    <span className="px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full text-xs font-semibold">Non Analysé</span>
                  )}
                </td>
                <td className="px-6 py-4 relative">
                  <div className="flex space-x-4">
                    {doc.status !== 'completed' ? (
                      <div className="relative">
                        <button 
                          onClick={() => setShowOptions(showOptions === doc.filename ? null : doc.filename)}
                          disabled={doc.status === 'processing'}
                          className={`text-sm font-semibold flex items-center ${doc.status === 'processing' ? 'text-gray-400 cursor-not-allowed' : 'text-blue-600 hover:text-blue-800'}`}
                        >
                          {doc.status === 'processing' ? 'Analyse en cours...' : "Lancer l'Analyse"} <span className="ml-1 text-[10px]">▼</span>
                        </button>
                        
                        {showOptions === doc.filename && (
                          <div className="absolute top-0 left-0 mt-8 w-48 bg-white rounded-xl shadow-xl border border-gray-100 z-50 overflow-hidden">
                            <button 
                              onClick={() => handleProcess(doc.filename, 'rapport')}
                              className="w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-700 transition"
                            >
                              📄 Vers le Rapport
                            </button>
                            <button 
                              onClick={() => handleProcess(doc.filename, 'kpis')}
                              className="w-full text-left px-4 py-3 text-sm text-gray-700 hover:bg-blue-50 hover:text-blue-700 transition border-t border-gray-50"
                            >
                              📊 Vers les KPIs
                            </button>
                          </div>
                        )}
                      </div>
                    ) : (
                      <div className="flex space-x-3">
                        <button 
                          onClick={() => onSelectReport(doc.filename)}
                          className="text-green-600 hover:text-green-800 text-sm font-semibold"
                        >
                          Rapport
                        </button>
                        <button 
                          onClick={() => onSelectKPIs(doc.filename)}
                          className="text-purple-600 hover:text-purple-800 text-sm font-semibold"
                        >
                          KPIs
                        </button>
                      </div>
                    )}
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {docs.length === 0 && <div className="p-10 text-center text-gray-500">Aucun document trouvé. Lancez le scraper !</div>}
      </div>

      {/* Modal de sélection de moteur */}
      {showEngineModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6 border-b border-gray-100">
              <h3 className="text-xl font-bold text-gray-800">Choisir le Moteur d'Analyse</h3>
              <p className="text-sm text-gray-600 mt-1">
                Document : <span className="font-semibold">{selectedDoc?.filename}</span>
              </p>
            </div>

            <div className="p-6">
              <EngineSelector 
                value={preference}
                onChange={updatePreference}
              />
            </div>

            <div className="p-6 border-t border-gray-100 flex justify-end gap-3">
              <button
                onClick={() => {
                  setShowEngineModal(false);
                  setSelectedDoc(null);
                }}
                className="px-6 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition font-semibold"
              >
                Annuler
              </button>
              <button
                onClick={handleConfirmProcess}
                disabled={preference.mode === 'manual' && !preference.selected_engine}
                className={`px-6 py-2 rounded-lg font-semibold transition ${
                  preference.mode === 'manual' && !preference.selected_engine
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                Lancer l'Analyse
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

export default DocumentList;
