import { useState, useEffect } from 'react';

const STORAGE_KEY = 'cmf_engine_preference';

const DEFAULT_PREFERENCE = {
  mode: 'auto',
  selected_engine: null
};

/**
 * Hook personnalisé pour gérer les préférences de moteur d'analyse
 * Sauvegarde et restaure automatiquement depuis localStorage
 */
const useEnginePreference = () => {
  const [preference, setPreference] = useState(() => {
    // Initialisation depuis localStorage
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        return { ...DEFAULT_PREFERENCE, ...parsed };
      }
    } catch (error) {
      console.error('Erreur lecture préférence:', error);
    }
    return DEFAULT_PREFERENCE;
  });

  // Sauvegarder dans localStorage à chaque changement
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(preference));
    } catch (error) {
      console.error('Erreur sauvegarde préférence:', error);
      // Fallback vers sessionStorage si localStorage échoue
      try {
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(preference));
      } catch (sessionError) {
        console.error('Erreur sauvegarde session:', sessionError);
      }
    }
  }, [preference]);

  const updatePreference = (newPreference) => {
    setPreference(prev => ({
      ...prev,
      ...newPreference
    }));
  };

  const resetPreference = () => {
    setPreference(DEFAULT_PREFERENCE);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (error) {
      console.error('Erreur reset préférence:', error);
    }
  };

  return {
    preference,
    updatePreference,
    resetPreference
  };
};

export default useEnginePreference;
