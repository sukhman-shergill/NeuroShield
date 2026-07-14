import React, { useState, useEffect } from 'react';
import { SystemLog } from '../types';

export default function SystemLogsView() {
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [severityFilter, setSeverityFilter] = useState('ALL');
  const [moduleFilter, setModuleFilter] = useState('ALL');
  const [selectedLog, setSelectedLog] = useState<SystemLog | null>(null);
  const [copySuccess, setCopySuccess] = useState(false);

  // Fetch logs from the backend
  useEffect(() => {
    const fetchLogs = () => {
      fetch('/api/logs')
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data)) {
            setLogs(data);
          }
        })
        .catch(err => console.error('Error fetching logs:', err));
    };

    fetchLogs();
    const interval = setInterval(fetchLogs, 3000);
    return () => clearInterval(interval);
  }, []);


  // Filter logic
  const filteredLogs = logs.filter(log => {
    const matchesSearch = log.message.toLowerCase().includes(searchTerm.toLowerCase()) || 
      log.module.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesSeverity = severityFilter === 'ALL' || log.severity === severityFilter;
    const matchesModule = moduleFilter === 'ALL' || log.module === moduleFilter;

    return matchesSearch && matchesSeverity && matchesModule;
  });

  const handleCopyJSON = (jsonStr: string) => {
    navigator.clipboard.writeText(jsonStr);
    setCopySuccess(true);
    setTimeout(() => setCopySuccess(false), 2000);
  };

  const formatLogToJSON = (log: SystemLog) => {
    return JSON.stringify({
      timestamp: log.timestamp,
      severity: log.severity,
      module: log.module,
      status: log.status,
      message: log.message,
    }, null, 2);
  };

  return (
    <div id="system-logs-root" className="space-y-6 font-sans">
      {/* Header and Counters */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-[#1e2230] pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span className="material-symbols-outlined text-indigo-400">terminal</span>
            System Logs Command Center
          </h2>
          <p className="text-xs text-slate-400">View system logs, monitor performance, and debug model warnings</p>
        </div>
        
        {/* Quick Uptime counters */}
        <div className="flex items-center gap-4 text-xs font-mono">
          <div className="text-right">
            <span className="text-slate-500 block text-[9px] uppercase">Error Rate</span>
            <span className="text-rose-400 font-bold font-mono">0.02%</span>
          </div>
          <div className="text-right">
            <span className="text-slate-500 block text-[9px] uppercase">Operational Uptime</span>
            <span className="text-emerald-400 font-bold font-mono">99.998%</span>
          </div>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="glass-panel p-4 rounded-xl flex flex-col md:flex-row gap-4 items-center justify-between" id="system-logs-filters">
        {/* Search */}
        <div className="relative w-full md:w-80">
          <span className="material-symbols-outlined absolute left-3 top-2.5 text-slate-500 text-sm">search</span>
          <input
            id="log-search-input"
            type="text"
            placeholder="Search kernel traces or error payloads..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full bg-slate-950/60 border border-slate-800 text-xs text-slate-200 pl-9 pr-4 py-2 rounded-lg focus:outline-none focus:border-indigo-500 font-mono"
          />
        </div>

        {/* Level Filters */}
        <div className="flex flex-wrap items-center gap-2 self-start md:self-auto" id="log-severity-selectors">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest mr-2">Level:</span>
          {['ALL', 'CRIT', 'ERROR', 'WARN', 'INFO'].map(lvl => (
            <button
              key={lvl}
              id={`log-severity-${lvl}`}
              onClick={() => setSeverityFilter(lvl)}
              className={`px-2.5 py-1.5 rounded text-[10px] font-mono font-bold uppercase transition-all duration-150 ${
                severityFilter === lvl 
                  ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/25' 
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30 border border-transparent'
              }`}
            >
              {lvl}
            </button>
          ))}
        </div>

        {/* Module Filter dropdown */}
        <div className="space-y-1 w-full md:w-44 self-start md:self-auto">
          <select
            id="log-module-select"
            value={moduleFilter}
            onChange={(e) => setModuleFilter(e.target.value)}
            className="w-full bg-slate-950/60 border border-slate-800 text-xs text-slate-300 px-3 py-2 rounded-lg focus:outline-none focus:border-indigo-500 font-mono"
          >
            <option value="ALL">ALL MODULES</option>
            <option value="Kernel">KERNEL MODULE</option>
            <option value="AI Engine">AI ENGINE MODULE</option>
            <option value="Network">NETWORK MODULE</option>
            <option value="Auth">AUTH MODULE</option>
            <option value="System">SYSTEM MODULE</option>
          </select>
        </div>
      </div>

      {/* Main logs list */}
      <div className="glass-panel p-5 rounded-xl">
        <div className="overflow-x-auto">
          <table className="w-full text-left" id="logs-history-table">
            <thead>
              <tr className="border-b border-[#1e2230] text-slate-400 text-[10px] font-mono uppercase tracking-wider">
                <th className="pb-3">Timestamp (UTC)</th>
                <th className="pb-3 text-center">Severity</th>
                <th className="pb-3">Kernel Module</th>
                <th className="pb-3">Trace Message</th>
                <th className="pb-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#181a25]/40 text-xs text-slate-300 font-mono">
              {filteredLogs.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-10 text-center text-slate-600 italic">
                    // NO DIAGNOSTIC TRACES MATCHING SEARCH CRITERIA
                  </td>
                </tr>
              ) : (
                filteredLogs.map((log, idx) => {
                  const isCrit = log.severity === 'CRIT' || log.severity === 'ERROR';
                  return (
                    <tr 
                      key={idx} 
                      className="hover:bg-slate-800/10 cursor-pointer transition-all"
                      onClick={() => setSelectedLog(log)}
                    >
                      <td className="py-3 text-[11px] text-slate-400">{log.timestamp}</td>
                      <td className="py-3 text-center">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                          isCrit ? 'bg-rose-500/15 text-rose-400 border border-rose-500/20' :
                          log.severity === 'WARN' ? 'bg-amber-500/15 text-amber-400 border border-amber-500/20' :
                          'bg-indigo-500/15 text-indigo-400 border border-indigo-500/20'
                        }`}>
                          {log.severity}
                        </span>
                      </td>
                      <td className="py-3 text-indigo-400 font-semibold">[{log.module}]</td>
                      <td className={`py-3 truncate max-w-sm md:max-w-md ${isCrit ? 'text-rose-300' : 'text-slate-200'}`}>
                        {log.message}
                      </td>
                      <td className="py-3 text-right">
                        <button
                          id={`inspect-log-btn-${idx}`}
                          onClick={(e) => {
                            e.stopPropagation();
                            setSelectedLog(log);
                          }}
                          className="text-indigo-400 hover:text-indigo-300 text-[10px] font-mono px-2 py-1 rounded hover:bg-indigo-500/10 border border-transparent hover:border-indigo-500/20 transition-all active:scale-95"
                        >
                          INSPECT JSON
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* JSON Debug modal overlay */}
      {selectedLog && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" id="log-inspector-modal">
          <div className="glass-panel w-full max-w-xl p-6 rounded-xl space-y-4 shadow-2xl relative border border-slate-700/50">
            <button 
              onClick={() => setSelectedLog(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 material-symbols-outlined"
              id="close-log-modal-btn"
            >
              close
            </button>
            <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
              <span className="material-symbols-outlined text-indigo-400">terminal</span>
              <h4 className="text-xs font-bold text-slate-200 tracking-wider uppercase">Structured trace Inspector</h4>
            </div>

            <div className="space-y-1.5">
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest block">Formatted JSON Trace</span>
              <pre className="bg-slate-950 p-4 rounded-lg text-[11px] font-mono text-emerald-400 border border-slate-800 leading-relaxed max-h-[300px] overflow-y-auto select-all">
                {formatLogToJSON(selectedLog)}
              </pre>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                id="copy-json-btn"
                onClick={() => handleCopyJSON(formatLogToJSON(selectedLog))}
                className="flex-1 bg-indigo-600 hover:bg-indigo-500 text-slate-100 py-2.5 rounded text-xs font-semibold tracking-wider transition-colors active:scale-95 flex items-center justify-center gap-2"
              >
                <span className="material-symbols-outlined text-sm">content_copy</span>
                {copySuccess ? 'COPIED TO CLIPBOARD' : 'COPY JSON TRACE'}
              </button>
              <button
                id="close-inspector-btn"
                onClick={() => setSelectedLog(null)}
                className="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2.5 rounded text-xs font-semibold tracking-wider transition-colors active:scale-95 border border-slate-700"
              >
                CLOSE
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
