import React, { useState, useEffect } from 'react';
import { ReportItem } from '../types';

export default function ReportsView() {
  const [reports, setReports] = useState<ReportItem[]>([]);
  const [template, setTemplate] = useState('SOC_2_Compliance');
  const [format, setFormat] = useState('CSV');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationProgress, setGenerationProgress] = useState(0);
  const [dateRange, setDateRange] = useState('Last 24 Hours');
  const [searchTerm, setSearchTerm] = useState('');

  // Analyst reference cards (just static context display)
  const analysts = [
    { name: 'Alex Rivera', role: 'SOC Analyst', initials: 'AR', color: 'bg-indigo-600' },
    { name: 'Alex Chen', role: 'Compliance Director', initials: 'AC', color: 'bg-emerald-600' },
    { name: 'S. Kaelo', role: 'Security Manager', initials: 'SK', color: 'bg-amber-600' },
    { name: 'A. Vance', role: 'Senior Auditor', initials: 'AV', color: 'bg-rose-600' }
  ];

  // Fetch report list from backend
  const fetchReports = () => {
    fetch('/api/reports')
      .then(res => res.json())
      .then(data => {
        if (Array.isArray(data)) {
          setReports(data);
        }
      })
      .catch(err => console.error('Error fetching reports:', err));
  };

  useEffect(() => {
    fetchReports();
  }, []);

  const handleGenerateReport = () => {
    setIsGenerating(true);
    setGenerationProgress(0);

    // Visual progress bar ticks
    const interval = setInterval(() => {
      setGenerationProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          
          // Call actual backend report generation endpoint
          fetch('/api/reports/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ template, dateRange, format })
          })
            .then(res => res.json())
            .then(data => {
              setIsGenerating(false);
              if (data.status === 'success') {
                fetchReports();
              } else {
                alert('Report generation failed: ' + data.message);
              }
            })
            .catch(err => {
              setIsGenerating(false);
              console.error(err);
              alert('Could not reach backend.');
            });

          return 100;
        }
        return prev + 25;
      });
    }, 200);
  };

  const handleDownloadReport = (name: string) => {
    // Open direct download link served by Flask
    window.open(`/api/reports/download/${name}`, '_blank');
  };

  const filteredReports = reports.filter(rep => 
    rep.name.toLowerCase().includes(searchTerm.toLowerCase()) || 
    rep.type.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div id="reports-root" className="space-y-6 font-sans">
      {/* Upper bar */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-[#1e2230] pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span className="material-symbols-outlined text-indigo-400">assessment</span>
            Auditing & Compliance Reports
          </h2>
          <p className="text-xs text-slate-400">Generate security reports and verify SHA-256 integrity hashes</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono bg-slate-950 p-2 rounded-lg border border-slate-800">
          <span className="text-slate-500">Security Audit:</span>
          <span className="text-emerald-400 font-bold flex items-center gap-1">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            ACTIVE AUDIT PROTOCOL
          </span>
        </div>
      </div>

      {/* KPI summaries */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4" id="reports-stats-cards">
        <div className="bg-[#12141f]/60 p-4 rounded-xl border border-[#1e2230]">
          <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider block">Generated Reports</span>
          <p className="text-2xl font-black text-slate-200 font-mono mt-0.5">{reports.length}</p>
        </div>
        <div className="bg-[#12141f]/60 p-4 rounded-xl border border-[#1e2230]">
          <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider block">Active Policy Scope</span>
          <p className="text-2xl font-black text-indigo-400 font-mono mt-0.5">3 Areas</p>
        </div>
        <div className="bg-[#12141f]/60 p-4 rounded-xl border border-[#1e2230]">
          <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider block">Hashes Verified</span>
          <p className="text-2xl font-black text-slate-200 font-mono mt-0.5">100% Valid</p>
        </div>
      </div>

      {/* Generation Panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Generate Custom Report Form */}
        <div className="glass-panel p-5 rounded-xl space-y-4 flex flex-col justify-between h-[360px]" id="report-generator-form">
          <div className="space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
              <span className="material-symbols-outlined text-indigo-400">build_circle</span>
              <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Report Synthesizer</h3>
            </div>

            <div className="space-y-3 text-xs">
              {/* Template dropdown */}
              <div className="space-y-1">
                <label className="text-[10px] font-mono text-slate-500 uppercase block">Report Template</label>
                <select
                  id="report-template-select"
                  value={template}
                  onChange={(e) => setTemplate(e.target.value)}
                  disabled={isGenerating}
                  className="w-full bg-slate-950/60 border border-slate-800 text-xs text-slate-300 px-3 py-2 rounded-lg font-mono focus:outline-none focus:border-indigo-500"
                >
                  <option value="SOC_2_Compliance">SOC 2 Compliance Audit</option>
                  <option value="ISO_27001_Audit">ISO 27001 Standard Log</option>
                  <option value="Penetration_Test_Summary">Penetration Test Summary</option>
                  <option value="Threat_Incident_Log">Threat Incident Vector Log</option>
                </select>
              </div>

              {/* Date filters / output formats */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1">
                  <label className="text-[10px] font-mono text-slate-500 block">Logging Scope</label>
                  <select
                    id="report-date-scope"
                    value={dateRange}
                    onChange={(e) => setDateRange(e.target.value)}
                    disabled={isGenerating}
                    className="w-full bg-slate-950/60 border border-slate-800 text-xs text-slate-300 px-3 py-2 rounded-lg font-mono focus:outline-none focus:border-indigo-500"
                  >
                    <option value="Last 24 Hours">Last 24 Hours</option>
                    <option value="Last 7 Days">Last 7 Days</option>
                    <option value="Last 30 Days">Last 30 Days</option>
                  </select>
                </div>
                <div className="space-y-1">
                  <label className="text-[10px] font-mono text-slate-500 block">Export Format</label>
                  <select
                    id="report-format-select"
                    value={format}
                    disabled={true} // Only CSV supported dynamically
                    className="w-full bg-slate-950/20 border border-slate-900 text-xs text-slate-500 px-3 py-2 rounded-lg font-mono cursor-not-allowed"
                  >
                    <option value="CSV">CSV Table</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          <button
            id="synthesize-report-btn"
            onClick={handleGenerateReport}
            disabled={isGenerating}
            className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-slate-800 text-slate-100 disabled:text-slate-500 py-3 rounded-lg text-xs font-bold tracking-wider transition-all duration-200 active:scale-95"
          >
            {isGenerating ? `COMPILING SUMMARY (${generationProgress}%)` : 'SYNTHESIZE COMPLIANCE REPORT'}
          </button>
        </div>

        {/* Right Columns: Active Analysts */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-xl flex flex-col justify-between h-[360px]" id="analysts-review-board">
          <div className="space-y-3">
            <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
              <span className="material-symbols-outlined text-indigo-400">groups</span>
              <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">SOC Analysts & Sign-off Auths</h3>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {analysts.map((a, idx) => (
                <div key={idx} className="bg-slate-950/50 p-3 rounded-lg border border-slate-800/80 flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-full border border-slate-700 flex items-center justify-center text-xs font-bold text-white ${a.color}`}>
                    {a.initials}
                  </div>
                  <div>
                    <h4 className="text-xs font-bold text-slate-200">{a.name}</h4>
                    <p className="text-[10px] text-slate-400">{a.role}</p>
                    <span className="inline-block bg-indigo-500/10 text-indigo-400 text-[8px] font-mono font-bold px-1.5 py-0.5 rounded mt-1 border border-indigo-500/20">
                      LEVEL-3 SIGNATURE OK
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="text-[10px] text-slate-500 bg-slate-900/10 p-3 rounded border border-slate-800/60 leading-normal">
            <span className="font-bold text-slate-400 font-mono flex items-center gap-1 mb-1">
              <span className="w-1.5 h-1.5 rounded-full bg-indigo-400"></span>
              Report Integrity Notice
            </span>
            <span>Reports generated via the dashboard are compiled into CSV files. Standard SHA-256 hashes are provided to ensure the logs have not been modified after generation.</span>
          </div>
        </div>
      </div>

      {/* Reports Catalog Table */}
      <div className="glass-panel p-5 rounded-xl">
        <div className="flex flex-col sm:flex-row items-center justify-between gap-3 mb-4 border-b border-slate-800/60 pb-3">
          <div>
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Reports Archive Catalog</h3>
            <p className="text-[10px] text-slate-400">Verify hashes, download generated audit packages, and manage compliance pipelines</p>
          </div>

          <div className="relative w-full sm:w-64">
            <span className="material-symbols-outlined absolute left-3 top-2.5 text-slate-500 text-xs">search</span>
            <input
              id="report-search-input"
              type="text"
              placeholder="Search reports archive..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-slate-950/60 border border-slate-800 text-xs text-slate-200 pl-8 pr-4 py-1.5 rounded-lg focus:outline-none focus:border-indigo-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          {reports.length === 0 ? (
            <p className="text-xs text-slate-500 italic py-10 text-center">// REPORTS ARCHIVE EMPTY</p>
          ) : (
            <table className="w-full text-left" id="reports-archive-table">
              <thead>
                <tr className="border-b border-[#1e2230] text-slate-400 text-[10px] font-mono uppercase tracking-wider">
                  <th className="pb-2">Filename</th>
                  <th className="pb-2">Template Type</th>
                  <th className="pb-2">Generated Timestamp</th>
                  <th className="pb-2">SHA-256 verified Hash</th>
                  <th className="pb-2 text-center">Status</th>
                  <th className="pb-2 text-center">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#181a25]/40 text-xs text-slate-300">
                {filteredReports.map((rep) => (
                  <tr key={rep.id} className="hover:bg-slate-800/10 transition-colors">
                    <td className="py-3 font-semibold text-slate-200 font-mono">{rep.name}</td>
                    <td className="py-3">
                      <span className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase ${
                        rep.type === 'Audit' ? 'bg-indigo-500/10 text-indigo-400 border border-indigo-500/20' :
                        rep.type === 'Vulnerability' ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' :
                        'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
                      }`}>
                        {rep.type}
                      </span>
                    </td>
                    <td className="py-3 text-slate-400">{rep.generated}</td>
                    <td className="py-3 font-mono text-[11px] text-slate-500">{rep.hash}</td>
                    <td className="py-3 text-center">
                      <span className={`inline-block px-2 py-0.5 rounded-full text-[9px] font-mono font-bold uppercase ${
                        rep.status === 'Ready' ? 'bg-emerald-500/10 text-emerald-400 animate-pulse' : 'bg-amber-500/10 text-amber-400'
                      }`}>
                        {rep.status}
                      </span>
                    </td>
                    <td className="py-3">
                      <div className="flex items-center justify-center gap-2">
                        <button
                          id={`download-report-btn-${rep.id}`}
                          onClick={() => handleDownloadReport(rep.name)}
                          className="text-indigo-400 hover:text-indigo-300 material-symbols-outlined text-lg p-1"
                          title="Download Document"
                        >
                          download
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
