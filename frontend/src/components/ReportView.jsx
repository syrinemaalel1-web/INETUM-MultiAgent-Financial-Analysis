import React, { useState, useEffect, useRef } from 'react';
import { getApiUrl, API_CONFIG } from '../config/api';
import { analyzeError, fetchWithTimeout } from '../utils/errorHandler';
import ErrorDisplay from './ErrorDisplay';
import LoadingState from './LoadingState';

/* ─────────────────── helpers ─────────────────── */
const SECTION_META = {
  'résumé exécutif':            { icon: '📋', gradient: 'from-blue-600 to-indigo-700',   light: 'bg-blue-50 border-blue-100',  text: 'text-blue-700'  },
  'performance opérationnelle': { icon: '📈', gradient: 'from-emerald-600 to-teal-700',  light: 'bg-emerald-50 border-emerald-100', text: 'text-emerald-700' },
  'structure financière':       { icon: '🏛️', gradient: 'from-amber-500 to-orange-600', light: 'bg-amber-50 border-amber-100', text: 'text-amber-700'  },
  'liquidité':                  { icon: '💧', gradient: 'from-cyan-500 to-sky-600',     light: 'bg-cyan-50 border-cyan-100',   text: 'text-cyan-700'  },
  'recommandations':            { icon: '🎯', gradient: 'from-purple-600 to-violet-700', light: 'bg-purple-50 border-purple-100',text: 'text-purple-700'},
  'fiabilité':                  { icon: '✅', gradient: 'from-slate-600 to-gray-700',    light: 'bg-slate-50 border-slate-100', text: 'text-slate-600'  },
};

const getMeta = (heading) => {
  const key = Object.keys(SECTION_META).find(k => heading.toLowerCase().includes(k));
  return key ? SECTION_META[key] : { icon: '📌', gradient: 'from-gray-500 to-gray-600', light: 'bg-gray-50 border-gray-100', text: 'text-gray-600' };
};

const extractKPIs = (content) => {
  const numbers = {};
  const patterns = [
    { key: 'marge_nette',          label: 'Marge Nette',      unit: '%', re: /[Mm]arge [Nn]ette[^\d]*?([\d,.]+)\s*%/          },
    { key: 'roe',                  label: 'ROE',               unit: '%', re: /ROE[^\d]*?([\d,.]+)\s*%/                         },
    { key: 'roa',                  label: 'ROA',               unit: '%', re: /ROA[^\d]*?([\d,.]+)\s*%/                         },
    { key: 'autonomie_financiere', label: 'Autonomie Fin.',    unit: '%', re: /autonomie financière[^\d]*?([\d,.]+)\s*%/i       },
    { key: 'ratio_endettement',    label: 'Endettement',       unit: 'x', re: /ratio d.endettement[^\d]*?([\d,.]+)/i           },
    { key: 'liquidite_generale',   label: 'Liquidité Gén.',    unit: 'x', re: /liquidité générale[^\d]*?([\d,.]+)/i            },
    { key: 'liquidite_immediate',  label: 'Liquidité Imm.',    unit: 'x', re: /liquidité immédiate[^\d]*?([\d,.]+)/i           },
  ];
  patterns.forEach(({ key, label, unit, re }) => {
    const m = content.match(re);
    if (m) numbers[key] = { label, value: parseFloat(m[1].replace(',', '.')), unit };
  });
  return numbers;
};

const parseMarkdown = (md) => {
  const lines = md.split('\n');
  const sections = [];
  let current = null;
  lines.forEach(line => {
    if (line.startsWith('# ') && !line.startsWith('## ')) {
      if (current) sections.push(current);
      current = { heading: line.replace(/^# /, '').trim(), body: [], isTitle: true };
    } else if (line.startsWith('## ')) {
      if (current) sections.push(current);
      current = { heading: line.replace(/^## /, '').trim(), body: [], isTitle: false };
    } else if (current) {
      current.body.push(line);
    }
  });
  if (current) sections.push(current);
  return sections;
};

const renderLine = (line, idx) => {
  const parts = line.split(/(\*\*[^*]+\*\*)/g);
  return (
    <span key={idx}>
      {parts.map((p, j) =>
        p.startsWith('**') && p.endsWith('**')
          ? <strong key={j} className="font-semibold text-gray-900">{p.slice(2, -2)}</strong>
          : p
      )}
    </span>
  );
};

const SectionBody = ({ lines, meta }) => {
  const bullets = lines.filter(l => l.trim().startsWith('- '));
  const paras   = lines.filter(l => !l.trim().startsWith('- ') && l.trim() && !l.startsWith('---') && !l.startsWith('*Rapport'));

  return (
    <div className="space-y-4">
      {paras.map((p, i) => (
        <p key={i} className="text-gray-700 leading-relaxed text-[15px]">
          {renderLine(p, i)}
        </p>
      ))}
      {bullets.length > 0 && (
        <ul className="mt-3 space-y-3">
          {bullets.map((b, i) => (
            <li key={i} className={`flex gap-3 items-start p-3 rounded-xl ${meta.light} border`}>
              <div className={`mt-0.5 flex-shrink-0 w-5 h-5 rounded-full ${meta.gradient.replace('from-', 'bg-gradient-to-br from-').split(' ')[0]} flex items-center justify-center bg-gradient-to-br ${meta.gradient}`}>
                <span className="text-white text-[10px] font-bold">{i + 1}</span>
              </div>
              <span className="text-gray-700 leading-relaxed text-[15px]">{b.replace(/^- /, '')}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

/* ─────────────────── KPI pill ─────────────────── */
const KpiPill = ({ label, value, unit, positive, threshold }) => {
  const ok = positive ? value >= threshold : value <= threshold;
  return (
    <div className="flex flex-col items-center bg-white rounded-xl p-4 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
      <span className="text-xs text-gray-400 font-semibold uppercase tracking-widest mb-1">{label}</span>
      <span className="text-2xl font-extrabold text-gray-900">{value.toFixed(2)}<span className="text-sm text-gray-400 ml-1">{unit}</span></span>
      <span className={`mt-2 text-[10px] font-bold uppercase px-2 py-0.5 rounded-full ${ok ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
        {ok ? '✓ Conforme' : '⚠ Alerte'}
      </span>
    </div>
  );
};

/* ─────────────────── PDF export ─────────────────── */
const handlePrint = () => window.print();

/* ─────────────────── main ─────────────────── */
const ReportView = ({ filename, onBack }) => {
  const [content, setContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError]     = useState(null);
  const [copied, setCopied]   = useState(false);
  const printRef = useRef(null);

  const fetchReport = async () => {
    setLoading(true); setError(null);
    try {
      const res  = await fetchWithTimeout(getApiUrl(API_CONFIG.ENDPOINTS.REPORT(filename)));
      const data = await res.json();
      setContent(data.content);
    } catch (err) {
      setError(await analyzeError(err));
    } finally { setLoading(false); }
  };

  useEffect(() => { if (filename) fetchReport(); }, [filename]);

  const copyText = () => {
    navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) return <LoadingState message="Génération de la vue rapport…" />;

  const sections = parseMarkdown(content);
  const titleSec = sections.find(s => s.isTitle);
  const bodySecs = sections.filter(s => !s.isTitle);
  const kpis     = extractKPIs(content);
  const isAgno   = content.includes('Agno');
  const score    = content.match(/Score de fiabilité.*?:\s*([\d.]+)/)?.[1];
  const company  = (titleSec?.heading || filename).replace('Rapport d\'Analyse Financière - ', '').replace('.pdf', '').replace(/_/g, ' ');
  const today    = new Date().toLocaleDateString('fr-FR', { year:'numeric', month:'long', day:'numeric' });

  return (
    <>
      {/* ── Print styles injected inline ── */}
      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

        @media print {
          body * { visibility: hidden !important; }
          #report-print-area, #report-print-area * { visibility: visible !important; }
          #report-print-area { position: fixed; inset: 0; background: white; padding: 32px; font-family: 'Inter', sans-serif; }
          .no-print { display: none !important; }
          .print-section { break-inside: avoid; margin-bottom: 24px; }
        }

        @keyframes slideIn {
          from { opacity: 0; transform: translateY(20px); }
          to   { opacity: 1; transform: translateY(0); }
        }
        .slide-in { animation: slideIn 0.4s ease both; }
        .slide-in-1 { animation-delay: 0.05s; }
        .slide-in-2 { animation-delay: 0.10s; }
        .slide-in-3 { animation-delay: 0.15s; }
        .slide-in-4 { animation-delay: 0.20s; }
        .slide-in-5 { animation-delay: 0.25s; }
        .slide-in-6 { animation-delay: 0.30s; }
      `}</style>

      <div style={{ fontFamily: "'Inter', sans-serif" }} className="min-h-screen bg-gradient-to-br from-gray-50 via-slate-50 to-blue-50/30">

        {/* ══ Sticky top bar ══ */}
        <div className="no-print sticky top-0 z-30 bg-white/90 backdrop-blur-xl border-b border-gray-200/80 shadow-sm">
          <div className="max-w-6xl mx-auto px-6 py-3 flex items-center justify-between">
            <button onClick={onBack}
              className="flex items-center gap-2 text-sm font-semibold text-gray-500 hover:text-indigo-600 transition-colors group">
              <svg className="w-4 h-4 group-hover:-translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M15 19l-7-7 7-7"/>
              </svg>
              Retour aux documents
            </button>

            <div className="flex items-center gap-3">
              {/* Engine badge */}
              <span className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${
                isAgno ? 'bg-purple-50 border-purple-200 text-purple-700' : 'bg-blue-50 border-blue-200 text-blue-700'}`}>
                {isAgno ? '🧠 Agno + RAG FAISS' : '⚡ CrewAI'}
              </span>

              {/* Copy button */}
              <button onClick={copyText}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-gray-600 bg-gray-100 hover:bg-gray-200 rounded-lg transition-colors">
                {copied ? '✓ Copié !' : '📋 Copier'}
              </button>

              {/* PDF button */}
              <button onClick={handlePrint}
                className="flex items-center gap-1.5 px-4 py-1.5 text-xs font-bold text-white bg-gradient-to-r from-red-500 to-rose-600 hover:from-red-600 hover:to-rose-700 rounded-lg shadow-sm hover:shadow-md transition-all">
                <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z" clipRule="evenodd"/>
                </svg>
                Télécharger PDF
              </button>
            </div>
          </div>
        </div>

        {/* ══ Print area ══ */}
        <div id="report-print-area" ref={printRef} className="max-w-6xl mx-auto px-6 py-10 space-y-8">

          {/* ── Hero ── */}
          <div className="slide-in slide-in-1 relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-indigo-950 to-slate-900 text-white shadow-2xl p-10">
            {/* decorative circles */}
            <div className="absolute -top-20 -right-20 w-64 h-64 rounded-full bg-indigo-500/10 blur-3xl pointer-events-none"/>
            <div className="absolute -bottom-16 -left-16 w-48 h-48 rounded-full bg-blue-500/10 blur-2xl pointer-events-none"/>

            <div className="relative flex items-start justify-between flex-wrap gap-6">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-3">
                  <span className="inline-block w-1.5 h-6 rounded-full bg-indigo-400"/>
                  <span className="text-indigo-300 text-xs font-bold uppercase tracking-widest">Rapport d'Analyse · CMF Tunisie</span>
                </div>
                <h1 className="text-3xl font-extrabold leading-tight tracking-tight">{company}</h1>
                <p className="mt-2 text-indigo-300/80 text-sm">Exercice 2025 · Généré le {today}</p>

                {score && (
                  <div className="mt-5 inline-flex items-center gap-2 px-4 py-2 bg-white/10 backdrop-blur rounded-xl border border-white/10">
                    <div className="w-2 h-2 rounded-full bg-green-400 animate-pulse"/>
                    <span className="text-sm font-semibold text-green-300">Fiabilité : {(parseFloat(score) * 100).toFixed(0)}%</span>
                  </div>
                )}
              </div>

              <div className="flex flex-col items-end gap-3">
                <div className="w-16 h-16 rounded-2xl bg-white/10 border border-white/20 flex items-center justify-center text-3xl shadow-inner">
                  🏦
                </div>
                <span className={`text-xs font-bold px-3 py-1 rounded-full border ${
                  isAgno ? 'bg-purple-500/20 border-purple-400/30 text-purple-200' : 'bg-blue-500/20 border-blue-400/30 text-blue-200'}`}>
                  {isAgno ? '🧠 Agno Framework' : '⚡ CrewAI'}
                </span>
              </div>
            </div>
          </div>

          {/* ── KPI strip ── */}
          {Object.keys(kpis).length > 0 && (
            <div className="slide-in slide-in-2">
              <div className="mb-3 flex items-center gap-2">
                <span className="text-xs font-bold text-gray-400 uppercase tracking-widest">Indicateurs Clés de Performance</span>
                <div className="flex-1 h-px bg-gray-200"/>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-7 gap-3">
                {Object.entries(kpis).map(([key, kpi]) => (
                  <KpiPill
                    key={key}
                    label={kpi.label}
                    value={kpi.value}
                    unit={kpi.unit}
                    positive={!['ratio_endettement'].includes(key)}
                    threshold={
                      key === 'autonomie_financiere' ? 30 :
                      key === 'ratio_endettement'    ? 1  :
                      key === 'liquidite_generale'   ? 1  :
                      key === 'liquidite_immediate'  ? 0.2 :
                      key === 'marge_nette'          ? 5  :
                      key === 'roe'                  ? 8  :
                      key === 'roa'                  ? 2  : 0
                    }
                  />
                ))}
              </div>
            </div>
          )}

          {/* ── Sections ── */}
          {error ? (
            <div className="p-8 bg-white rounded-2xl">
              <ErrorDisplay error={error} onRetry={fetchReport} showRetry />
            </div>
          ) : (
            bodySecs.map((section, idx) => {
              const meta = getMeta(section.heading);
              const isRecs = section.heading.toLowerCase().includes('recommandation');

              return (
                <div key={idx} className={`slide-in slide-in-${Math.min(idx + 3, 6)} print-section group`}>
                  <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-lg transition-all duration-300 hover:-translate-y-0.5">
                    {/* Section header */}
                    <div className={`px-6 py-4 bg-gradient-to-r ${meta.gradient} flex items-center gap-3`}>
                      <div className="w-9 h-9 rounded-xl bg-white/20 flex items-center justify-center text-lg shadow-inner">
                        {meta.icon}
                      </div>
                      <h2 className="text-white font-bold text-base tracking-wide">{section.heading}</h2>
                      <div className="ml-auto w-2 h-2 rounded-full bg-white/40"/>
                    </div>

                    {/* Section body */}
                    <div className={`px-7 py-6 ${isRecs ? 'bg-gradient-to-br ' + meta.light.replace('bg-', 'from-').replace('-50', '-50/40 to-white') : ''}`}>
                      <SectionBody lines={section.body} meta={meta} />
                    </div>
                  </div>
                </div>
              );
            })
          )}

          {/* ── Footer watermark ── */}
          <div className="text-center py-6 border-t border-gray-100">
            <p className="text-xs text-gray-300 font-medium tracking-wide">
              Rapport généré automatiquement · <span className="text-gray-400 font-semibold">CMF Tunisie Analysis Platform</span> · {today}
            </p>
          </div>

        </div>
      </div>
    </>
  );
};

export default ReportView;
