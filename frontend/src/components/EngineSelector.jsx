import React, { useState, useEffect } from 'react';
import './EngineSelector.css';

const EngineSelector = ({ value, onChange, recommendation }) => {
  const [engineInfo, setEngineInfo] = useState(null);
  const [showTooltip, setShowTooltip] = useState(null);

  useEffect(() => {
    // Charger les informations sur les moteurs
    fetch('/api/engines/info')
      .then(res => res.json())
      .then(data => setEngineInfo(data))
      .catch(err => console.error('Erreur chargement engine info:', err));
  }, []);

  const handleModeChange = (mode) => {
    onChange({ ...value, mode, selected_engine: mode === 'auto' ? null : value.selected_engine });
  };

  const handleEngineChange = (engine) => {
    onChange({ ...value, mode: 'manual', selected_engine: engine });
  };

  const getEngineIcon = (engine) => {
    if (!engineInfo) return '';
    return engineInfo[engine]?.icon || '';
  };

  const getEngineName = (engine) => {
    if (!engineInfo) return engine;
    return engineInfo[engine]?.name || engine;
  };

  const getEngineDescription = (engine) => {
    if (!engineInfo) return '';
    return engineInfo[engine]?.description || '';
  };

  const renderEngineCard = (engineKey) => {
    if (!engineInfo || !engineInfo[engineKey]) return null;

    const engine = engineInfo[engineKey];
    const isSelected = value.mode === 'manual' && value.selected_engine === engineKey;
    const isRecommended = recommendation && recommendation.engine === engineKey;

    return (
      <div
        key={engineKey}
        className={`engine-card ${isSelected ? 'selected' : ''} ${isRecommended ? 'recommended' : ''}`}
        onClick={() => handleEngineChange(engineKey)}
        onMouseEnter={() => setShowTooltip(engineKey)}
        onMouseLeave={() => setShowTooltip(null)}
      >
        <div className="engine-header">
          <span className="engine-icon">{engine.icon}</span>
          <span className="engine-name">{engine.name}</span>
          {isRecommended && <span className="recommended-badge">Recommandé</span>}
        </div>
        
        <p className="engine-description">{engine.description}</p>

        {showTooltip === engineKey && (
          <div className="engine-tooltip">
            <div className="tooltip-section">
              <strong>Idéal pour :</strong>
              <ul>
                {engine.best_for.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
            <div className="tooltip-section">
              <strong>Limitations :</strong>
              <ul>
                {engine.limitations.map((item, idx) => (
                  <li key={idx}>{item}</li>
                ))}
              </ul>
            </div>
            {engine.performance && (
              <div className="tooltip-section">
                <strong>Performance :</strong>
                <ul>
                  <li>Vitesse : {engine.performance.speed}</li>
                  <li>Fiabilité : {engine.performance.reliability}</li>
                  <li>Coût : {engine.performance.cost}</li>
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="engine-selector">
      <h3>Moteur d'Analyse</h3>
      
      <div className="mode-selector">
        <label className={`mode-option ${value.mode === 'auto' ? 'active' : ''}`}>
          <input
            type="radio"
            name="mode"
            value="auto"
            checked={value.mode === 'auto'}
            onChange={() => handleModeChange('auto')}
          />
          <span className="mode-icon">🤖</span>
          <span className="mode-label">Automatique</span>
          <span className="mode-description">Le système choisit le meilleur moteur</span>
        </label>

        <label className={`mode-option ${value.mode === 'manual' ? 'active' : ''}`}>
          <input
            type="radio"
            name="mode"
            value="manual"
            checked={value.mode === 'manual'}
            onChange={() => handleModeChange('manual')}
          />
          <span className="mode-icon">👤</span>
          <span className="mode-label">Manuel</span>
          <span className="mode-description">Vous choisissez le moteur</span>
        </label>
      </div>

      {value.mode === 'manual' && engineInfo && (
        <div className="engine-cards">
          {renderEngineCard('crewai')}
          {renderEngineCard('agno')}
        </div>
      )}

      {value.mode === 'auto' && recommendation && (
        <div className="auto-recommendation">
          <div className="recommendation-icon">💡</div>
          <div className="recommendation-content">
            <strong>Recommandation :</strong> {getEngineName(recommendation.engine)}
            <p className="recommendation-reason">{recommendation.reason}</p>
            {recommendation.document_analysis && (
              <div className="document-stats">
                <span>📄 {recommendation.document_analysis.estimated_pages} pages estimées</span>
                <span>📊 Complexité : {recommendation.document_analysis.complexity}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {value.mode === 'manual' && !value.selected_engine && (
        <div className="selection-prompt">
          ⬆️ Sélectionnez un moteur d'analyse ci-dessus
        </div>
      )}
    </div>
  );
};

export default EngineSelector;
