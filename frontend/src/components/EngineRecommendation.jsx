import React, { useState, useEffect } from 'react';
import './EngineRecommendation.css';

const EngineRecommendation = ({ file, onRecommendation }) => {
  const [recommendation, setRecommendation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (file) {
      fetchRecommendation(file);
    }
  }, [file]);

  const fetchRecommendation = async (file) => {
    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/engines/recommend', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        throw new Error('Erreur lors de la recommandation');
      }

      const data = await response.json();
      setRecommendation(data);
      
      // Notifier le parent
      if (onRecommendation) {
        onRecommendation(data);
      }
    } catch (err) {
      console.error('Erreur recommandation:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (!file) return null;

  if (loading) {
    return (
      <div className="engine-recommendation loading">
        <div className="spinner"></div>
        <span>Analyse du document...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="engine-recommendation error">
        <span className="error-icon">⚠️</span>
        <span>Impossible d'analyser le document</span>
      </div>
    );
  }

  if (!recommendation) return null;

  const getEngineIcon = (engine) => {
    const icons = {
      'crewai': '⚡',
      'agno': '🧠',
      'auto': '🤖'
    };
    return icons[engine] || '🔧';
  };

  const getEngineName = (engine) => {
    const names = {
      'crewai': 'CrewAI',
      'agno': 'Agno Framework',
      'auto': 'Automatique'
    };
    return names[engine] || engine;
  };

  const getConfidenceColor = (confidence) => {
    if (confidence >= 0.8) return '#4CAF50';
    if (confidence >= 0.6) return '#FF9800';
    return '#F44336';
  };

  const getConfidenceLabel = (confidence) => {
    if (confidence >= 0.8) return 'Haute confiance';
    if (confidence >= 0.6) return 'Confiance moyenne';
    return 'Faible confiance';
  };

  return (
    <div className="engine-recommendation">
      <div className="recommendation-header">
        <span className="recommendation-icon">{getEngineIcon(recommendation.engine)}</span>
        <div className="recommendation-title">
          <strong>Recommandation : {getEngineName(recommendation.engine)}</strong>
          <span 
            className="confidence-badge"
            style={{ backgroundColor: getConfidenceColor(recommendation.confidence) }}
          >
            {getConfidenceLabel(recommendation.confidence)}
          </span>
        </div>
      </div>

      <p className="recommendation-reason">{recommendation.reason}</p>

      {recommendation.document_analysis && (
        <div className="document-analysis">
          <div className="analysis-item">
            <span className="analysis-icon">📄</span>
            <span className="analysis-label">Pages estimées :</span>
            <span className="analysis-value">{recommendation.document_analysis.estimated_pages}</span>
          </div>
          
          {recommendation.document_analysis.complexity && (
            <div className="analysis-item">
              <span className="analysis-icon">📊</span>
              <span className="analysis-label">Complexité :</span>
              <span className={`analysis-value complexity-${recommendation.document_analysis.complexity}`}>
                {recommendation.document_analysis.complexity}
              </span>
            </div>
          )}

          {recommendation.document_analysis.file_size && (
            <div className="analysis-item">
              <span className="analysis-icon">💾</span>
              <span className="analysis-label">Taille :</span>
              <span className="analysis-value">
                {(recommendation.document_analysis.file_size / 1024 / 1024).toFixed(2)} MB
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default EngineRecommendation;
