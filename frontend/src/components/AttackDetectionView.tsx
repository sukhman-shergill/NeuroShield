import React, { useState } from 'react';
import { SecurityAlert } from '../types';

interface AttackDetectionViewProps {
  alerts: SecurityAlert[];
  onIsolateHost: (ip: string) => void;
  onReviewHost: (ip: string) => void;
  onIgnoreHost: (ip: string) => void;
}

export default function AttackDetectionView({ alerts, onIsolateHost, onReviewHost, onIgnoreHost }: AttackDetectionViewProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState<string>('ALL');
  const [notification, setNotification] = useState<string | null>(null);

  // Filter logic
  const filteredAlerts = alerts.filter(alert => {
    const matchesSearch = alert.sourceIp.includes(searchTerm) || 
      (alert.attackType && alert.attackType.toLowerCase().includes(searchTerm.toLowerCase())) ||
      ((alert as any).predictedAttack && (alert as any).predictedAttack.toLowerCase().includes(searchTerm.toLowerCase()));

    const matchesSeverity = severityFilter === 'ALL' || alert.severity.toUpperCase() === severityFilter;

    return matchesSearch && matchesSeverity;
  });

  const triggerNotification = (msg: string) => {
    setNotification(msg);
    setTimeout(() => {
      setNotification(null);
    }, 4000);
  };

  const isolateAction = (ip: string) => {
    onIsolateHost(ip);
    triggerNotification(`Host IP ${ip} has been successfully isolated from core gateways.`);
  };

  const reviewAction = (ip: string) => {
    onReviewHost(ip);
    triggerNotification(`Incident for ${ip} marked for review by secondary tier-3 SOC team.`);
  };

  const ignoreAction = (ip: string) => {
    onIgnoreHost(ip);
    triggerNotification(`Incident vector for ${ip} safely disregarded and logged.`);
  };

  return (
    <div id="attack-detection-root" className="space-y-6 font-sans">
      {/* Dynamic Notifications Banner */}
      {notification && (
        <div className="bg-[#12151f] border-l-4 border-indigo-500 text-slate-200 px-4 py-3 rounded-r-lg shadow-xl flex items-center justify-between gap-3 animate-bounce" id="detection-toast">
          <div className="flex items-center gap-2">
            <span className="material-symbols-outlined text-indigo-400 fill-icon">info</span>
            <span className="text-xs font-medium font-mono">{notification}</span>
          </div>
          <button onClick={() => setNotification(null)} className="material-symbols-outlined text-slate-400 hover:text-slate-200 text-sm">close</button>
        </div>
      )}

      {/* Header and Filter Toolbar */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#1e2230] pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span className="material-symbols-outlined text-rose-500">dangerous</span>
            Threat Detection Queue
          </h2>
          <p className="text-xs text-slate-400">Review neural IDS incidents, configure isolate policies, and export vector log packages</p>
        </div>

        {/* Action button */}
        <div className="flex items-center gap-2">
          <button 
            id="export-csv-btn"
            onClick={() => triggerNotification('Exporting complete incident queue to secure CSV format...')}
            className="bg-[#1b1f2e] hover:bg-[#252b40] text-slate-300 font-semibold px-4 py-2 rounded-lg text-xs tracking-wide border border-slate-700/50 flex items-center gap-2 transition-all active:scale-95"
          >
            <span className="material-symbols-outlined text-sm">download</span>
            EXPORT QUEUE
          </button>
        </div>
      </div>

      {/* Filter Options */}
      <div className="glass-panel p-4 rounded-xl flex flex-col md:flex-row gap-4 items-center justify-between" id="attack-detection-filters">
        {/* Search Input */}
        <div className="relative w-full md:w-80">
          <span className="material-symbols-outlined absolute left-3 top-2.5 text-slate-500 text-sm">search</span>
          <input
            id="attack-search-input"
            type="text"
            placeholder="Search by IP address or attack vector..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950/60 border border-slate-800 text-xs text-slate-200 pl-9 pr-4 py-2 rounded-lg focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>

        {/* Severity toggles */}
        <div className="flex items-center gap-1.5 self-start md:self-auto" id="attack-severity-filters">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mr-2">Severity Level:</span>
          {['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'].map(level => (
            <button
              key={level}
              id={`severity-filter-${level}`}
              onClick={() => setSeverityFilter(level)}
              className={`px-3 py-1.5 rounded-lg text-[10px] font-mono font-bold uppercase transition-all duration-200 ${
                severityFilter === level
                  ? level === 'CRITICAL' ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30' :
                    level === 'HIGH' ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30' :
                    level === 'MEDIUM' ? 'bg-blue-500/15 text-blue-400 border border-blue-500/30' :
                    level === 'LOW' ? 'bg-slate-500/25 text-slate-300 border border-slate-500/30' :
                    'bg-indigo-500/15 text-indigo-400 border border-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30 border border-transparent'
              }`}
            >
              {level}
            </button>
          ))}
        </div>
      </div>

      {/* Main Table Queue */}
      <div className="glass-panel p-5 rounded-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left" id="threat-queue-table">
            <thead>
              <tr className="border-b border-[#1e2230] text-slate-400 text-[10px] font-mono uppercase tracking-wider">
                <th className="pb-3">Timestamp</th>
                <th className="pb-3">Incident Identity</th>
                <th className="pb-3">Source Host IP</th>
                <th className="pb-3 text-center">Threat Severity</th>
                <th className="pb-3 text-right">Confidence Level</th>
                <th className="pb-3 text-center">Protocol Interface</th>
                <th className="pb-3 text-center">Orchestration Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#181a25]/40 text-xs text-slate-300">
              {filteredAlerts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="py-10 text-center text-slate-600 italic">
                    // NO DETECTED THREATS MATCHING CRITERIA
                  </td>
                </tr>
              ) : (
                filteredAlerts.map((alert, idx) => {
                  const isCritical = alert.severity === 'Critical';
                  const isHigh = alert.severity === 'High';
                  const score = alert.confScore || (alert as any).confidenceScore || 75.2;

                  return (
                    <tr key={idx} className="hover:bg-slate-800/10 transition-colors">
                      <td className="py-3.5 font-mono text-slate-400 text-[11px]">{alert.timestamp}</td>
                      <td className="py-3.5 font-medium">
                        <span className="text-slate-100 font-semibold block">{alert.attackType || (alert as any).predictedAttack}</span>
                        <span className="text-[10px] text-slate-500 font-mono">IDS-VECTOR-{idx + 104}</span>
                      </td>
                      <td className="py-3.5 font-mono text-slate-200">{alert.sourceIp}</td>
                      <td className="py-3.5 text-center">
                        <span className={`px-2.5 py-1 rounded-full text-[9px] font-mono font-bold uppercase ${
                          isCritical ? 'bg-rose-500/15 text-rose-400 ring-1 ring-rose-500/20' :
                          isHigh ? 'bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/20' :
                          alert.severity === 'Medium' ? 'bg-blue-500/15 text-blue-400 ring-1 ring-blue-500/20' :
                          'bg-slate-500/15 text-slate-400 ring-1 ring-slate-500/20'
                        }`}>
                          {alert.severity}
                        </span>
                      </td>
                      <td className="py-3.5 text-right font-mono">
                        <div className="flex flex-col items-end gap-1">
                          <span className="font-bold text-slate-200">{score}%</span>
                          <div className="w-16 bg-slate-900 h-1 rounded-full overflow-hidden border border-slate-800">
                            <div className={`h-full rounded-full ${
                              score > 90 ? 'bg-rose-500' : score > 70 ? 'bg-amber-500' : 'bg-indigo-500'
                            }`} style={{ width: `${score}%` }}></div>
                          </div>
                        </div>
                      </td>
                      <td className="py-3.5 text-center font-mono text-slate-400 text-[11px]">{alert.protocol || (alert as any).protocolPort}</td>
                      <td className="py-3.5">
                        <div className="flex items-center justify-center gap-2">
                          {alert.actionTaken === 'ISOLATE' ? (
                            <span className="text-[10px] font-mono text-rose-400 bg-rose-500/10 px-3 py-1 rounded border border-rose-500/20">HOST ISOLATED</span>
                          ) : alert.actionTaken === 'REVIEW' ? (
                            <span className="text-[10px] font-mono text-amber-400 bg-amber-500/10 px-3 py-1 rounded border border-amber-500/20">UNDER REVIEW</span>
                          ) : (
                            <>
                              <button
                                id={`isolate-threat-btn-${idx}`}
                                onClick={() => isolateAction(alert.sourceIp)}
                                className="bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 px-2.5 py-1 rounded text-[10px] font-mono border border-rose-500/25 transition-all active:scale-95"
                              >
                                ISOLATE
                              </button>
                              <button
                                id={`review-threat-btn-${idx}`}
                                onClick={() => reviewAction(alert.sourceIp)}
                                className="bg-slate-800 text-slate-300 hover:bg-slate-700 px-2.5 py-1 rounded text-[10px] font-mono border border-slate-700 transition-all active:scale-95"
                              >
                                REVIEW
                              </button>
                              <button
                                id={`ignore-threat-btn-${idx}`}
                                onClick={() => ignoreAction(alert.sourceIp)}
                                className="text-slate-500 hover:text-slate-300 px-1 py-1 material-symbols-outlined text-sm transition-all"
                                title="Disregard Incident"
                              >
                                delete
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Aggregate metrics for attack protection */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4" id="attack-aggregate-metrics">
        <div className="bg-[#12141f]/70 border border-[#1e2230] p-4 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-indigo-500/10 text-indigo-400 rounded-lg">
            <span className="material-symbols-outlined text-2xl">shield_with_heart</span>
          </div>
          <div>
            <p className="text-[10px] text-slate-500 font-mono tracking-wider uppercase">Active Blocking Rate</p>
            <p className="text-lg font-black text-slate-100 font-mono">99.82%</p>
          </div>
        </div>
        <div className="bg-[#12141f]/70 border border-[#1e2230] p-4 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-rose-500/10 text-rose-400 rounded-lg">
            <span className="material-symbols-outlined text-2xl">timer_10_alt_1</span>
          </div>
          <div>
            <p className="text-[10px] text-slate-500 font-mono tracking-wider uppercase">Average Mitigate Speed</p>
            <p className="text-lg font-black text-slate-100 font-mono">14.8 seconds</p>
          </div>
        </div>
        <div className="bg-[#12141f]/70 border border-[#1e2230] p-4 rounded-xl flex items-center gap-4">
          <div className="p-3 bg-amber-500/10 text-amber-400 rounded-lg">
            <span className="material-symbols-outlined text-2xl">grid_view</span>
          </div>
          <div>
            <p className="text-[10px] text-slate-500 font-mono tracking-wider uppercase">IP Blocklist Pool</p>
            <p className="text-lg font-black text-slate-100 font-mono">1,420 Subnets</p>
          </div>
        </div>
      </div>
    </div>
  );
}
