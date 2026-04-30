import React, { useState, useEffect } from 'react';
import {
  RadarChart, Radar, PolarGrid, PolarAngleAxis,
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  RadialBarChart, RadialBar,
} from 'recharts';
import { getApiUrl, API_CONFIG } from '../config/api';
import { analyzeError, fetchWithTimeout } from '../utils/errorHandler';
import ErrorDisplay from './ErrorDisplay';
import LoadingState from './LoadingState';

/* ── Design tokens ── */
const T = {
  navy:   '#0f2557',
  blue:   '#1e40af',
  sky:    '#3b82f6',
  gold:   '#d97706',
  amber:  '#f59e0b',
  teal:   '#0d9488',
  green:  '#059669',
  red:    '#dc2626',
  slate:  '#64748b',
  light:  '#f8fafc',
};

const KPIS = [
  { key:'marge_exploitation', label:"Marge d'Exploitation", short:'M.Exp',  unit:'%', pos:true,  seuil:5,   cat:'rent', formula:'EBIT / CA × 100' },
  { key:'marge_nette',        label:'Marge Nette',          short:'M.Net',  unit:'%', pos:true,  seuil:5,   cat:'rent', formula:'Rés. Net / CA × 100' },
  { key:'roe',                label:'ROE',                  short:'ROE',    unit:'%', pos:true,  seuil:8,   cat:'rent', formula:'Rés. Net / CP × 100' },
  { key:'roa',                label:'ROA',                  short:'ROA',    unit:'%', pos:true,  seuil:2,   cat:'rent', formula:'Rés. Net / Actif × 100' },
  { key:'autonomie_financiere',label:'Autonomie Financière',short:'A.Fin',  unit:'%', pos:true,  seuil:30,  cat:'struct', formula:'CP / Total Actif' },
  { key:'ratio_endettement',  label:'Ratio Endettement',    short:'Endet',  unit:'x', pos:false, seuil:1.0, cat:'struct', formula:'Dettes / CP' },
  { key:'frng',               label:'FRNG',                 short:'FRNG',   unit:'DT',pos:true,  seuil:0,   cat:'struct', formula:'Cap. Perm. – Actif NC', big:true },
  { key:'bfr',                label:'BFR',                  short:'BFR',    unit:'DT',pos:true,  seuil:0,   cat:'struct', formula:'AC – PC', big:true },
  { key:'tresorerie_nette',   label:'Trésorerie Nette',     short:'TN',     unit:'DT',pos:true,  seuil:0,   cat:'struct', formula:'FRNG – BFR', big:true },
  { key:'liquidite_generale', label:'Liquidité Générale',   short:'L.Gén',  unit:'x', pos:true,  seuil:1.0, cat:'liq', formula:'(AC+Tréso.) / PC' },
  { key:'liquidite_immediate',label:'Liquidité Immédiate',  short:'L.Imm',  unit:'x', pos:true,  seuil:0.2, cat:'liq', formula:'Tréso. / PC' },
];

const CATS = {
  rent:   { label:'Rentabilité',          icon:'📈', color:'#1e40af', bg:'#eff6ff', tag:'#dbeafe' },
  struct: { label:'Structure Financière', icon:'🏛️', color:'#d97706', bg:'#fffbeb', tag:'#fef3c7' },
  liq:    { label:'Liquidité',            icon:'💧', color:'#0d9488', bg:'#f0fdfa', tag:'#ccfbf1' },
};

const ok = (d, v) => v !== null && v !== undefined && (d.pos ? v >= d.seuil : v <= d.seuil);
const fmtDT = v => new Intl.NumberFormat('fr-FR',{maximumFractionDigits:0}).format(v);
const fmtN  = (v,u) => u==='DT' ? fmtDT(v)+' DT' : v.toLocaleString('fr-FR',{minimumFractionDigits:2,maximumFractionDigits:2})+' '+u;

/* counter */
const Counter = ({ v, unit }) => {
  const [n, setN] = useState(0);
  useEffect(() => {
    if (!v && v!==0) return;
    const abs = Math.abs(v); let cur = 0;
    const step = (abs/800)*16;
    const t = setInterval(()=>{ cur+=step; if(cur>=abs){setN(abs);clearInterval(t);}else setN(cur); },16);
    return ()=>clearInterval(t);
  }, [v]);
  const s = v<0?'-':'';
  return <>{s}{unit==='DT' ? fmtDT(n) : n.toFixed(2)}</>;
};

/* tooltip */
const Tip = ({ active, payload, label }) => {
  if (!active||!payload?.length) return null;
  return (
    <div style={{background:'white',border:'1px solid #e2e8f0',borderRadius:12,padding:'10px 14px',boxShadow:'0 10px 40px rgba(0,0,0,0.1)'}}>
      <p style={{fontWeight:700,color:T.navy,marginBottom:4,fontSize:12}}>{label}</p>
      {payload.map((p,i)=><p key={i} style={{color:p.color||T.slate,fontSize:12,fontWeight:600}}>{p.name}: {typeof p.value==='number'?p.value.toFixed(2):p.value}</p>)}
    </div>
  );
};

/* KPI card — clean professional */
const Card = ({ d, v, idx }) => {
  const [show, setShow] = useState(false);
  useEffect(()=>{ const t=setTimeout(()=>setShow(true),idx*60); return()=>clearTimeout(t); },[idx]);
  const has = v!==null&&v!==undefined;
  const good = has && ok(d,v);
  const cat = CATS[d.cat];
  const pct = has&&!d.big ? Math.min(100, d.pos ? (v/(d.seuil*2))*100 : Math.max(0,(1-v/(d.seuil*2))*100)) : 0;

  return (
    <div style={{
      opacity:show?1:0, transform:show?'translateY(0)':'translateY(16px)',
      transition:'all 0.45s cubic-bezier(0.22,1,0.36,1)',
      background:'white', borderRadius:16,
      border:`1px solid ${has?(good?'#bbf7d0':'#fecaca'):'#e2e8f0'}`,
      boxShadow: has?(good?'0 2px 12px rgba(5,150,105,0.08)':'0 2px 12px rgba(220,38,38,0.06)'):'0 1px 4px rgba(0,0,0,0.04)',
      overflow:'hidden', position:'relative',
    }}>
      {/* accent stripe */}
      <div style={{height:3,background:has?(good?T.green:T.red):'#e2e8f0'}}/>

      <div style={{padding:'14px 16px'}}>
        {/* header */}
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'flex-start',marginBottom:8}}>
          <div>
            <p style={{fontSize:10,fontWeight:700,color:cat.color,textTransform:'uppercase',letterSpacing:'0.08em',marginBottom:2}}>
              {d.label}
            </p>
            <p style={{fontSize:9,color:'#94a3b8',fontFamily:'monospace'}}>{d.formula}</p>
          </div>
          {has && (
            <span style={{
              fontSize:9,fontWeight:800,padding:'2px 8px',borderRadius:999,
              background:good?'#dcfce7':'#fee2e2',
              color:good?T.green:T.red,
              border:`1px solid ${good?'#bbf7d0':'#fecaca'}`,
              whiteSpace:'nowrap',
            }}>
              {good?'✓ Conforme':'⚠ Alerte'}
            </span>
          )}
        </div>

        {/* value */}
        {has ? (
          <div style={{display:'flex',alignItems:'baseline',gap:4,margin:'10px 0 8px'}}>
            <span style={{fontSize:d.big?18:26,fontWeight:900,color:T.navy,letterSpacing:'-0.02em',fontVariantNumeric:'tabular-nums'}}>
              <Counter v={v} unit={d.unit}/>
            </span>
            <span style={{fontSize:11,color:T.slate,fontWeight:600}}>{d.unit}</span>
          </div>
        ) : (
          <div style={{margin:'10px 0 8px'}}>
            <span style={{fontSize:22,fontWeight:700,color:'#cbd5e1'}}>N/A</span>
            <p style={{fontSize:9,color:'#cbd5e1',marginTop:2}}>Donnée manquante</p>
          </div>
        )}

        {/* progress + seuil */}
        <div style={{display:'flex',alignItems:'center',justifyContent:'space-between',gap:8}}>
          <span style={{fontSize:9,color:'#94a3b8',fontWeight:600,whiteSpace:'nowrap'}}>
            Seuil {d.pos?'>':'<'} {d.seuil}{d.unit!=='DT'?' '+d.unit:''}
          </span>
          {has && !d.big && (
            <div style={{flex:1,height:4,background:'#f1f5f9',borderRadius:99,overflow:'hidden'}}>
              <div style={{height:'100%',borderRadius:99,width:`${pct}%`,background:good?T.green:T.red,transition:'width 1s ease'}}/>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

/* main */
const KPIDashboard = ({ filename, onBack }) => {
  const [data, setData]     = useState(null);
  const [loading, setLoad]  = useState(true);
  const [error, setError]   = useState(null);

  const fetch_ = async () => {
    setLoad(true); setError(null);
    try { setData(await (await fetchWithTimeout(getApiUrl(API_CONFIG.ENDPOINTS.KPIS(filename)))).json()); }
    catch(e) { setError(await analyzeError(e)); }
    finally { setLoad(false); }
  };
  useEffect(()=>{ if(filename) fetch_(); },[filename]);

  if (loading) return <LoadingState message="Calcul des 11 KPI SCE Tunisie…"/>;
  if (error)   return <div className="p-10"><button onClick={onBack} className="text-blue-600 font-bold mb-4 block">← Retour</button><ErrorDisplay error={error} onRetry={fetch_} showRetry/></div>;

  /* chart data */
  const ratios = KPIS.filter(d=>!d.big && data[d.key]!=null);
  const bigs   = KPIS.filter(d=> d.big && data[d.key]!=null);

  const radarD = ratios.map(d=>({
    subject:d.short,
    value:Math.round(d.pos ? Math.min(100,(data[d.key]/(d.seuil*2))*100) : Math.min(100,Math.max(0,(1-data[d.key]/(d.seuil*2))*100))),
    fullMark:100,
  }));

  let okN=0,koN=0,naN_=0;
  KPIS.forEach(d=>{ const v=data[d.key]; if(v==null)naN_++; else if(ok(d,v))okN++; else koN++; });
  const pieD = [{name:'Conformes',value:okN,color:'#059669'},{name:'Alertes',value:koN,color:'#dc2626'},{name:'N/A',value:naN_,color:'#e2e8f0'}].filter(x=>x.value>0);

  const validAll = KPIS.filter(d=>data[d.key]!=null);
  const score = validAll.length ? Math.round((okN/validAll.length)*100) : 0;
  const scoreCol = score>=70?T.green:score>=40?T.gold:T.red;

  const catScores = Object.entries(CATS).map(([k,m])=>{
    const items=KPIS.filter(d=>d.cat===k); const valid=items.filter(d=>data[d.key]!=null);
    return { name:m.label, value:valid.length?Math.round((valid.filter(d=>ok(d,data[d.key])).length/valid.length)*100):0, fill:m.color };
  });

  const barD = ratios.map(d=>({ name:d.short, Valeur:+data[d.key].toFixed(2), Seuil:d.seuil, ok:ok(d,data[d.key]) }));

  let idx=0;

  return (
    <div style={{fontFamily:"'Inter',sans-serif",background:'#f8fafc',minHeight:'100vh',padding:'0 0 40px'}}>
      <style>{`@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');`}</style>

      {/* ── header ── */}
      <div style={{background:'white',borderBottom:'1px solid #e2e8f0',padding:'16px 28px',display:'flex',alignItems:'center',justifyContent:'space-between',flexWrap:'wrap',gap:12}}>
        <div>
          <h2 style={{fontSize:20,fontWeight:800,color:T.navy,margin:0}}>Tableau de Bord Financier</h2>
          <p style={{fontSize:12,color:T.slate,margin:'2px 0 0'}}>{filename} · Unité : <strong style={{color:T.blue}}>{data.unit||'DT'}</strong> · 11 KPI SCE Tunisie</p>
        </div>
        <button onClick={onBack} style={{padding:'8px 18px',background:T.light,border:'1px solid #e2e8f0',borderRadius:10,fontSize:13,fontWeight:600,color:T.slate,cursor:'pointer'}}>
          ← Retour
        </button>
      </div>

      <div style={{maxWidth:1280,margin:'0 auto',padding:'28px 24px',display:'flex',flexDirection:'column',gap:24}}>

        {/* ── row 1 : score + pie + radial ── */}
        <div style={{display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:20}}>

          {/* score */}
          <div style={{background:`linear-gradient(145deg,${T.navy},#1e3a8a)`,borderRadius:20,padding:28,color:'white',display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',textAlign:'center'}}>
            <p style={{fontSize:10,fontWeight:700,letterSpacing:'0.12em',textTransform:'uppercase',color:'#93c5fd',marginBottom:20}}>Score Global SCE</p>
            <div style={{position:'relative',width:130,height:130}}>
              <svg viewBox="0 0 100 100" style={{width:'100%',height:'100%',transform:'rotate(-90deg)'}}>
                <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(255,255,255,0.1)" strokeWidth="8"/>
                <circle cx="50" cy="50" r="40" fill="none" stroke={scoreCol} strokeWidth="8"
                  strokeDasharray={`${score*2.51} 251`} strokeLinecap="round" style={{transition:'stroke-dasharray 1.2s ease'}}/>
              </svg>
              <div style={{position:'absolute',inset:0,display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center'}}>
                <span style={{fontSize:32,fontWeight:900,color:'white',lineHeight:1}}>{score}</span>
                <span style={{fontSize:11,color:'rgba(255,255,255,0.5)'}}>/ 100</span>
              </div>
            </div>
            <p style={{marginTop:16,fontSize:13,fontWeight:700,color:scoreCol}}>{score>=70?'✓ Bonne Santé':score>=40?'⚠ Vigilance':'✗ Critique'}</p>
            <p style={{fontSize:11,color:'rgba(255,255,255,0.4)',marginTop:4}}>{okN}/{validAll.length} conformes · {naN_} N/A</p>
            {data.extraction_confidence && (
              <div style={{marginTop:16,width:'100%',background:'rgba(255,255,255,0.08)',borderRadius:10,padding:12}}>
                <p style={{fontSize:10,color:'rgba(255,255,255,0.4)',marginBottom:6}}>Confiance extraction</p>
                <div style={{height:4,background:'rgba(255,255,255,0.1)',borderRadius:99}}>
                  <div style={{height:'100%',width:`${data.extraction_confidence*100}%`,background:'#34d399',borderRadius:99,transition:'width 1s ease'}}/>
                </div>
                <p style={{fontSize:11,color:'#34d399',fontWeight:700,marginTop:4}}>{(data.extraction_confidence*100).toFixed(0)}%</p>
              </div>
            )}
          </div>

          {/* pie */}
          <div style={{background:'white',borderRadius:20,border:'1px solid #e2e8f0',padding:'20px 20px 16px',boxShadow:'0 2px 12px rgba(0,0,0,0.04)'}}>
            <p style={{fontSize:12,fontWeight:700,color:T.navy,marginBottom:4}}>🎯 Répartition Conformité</p>
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={pieD} cx="50%" cy="50%" innerRadius={50} outerRadius={78} paddingAngle={3} dataKey="value">
                  {pieD.map((e,i)=><Cell key={i} fill={e.color}/>)}
                </Pie>
                <Tooltip content={<Tip/>}/>
              </PieChart>
            </ResponsiveContainer>
            <div style={{display:'flex',justifyContent:'center',gap:16,marginTop:4}}>
              {pieD.map((p,i)=>(
                <div key={i} style={{display:'flex',alignItems:'center',gap:6,fontSize:11,fontWeight:600,color:T.slate}}>
                  <div style={{width:10,height:10,borderRadius:99,background:p.color}}/>
                  {p.name} ({p.value})
                </div>
              ))}
            </div>
          </div>

          {/* radial */}
          <div style={{background:'white',borderRadius:20,border:'1px solid #e2e8f0',padding:'20px 20px 16px',boxShadow:'0 2px 12px rgba(0,0,0,0.04)'}}>
            <p style={{fontSize:12,fontWeight:700,color:T.navy,marginBottom:4}}>📊 Score par Catégorie</p>
            <ResponsiveContainer width="100%" height={175}>
              <RadialBarChart cx="50%" cy="50%" innerRadius={25} outerRadius={80} data={catScores} startAngle={90} endAngle={-270}>
                <RadialBar minAngle={10} dataKey="value" cornerRadius={6} label={{position:'insideStart',fill:'white',fontSize:10,fontWeight:'bold'}}/>
                <Tooltip content={<Tip/>} formatter={v=>[v+'%','Score']}/>
              </RadialBarChart>
            </ResponsiveContainer>
            <div style={{display:'flex',flexDirection:'column',gap:6,marginTop:4}}>
              {catScores.map((c,i)=>(
                <div key={i} style={{display:'flex',alignItems:'center',gap:8}}>
                  <div style={{width:8,height:8,borderRadius:99,background:c.fill,flexShrink:0}}/>
                  <span style={{fontSize:11,color:T.slate,flex:1}}>{c.name}</span>
                  <span style={{fontSize:11,fontWeight:700,color:c.fill}}>{c.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── row 2: bar chart ── */}
        {barD.length>0 && (
          <div style={{background:'white',borderRadius:20,border:'1px solid #e2e8f0',padding:24,boxShadow:'0 2px 12px rgba(0,0,0,0.04)'}}>
            <p style={{fontSize:13,fontWeight:700,color:T.navy,marginBottom:4}}>📉 Valeurs réelles vs Seuils SCE</p>
            <p style={{fontSize:11,color:T.slate,marginBottom:20}}>Ratios et pourcentages uniquement</p>
            <ResponsiveContainer width="100%" height={230}>
              <BarChart data={barD} margin={{top:5,right:20,left:0,bottom:5}} barGap={6}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false}/>
                <XAxis dataKey="name" tick={{fontSize:11,fontWeight:600,fill:T.slate}} axisLine={false} tickLine={false}/>
                <YAxis tick={{fontSize:10,fill:'#94a3b8'}} axisLine={false} tickLine={false}/>
                <Tooltip content={<Tip/>}/>
                <Bar dataKey="Valeur" radius={[6,6,0,0]} maxBarSize={40}>
                  {barD.map((e,i)=><Cell key={i} fill={e.ok?T.green:T.red}/>)}
                </Bar>
                <Bar dataKey="Seuil" fill="#dde1e7" radius={[6,6,0,0]} maxBarSize={40}/>
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* ── row 3: radar ── */}
        {radarD.length>=3 && (
          <div style={{background:'white',borderRadius:20,border:'1px solid #e2e8f0',padding:24,boxShadow:'0 2px 12px rgba(0,0,0,0.04)'}}>
            <p style={{fontSize:13,fontWeight:700,color:T.navy,marginBottom:20}}>🕸️ Profil de Performance Normalisé</p>
            <ResponsiveContainer width="100%" height={280}>
              <RadarChart data={radarD}>
                <PolarGrid stroke="#e2e8f0"/>
                <PolarAngleAxis dataKey="subject" tick={{fontSize:11,fontWeight:600,fill:T.slate}}/>
                <Radar name="Score" dataKey="value" stroke={T.blue} fill={T.blue} fillOpacity={0.15} strokeWidth={2}/>
                <Tooltip content={<Tip/>} formatter={v=>[v+'/100','Score']}/>
              </RadarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* ── row 4: balance ── */}
        {bigs.length>0 && (
          <div style={{background:'white',borderRadius:20,border:'1px solid #e2e8f0',padding:24,boxShadow:'0 2px 12px rgba(0,0,0,0.04)'}}>
            <p style={{fontSize:13,fontWeight:700,color:T.navy,marginBottom:20}}>⚖️ Équilibre Financier (DT)</p>
            <div style={{display:'flex',flexDirection:'column',gap:14}}>
              {bigs.map(d=>{
                const v = data[d.key]; const max = Math.max(...bigs.map(b=>Math.abs(data[b.key]||0)));
                const pct = max ? Math.min(100,(Math.abs(v)/max)*100) : 0;
                return (
                  <div key={d.key} style={{display:'flex',alignItems:'center',gap:16}}>
                    <span style={{width:130,fontSize:12,fontWeight:600,color:T.slate,flexShrink:0}}>{d.label}</span>
                    <div style={{flex:1,height:8,background:'#f1f5f9',borderRadius:99,overflow:'hidden'}}>
                      <div style={{height:'100%',width:`${pct}%`,background:v>=0?T.teal:T.red,borderRadius:99,transition:'width 1s ease'}}/>
                    </div>
                    <span style={{fontSize:12,fontWeight:700,color:v>=0?T.teal:T.red,fontVariantNumeric:'tabular-nums',width:140,textAlign:'right',flexShrink:0}}>
                      {fmtDT(v)} DT
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* ── KPI cards per category ── */}
        {Object.entries(CATS).map(([catKey, cat])=>{
          const items = KPIS.filter(d=>d.cat===catKey);
          return (
            <div key={catKey}>
              <div style={{display:'flex',alignItems:'center',gap:12,marginBottom:14}}>
                <div style={{width:36,height:36,borderRadius:12,background:cat.bg,border:`1.5px solid ${cat.tag}`,display:'flex',alignItems:'center',justifyContent:'center',fontSize:16}}>
                  {cat.icon}
                </div>
                <h3 style={{fontSize:14,fontWeight:800,color:cat.color,margin:0}}>{cat.label}</h3>
                <div style={{flex:1,height:1,background:`linear-gradient(90deg,${cat.tag},transparent)`}}/>
              </div>
              <div style={{display:'grid',gridTemplateColumns:`repeat(${Math.min(items.length,4)},1fr)`,gap:14}}>
                {items.map(d=><Card key={d.key} d={d} v={data[d.key]??null} idx={idx++}/>)}
              </div>
            </div>
          );
        })}

        {/* missing data */}
        {data.missing_data?.length>0 && (
          <div style={{background:'#fff7ed',border:'1px solid #fed7aa',borderRadius:16,padding:20}}>
            <p style={{fontSize:13,fontWeight:700,color:'#c2410c',marginBottom:10}}>⚠️ Données Manquantes</p>
            <div style={{display:'flex',flexWrap:'wrap',gap:8,marginBottom:data.processing_notes?.length?12:0}}>
              {data.missing_data.map((m,i)=>(
                <span key={i} style={{padding:'4px 12px',background:'#ffedd5',color:'#c2410c',fontSize:11,fontWeight:700,borderRadius:99,border:'1px solid #fdba74'}}>{m}</span>
              ))}
            </div>
            {data.processing_notes?.map((n,i)=>(
              <p key={i} style={{fontSize:11,color:'#9a3412',display:'flex',gap:6,marginTop:6}}>
                <span>•</span>{n}
              </p>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default KPIDashboard;
