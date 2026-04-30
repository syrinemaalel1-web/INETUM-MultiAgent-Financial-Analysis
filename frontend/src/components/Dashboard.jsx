import React from 'react';
import ErrorDisplay from './ErrorDisplay';

const StatCard = ({ title, value, color, icon }) => (
  <div className="bg-white p-6 rounded-2xl shadow-sm border border-gray-100">
    <div className="flex justify-between items-start mb-4">
      <div className={`p-3 rounded-xl bg-${color}-50 text-${color}-600`}>
        {icon}
      </div>
    </div>
    <h3 className="text-gray-500 text-sm font-medium">{title}</h3>
    <p className="text-3xl font-bold mt-1">{value}</p>
  </div>
);

const Dashboard = ({ stats, statsError }) => {
  return (
    <div className="space-y-8">
      {statsError && (
        <ErrorDisplay 
          error={statsError} 
          size="compact"
          showRetry={false}
          className="mb-6"
        />
      )}
      
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <StatCard 
          title="PDFs Téléchargés" 
          value={stats.raw_pdfs} 
          color="blue"
          icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>}
        />
        <StatCard 
          title="Documents Extraits" 
          value={stats.processed_mds} 
          color="purple"
          icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>}
        />
        <StatCard 
          title="Analyses IA Terminées" 
          value={stats.reports_generated} 
          color="green"
          icon={<svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"></path></svg>}
        />
      </div>

      <div className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100">
        <h3 className="text-xl font-bold mb-6">Pipeline CMF - Progression</h3>
        <div className="flex items-center justify-between relative">
            <div className="absolute left-0 right-0 h-1 bg-gray-100 top-1/2 -translate-y-1/2 z-0"></div>
            
            {[
                { label: 'Scraping', active: stats.is_scraping, done: stats.raw_pdfs > 0 },
                { label: 'Extraction', active: false, done: stats.processed_mds > 0 },
                { label: 'Analyse IA', active: false, done: stats.reports_generated > 0 }
            ].map((step, i) => (
                <div key={i} className="relative z-10 flex flex-col items-center">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        step.active ? 'bg-blue-600 text-white animate-pulse' : 
                        step.done ? 'bg-green-500 text-white' : 'bg-gray-200 text-gray-400'
                    }`}>
                        {step.done ? '✓' : i + 1}
                    </div>
                    <span className="text-xs font-semibold mt-2 uppercase text-gray-500 tracking-wider">{step.label}</span>
                </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
