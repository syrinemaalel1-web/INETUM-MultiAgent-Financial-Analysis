import React, { useState } from 'react';
import { getApiUrl, API_CONFIG } from '../config/api';
import { useNotificationContext } from './NotificationContainer';
import { analyzeError, fetchWithTimeout } from '../utils/errorHandler';

const ScraperControl = ({ isScraping, onUpdate }) => {
  const [params, setParams] = useState({ page_start: 0, page_end: 2, societe_filter: '' });
  const [isStarting, setIsStarting] = useState(false);
  const { showError, showSuccess } = useNotificationContext();

  const handleStart = async () => {
    setIsStarting(true);
    
    try {
      const response = await fetchWithTimeout(
        getApiUrl(API_CONFIG.ENDPOINTS.SCRAPE),
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(params)
        },
        15000 // 15 second timeout for scraping requests
      );

      if (response.ok) {
        showSuccess("Scraping lancé avec succès !", 4000);
        onUpdate();
      }
    } catch (err) {
      console.error('Failed to start scraping:', err);
      const errorInfo = await analyzeError(err);
      showError(`Erreur lors du lancement du scraper: ${errorInfo.message}`, 6000);
    } finally {
      setIsStarting(false);
    }
  };

  return (
    <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 max-w-2xl">
      <h3 className="text-xl font-bold mb-6">Paramètres de Collecte CMF</h3>
      
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Page Début</label>
            <input 
              type="number" 
              value={params.page_start}
              onChange={(e) => setParams({...params, page_start: parseInt(e.target.value)})}
              className="w-full p-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Page Fin</label>
            <input 
              type="number" 
              value={params.page_end}
              onChange={(e) => setParams({...params, page_end: parseInt(e.target.value)})}
              className="w-full p-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Filtre Société (Optionnel)</label>
          <input 
            type="text" 
            placeholder="Ex: ATTIJARI BANK"
            value={params.societe_filter}
            onChange={(e) => setParams({...params, societe_filter: e.target.value})}
            className="w-full p-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 outline-none"
          />
        </div>

        <button 
          onClick={handleStart}
          disabled={isScraping || isStarting}
          className={`w-full py-3 rounded-lg font-bold text-white transition ${
            isScraping || isStarting 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-blue-600 hover:bg-blue-700'
          }`}
        >
          {isScraping 
            ? 'Collecte en cours...' 
            : isStarting 
              ? 'Démarrage...' 
              : 'Lancer le Scraper'
          }
        </button>

        <p className="text-xs text-gray-500 mt-4 italic">
          Note : Le scraper utilise CrewAI pour identifier les liens et un script optimisé pour le téléchargement des PDFs.
        </p>
      </div>
    </div>
  );
};

export default ScraperControl;
