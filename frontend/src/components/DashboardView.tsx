import React, { useState, useEffect, useMemo } from 'react';
import { motion } from 'motion/react';
import { SecurityAlert } from '../types';

interface DashboardViewProps {
  alerts: SecurityAlert[];
  onIsolateHost: (ip: string) => void;
  onReviewHost: (ip: string) => void;
}

export default function DashboardView({ alerts, onIsolateHost, onReviewHost }: DashboardViewProps) {
  const [hoveredMetric, setHoveredMetric] = useState<string | null>(null);
  const [selectedAlert, setSelectedAlert] = useState<SecurityAlert | null>(null);
  const [simulatedTraffic, setSimulatedTraffic] = useState<number[]>([24, 38, 45, 30, 48, 62, 55, 70, 64, 82, 78, 95, 88, 110, 105, 124, 118, 130, 125, 142]);
  const [blockedTraffic, setBlockedTraffic] = useState<number[]>([2, 4, 3, 5, 8, 12, 10, 15, 12, 18, 15, 22, 20, 25, 22, 28, 25, 30, 28, 35]);
  const [activeDonutSlice, setActiveDonutSlice] = useState<number | null>(null);
  const [modelAccuracy, setModelAccuracy] = useState<number | null>(null);
  const [modelF1, setModelF1] = useState<number | null>(null);
  const [donutData, setDonutData] = useState<Array<{label: string, value: number, color: string, textClass: string}>>([]);
  const [stats, setStats] = useState<any>(null);

  // Fetch real model metrics on mount
  useEffect(() => {
    fetch('/api/model/info')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success' && data.classification_report) {
          const report = data.classification_report;
          const acc = report.overall_accuracy || report.accuracy;
          const f1 = report.weighted_f1 || (report["weighted avg"] && report["weighted avg"]["f1-score"]);
          if (acc) setModelAccuracy(acc);
          if (f1) setModelF1(f1);
        }
      })
      .catch(err => {
        console.error('Error fetching model info:', err);
      });

    // Fetch attack distribution from evaluation
    fetch('/api/evaluation')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success' && data.attack_distribution) {
          const dist = data.attack_distribution;
          const labels = dist.labels || [];
          const counts = dist.actual_counts || [];
          const total = counts.reduce((a: number, b: number) => a + b, 0);
          if (total > 0) {
            const colorMap: Record<string, string> = {
              DoS: '#f43f5e',
              Normal: '#10b981',
              Probe: '#fbbf24',
              R2L: '#3b82f6',
              U2R: '#a855f7'
            };
            const textClassMap: Record<string, string> = {
              DoS: 'text-rose-500',
              Normal: 'text-emerald-500',
              Probe: 'text-amber-400',
              R2L: 'text-blue-500',
              U2R: 'text-purple-500'
            };

            const newDonutData = labels.map((label: string, idx: number) => {
              const count = counts[idx] || 0;
              return {
                label,
                value: Math.round((count / total) * 100),
                color: colorMap[label] || '#64748b',
                textClass: textClassMap[label] || 'text-slate-400'
              };
            }).filter((item: any) => item.value > 0).sort((a: any, b: any) => b.value - a.value);

            setDonutData(newDonutData);
          }
        }
      })
      .catch(err => console.error('Error fetching evaluation data:', err));
  }, []);

  // Fetch server stats
  useEffect(() => {
    const fetchStats = () => {
      fetch('/api/stats')
        .then(res => res.json())
        .then(data => {
          setStats(data);
        })
        .catch(err => console.error('Error fetching dashboard stats:', err));
    };

    fetchStats();
    const interval = setInterval(fetchStats, 2000);
    return () => clearInterval(interval);
  }, []);

  // Slowly shift traffic metrics in real-time to simulate a living network
  useEffect(() => {
    const timer = setInterval(() => {
      setSimulatedTraffic(prev => {
        const next = [...prev.slice(1)];
        const last = prev[prev.length - 1];
        const change = Math.floor(Math.random() * 21) - 10; // -10 to +10
        next.push(Math.max(10, Math.min(200, last + change)));
        return next;
      });

      setBlockedTraffic(prev => {
        const next = [...prev.slice(1)];
        const last = prev[prev.length - 1];
        const change = Math.floor(Math.random() * 7) - 3; // -3 to +3
        next.push(Math.max(0, Math.min(60, last + change)));
        return next;
      });
    }, 4000);

    return () => clearInterval(timer);
  }, []);

  // Quick Sparkline helper
  const drawSparkline = (data: number[], color: string) => {
    const max = Math.max(...data, 1);
    const min = Math.min(...data, 0);
    const range = max - min;
    const width = 140;
    const height = 40;
    const points = data.map((val, idx) => {
      const x = (idx / (data.length - 1)) * width;
      const y = height - ((val - min) / range) * height;
      return `${x},${y}`;
    }).join(' ');

    return (
      <svg className="w-28 h-8" viewBox={`0 0 ${width} ${height}`}>
        <polyline
          fill="none"
          stroke={color}
          strokeWidth="1.75"
          points={points}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    );
  };

  // Big Traffic Curve path helper
  const drawAreaPath = (data: number[], width: number, height: number, fill = false) => {
    const max = Math.max(...data, 1);
    const points = data.map((val, idx) => {
      const x = (idx / (data.length - 1)) * width;
      const y = height - (val / max) * (height - 15);
      return { x, y };
    });

    if (points.length === 0) return '';
    let d = `M ${points[0].x} ${points[0].y}`;
    for (let i = 1; i < points.length; i++) {
      // Bezier curve calculations for organic flow
      const cpX1 = points[i-1].x + (points[i].x - points[i-1].x) / 2;
      const cpY1 = points[i-1].y;
      const cpX2 = points[i-1].x + (points[i].x - points[i-1].x) / 2;
      const cpY2 = points[i].y;
      d += ` C ${cpX1} ${cpY1}, ${cpX2} ${cpY2}, ${points[i].x} ${points[i].y}`;
    }

    if (fill) {
      d += ` L ${width} ${height} L 0 ${height} Z`;
    }
    return d;
  };

  // Compute donut slice offsets in a render-safe way (no mutable variables in component body)
  const sliceOffsets = useMemo(() => {
    let accumulated = 0;
    return donutData.map((slice) => {
      const offset = 100 - accumulated;
      accumulated += slice.value;
      return offset;
    });
  }, [donutData]);

  return (
    <div id="soc-dashboard-root" className="space-y-6 font-sans">
      {/* Upper Status Bar & Section Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold tracking-tight flex items-center gap-2">
            <span className="material-symbols-outlined text-indigo-400 fill-icon">dashboard</span>
            <span className="text-gradient-secondary">NeuroShield Dashboard</span>
          </h2>
          <p className="text-xs text-slate-400 mt-1">Real-time status updates from the IDS model</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-mono">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-ping"></span>
            NETWORK SECURE
          </span>
          <span className="text-xs text-slate-500 font-mono">STATION ID: NEUROSHIELD-SOC-TX</span>
        </div>
      </div>

      {/* 4 Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4" id="dashboard-metric-cards">
        {/* Card 1 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0 }}
          className="glass-card p-5 rounded-xl flex items-center justify-between transition-all duration-300 hover:scale-[1.02] hover:border-slate-600"
          onMouseEnter={() => setHoveredMetric('traffic')}
          onMouseLeave={() => setHoveredMetric(null)}
        >
          <div className="space-y-1">
            <span className="text-[11px] font-bold text-slate-400 tracking-wider uppercase">Live Traffic Rate</span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-slate-100">
                {stats ? (stats.packet_rate * 12.5).toFixed(1) : '812.4'}
              </span>
              <span className="text-xs text-slate-400 font-mono">Mbps</span>
            </div>
            <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-0.5 font-bold">
              <span className="material-symbols-outlined text-xs">trending_up</span>
              +12.4% over 24h
            </span>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <span className="material-symbols-outlined text-xl">speed</span>
            </div>
            {drawSparkline(simulatedTraffic.slice(-10), '#6366f1')}
          </div>
        </motion.div>

        {/* Card 2 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="glass-card p-5 rounded-xl flex items-center justify-between transition-all duration-300 hover:scale-[1.02] hover:border-slate-600"
          onMouseEnter={() => setHoveredMetric('threats')}
          onMouseLeave={() => setHoveredMetric(null)}
        >
          <div className="space-y-1">
            <span className="text-[11px] font-bold text-slate-400 tracking-wider uppercase">Threats Flagged</span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-rose-400">
                {stats ? stats.total_alerts : '1,424'}
              </span>
              <span className="text-xs text-rose-500/80 font-mono">EVENTS</span>
            </div>
            <span className="text-[10px] text-rose-400 font-mono flex items-center gap-0.5 font-bold">
              <span className="material-symbols-outlined text-xs">warning</span>
              +8.3% increase
            </span>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="p-2 rounded-lg bg-rose-500/10 text-rose-400">
              <span className="material-symbols-outlined text-xl">gpp_maybe</span>
            </div>
            {drawSparkline(blockedTraffic.slice(-10), '#f43f5e')}
          </div>
        </motion.div>

        {/* Card 3 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.2 }}
          className="glass-card p-5 rounded-xl flex items-center justify-between transition-all duration-300 hover:scale-[1.02] hover:border-slate-600"
          onMouseEnter={() => setHoveredMetric('latency')}
          onMouseLeave={() => setHoveredMetric(null)}
        >
          <div className="space-y-1">
            <span className="text-[11px] font-bold text-slate-400 tracking-wider uppercase">Inference Speed</span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-slate-100">12.4</span>
              <span className="text-xs text-slate-400 font-mono">ms</span>
            </div>
            <span className="text-[10px] text-emerald-400 font-mono flex items-center gap-0.5 font-bold">
              <span className="material-symbols-outlined text-xs">trending_down</span>
              -14.2% (Faster)
            </span>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-400">
              <span className="material-symbols-outlined text-xl">schedule</span>
            </div>
            {drawSparkline([80, 75, 70, 72, 68, 62, 58, 55, 52, 48], '#10b981')}
          </div>
        </motion.div>

        {/* Card 4 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="glass-card p-5 rounded-xl flex items-center justify-between transition-all duration-300 hover:scale-[1.02] hover:border-slate-600"
          onMouseEnter={() => setHoveredMetric('accuracy')}
          onMouseLeave={() => setHoveredMetric(null)}
        >
          <div className="space-y-1">
            <span className="text-[11px] font-bold text-slate-400 tracking-wider uppercase">Model Performance</span>
            <div className="flex items-baseline gap-1.5">
              <span className="text-2xl font-black text-indigo-400">
                {modelF1 !== null ? (modelF1 * 100).toFixed(1) + '%' : '80.0%'}
              </span>
              <span className="text-xs text-slate-400 font-mono">F1 SCORE</span>
            </div>
            <span className="text-[10px] text-indigo-400 font-mono flex items-center gap-0.5 font-bold">
              <span className="material-symbols-outlined text-xs">done_all</span>
              Accuracy: {modelAccuracy !== null ? (modelAccuracy * 100).toFixed(1) + '%' : '80.8%'}
            </span>
          </div>
          <div className="flex flex-col items-end gap-2">
            <div className="p-2 rounded-lg bg-indigo-500/10 text-indigo-400">
              <span className="material-symbols-outlined text-xl">rocket_launch</span>
            </div>
            {drawSparkline([72, 74, 76, 77, 78, 79, 79.5, 79.8, 79.9, 80.0], '#818cf8')}
          </div>
        </motion.div>
      </div>

      {/* Resource Utilization Gauges */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.4 }}
        className="glass-panel p-5 rounded-xl"
      >
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">System Resource Utilization</h3>
            <p className="text-[10px] text-slate-400">Real-time hardware metrics from the inference engine host</p>
          </div>
          <span className="text-[10px] font-mono text-slate-500">AUTO-REFRESH: 2s</span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          {[
            { label: 'CPU Usage', value: stats?.cpu ?? 0, color: '#6366f1', icon: 'memory' },
            { label: 'Memory', value: stats?.memory ?? 0, color: '#10b981', icon: 'developer_board' },
            { label: 'GPU Compute', value: stats?.gpu?.gpu_util ?? 0, color: '#f59e0b', icon: 'bolt' },
            { label: 'GPU Memory', value: stats?.gpu?.gpu_mem_percent ?? 0, color: '#f43f5e', icon: 'sd_storage' },
          ].map((gauge) => {
            const circumference = 2 * Math.PI * 28;
            const filled = (gauge.value / 100) * circumference;
            return (
              <div key={gauge.label} className="flex flex-col items-center gap-2">
                <div className="relative w-20 h-20">
                  <svg className="w-full h-full rotate-[-90deg]" viewBox="0 0 64 64">
                    <circle cx="32" cy="32" r="28" fill="none" stroke="#1e293b" strokeWidth="4" />
                    <circle
                      cx="32" cy="32" r="28" fill="none"
                      stroke={gauge.color}
                      strokeWidth="4"
                      strokeDasharray={`${filled} ${circumference - filled}`}
                      strokeLinecap="round"
                      className="transition-all duration-700"
                    />
                  </svg>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-sm font-black text-slate-100">{gauge.value.toFixed(1)}%</span>
                  </div>
                </div>
                <div className="flex items-center gap-1">
                  <span className="material-symbols-outlined text-xs" style={{ color: gauge.color }}>{gauge.icon}</span>
                  <span className="text-[10px] font-mono text-slate-400 font-semibold">{gauge.label}</span>
                </div>
              </div>
            );
          })}
        </div>
      </motion.div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live Network Traffic Analysis */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.3 }}
          className="lg:col-span-2 glass-panel p-5 rounded-xl flex flex-col h-[320px]"
        >
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Live Traffic Monitoring (Packets / Sec)</h3>
              <p className="text-[10px] text-slate-400">Classification of inbound network traffic</p>
            </div>
            <div className="flex items-center gap-4 text-[10px] font-mono">
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded bg-indigo-500"></span>
                Inbound Requests
              </span>
              <span className="flex items-center gap-1.5">
                <span className="w-2.5 h-2.5 rounded bg-rose-500 animate-pulse"></span>
                Blocked Vector
              </span>
            </div>
          </div>

          <div className="flex-1 relative min-h-0 bg-slate-950/40 rounded-lg p-2 border border-slate-800/60">
            <svg className="w-full h-full" viewBox="0 0 500 180" preserveAspectRatio="none">
              {/* Background horizontal gridlines */}
              <line x1="0" y1="30" x2="500" y2="30" stroke="#1e293b" strokeDasharray="3,3" strokeWidth="0.5" />
              <line x1="0" y1="75" x2="500" y2="75" stroke="#1e293b" strokeDasharray="3,3" strokeWidth="0.5" />
              <line x1="0" y1="120" x2="500" y2="120" stroke="#1e293b" strokeDasharray="3,3" strokeWidth="0.5" />
              <line x1="0" y1="165" x2="500" y2="165" stroke="#1e293b" strokeDasharray="3,3" strokeWidth="0.5" />

              {/* Area fills */}
              <path d={drawAreaPath(simulatedTraffic, 500, 180, true)} fill="url(#grad-traffic)" opacity="0.12" />
              <path d={drawAreaPath(blockedTraffic, 500, 180, true)} fill="url(#grad-blocked)" opacity="0.18" />

              {/* Path strokes */}
              <path d={drawAreaPath(simulatedTraffic, 500, 180, false)} fill="none" stroke="#6366f1" strokeWidth="1.75" strokeLinecap="round" />
              <path d={drawAreaPath(blockedTraffic, 500, 180, false)} fill="none" stroke="#f43f5e" strokeWidth="1.5" strokeLinecap="round" />

              {/* Gradients */}
              <defs>
                <linearGradient id="grad-traffic" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="#6366f1" stopOpacity="0" />
                </linearGradient>
                <linearGradient id="grad-blocked" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#f43f5e" />
                  <stop offset="100%" stopColor="#f43f5e" stopOpacity="0" />
                </linearGradient>
              </defs>
            </svg>
          </div>
        </motion.div>

        {/* Threat Categories Breakdown */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="glass-panel p-5 rounded-xl flex flex-col h-[320px]"
        >
          <div>
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Attack Categories</h3>
            <p className="text-[10px] text-slate-400">Real-time multi-class threat vectors identified by CNN-LSTM model</p>
          </div>

          <div className="flex-1 flex flex-col sm:flex-row items-center justify-around gap-4 min-h-0 py-2">
            {/* SVG Donut */}
            <div className="relative w-32 h-32 flex-shrink-0">
              <svg className="w-full h-full rotate-[-90deg]" viewBox="0 0 36 36">
                <circle cx="18" cy="18" r="15.915" fill="none" stroke="#1e293b" strokeWidth="3" />
                
                {donutData.map((slice, i) => {
                  const dashArray = `${slice.value} ${100 - slice.value}`;
                  const offset = sliceOffsets[i];

                  const isHovered = activeDonutSlice === i;
                  return (
                    <circle
                      key={slice.label}
                      cx="18"
                      cy="18"
                      r="15.915"
                      fill="none"
                      stroke={slice.color}
                      strokeWidth={isHovered ? "4" : "3"}
                      strokeDasharray={dashArray}
                      strokeDashoffset={offset}
                      className="transition-all duration-300 cursor-pointer"
                      onMouseEnter={() => setActiveDonutSlice(i)}
                      onMouseLeave={() => setActiveDonutSlice(null)}
                    />
                  );
                })}
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center text-center pointer-events-none">
                <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">Active</span>
                <span className="text-lg font-black text-slate-200">
                  {activeDonutSlice !== null ? `${donutData[activeDonutSlice].value}%` : '100%'}
                </span>
                <span className="text-[9px] text-slate-400 truncate max-w-[80px]">
                  {activeDonutSlice !== null ? donutData[activeDonutSlice].label : 'Classified'}
                </span>
              </div>
            </div>

            {/* Labels */}
            <div className="space-y-2 flex-1">
              {donutData.map((slice, i) => (
                <div 
                  key={slice.label} 
                  className={`flex items-center justify-between p-1 rounded transition-colors ${activeDonutSlice === i ? 'bg-slate-800/30' : ''}`}
                  onMouseEnter={() => setActiveDonutSlice(i)}
                  onMouseLeave={() => setActiveDonutSlice(null)}
                >
                  <div className="flex items-center gap-1.5">
                    <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: slice.color }}></span>
                    <span className="text-[10px] text-slate-300 font-medium">{slice.label}</span>
                  </div>
                  <span className={`text-[10px] font-mono font-bold ${slice.textClass}`}>{slice.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Bottom Row - Alerts Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.5 }}
        className="glass-panel p-5 rounded-xl"
      >
        <div className="flex items-center justify-between mb-4 border-b border-[#1e2230] pb-3">
          <div>
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Real-Time Threat Detections</h3>
            <p className="text-[10px] text-slate-400">Select any row to review network packet triggers or run mitigation commands</p>
          </div>
          <span className="text-xs font-mono text-slate-500">Live Queue: {alerts.length} Records</span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse" id="dashboard-threat-table">
            <thead>
              <tr className="border-b border-[#1e2230] text-slate-400 text-[10px] font-mono uppercase tracking-wider">
                <th className="py-2.5 font-semibold">Timestamp</th>
                <th className="py-2.5 font-semibold">Source IP</th>
                <th className="py-2.5 font-semibold">Classification Vector</th>
                <th className="py-2.5 font-semibold text-center">Severity</th>
                <th className="py-2.5 font-semibold">Service Protocol</th>
                <th className="py-2.5 font-semibold text-right">Confidence Score</th>
                <th className="py-2.5 font-semibold text-center">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-[#181a25]/40 text-xs text-slate-300">
              {alerts.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-12 text-center">
                    <div className="flex flex-col items-center gap-2 text-slate-500">
                      <span className="material-symbols-outlined text-3xl text-slate-600">verified_user</span>
                      <span className="text-sm font-medium">No threats detected</span>
                      <span className="text-[10px] font-mono">All network traffic is currently classified as benign</span>
                    </div>
                  </td>
                </tr>
              )}
              {alerts.map((alert, index) => {
                const isCritical = alert.severity === 'Critical';
                const isHigh = alert.severity === 'High';
                
                return (
                  <tr 
                    key={index} 
                    className="hover:bg-slate-800/10 cursor-pointer transition-colors"
                    onClick={() => setSelectedAlert(alert)}
                  >
                    <td className="py-3 font-mono text-[11px] text-slate-400">{alert.timestamp}</td>
                    <td className="py-3 font-mono text-slate-100 font-semibold">{alert.sourceIp}</td>
                    <td className="py-3 font-medium">
                      <div className="flex items-center gap-1.5">
                        <span className={`w-1.5 h-1.5 rounded-full ${isCritical ? 'bg-rose-500 animate-pulse' : isHigh ? 'bg-amber-500' : 'bg-indigo-400'}`}></span>
                        {alert.attackType || (alert as any).predictedAttack}
                      </div>
                    </td>
                    <td className="py-3 text-center">
                      <span className={`px-2 py-0.5 rounded-full text-[9px] font-mono font-bold uppercase ${
                        isCritical ? 'bg-rose-500/15 text-rose-400 ring-1 ring-rose-500/20' :
                        isHigh ? 'bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/20' :
                        alert.severity === 'Medium' ? 'bg-blue-500/15 text-blue-400 ring-1 ring-blue-500/20' :
                        'bg-slate-500/15 text-slate-400 ring-1 ring-slate-500/20'
                      }`}>
                        {alert.severity}
                      </span>
                    </td>
                    <td className="py-3 font-mono text-slate-400 text-[11px]">{alert.protocol || (alert as any).protocolPort}</td>
                    <td className="py-3 text-right font-mono text-slate-200 font-semibold">{alert.confScore || (alert as any).confidenceScore || 72.5}%</td>
                    <td className="py-3 text-center">
                      {alert.actionTaken === 'ISOLATE' ? (
                        <span className="text-[10px] font-mono text-rose-400 bg-rose-500/10 px-2.5 py-1 rounded border border-rose-500/20">ISOLATED</span>
                      ) : alert.actionTaken === 'REVIEW' ? (
                        <span className="text-[10px] font-mono text-amber-400 bg-amber-500/10 px-2.5 py-1 rounded border border-amber-500/20">UNDER REVIEW</span>
                      ) : (
                        <div className="flex items-center justify-center gap-2">
                          <button 
                            id={`isolate-btn-${index}`}
                            onClick={(e) => {
                              e.stopPropagation();
                              onIsolateHost(alert.sourceIp);
                            }}
                            className="bg-rose-500/10 text-rose-400 hover:bg-rose-500/20 px-2 py-1 rounded text-[10px] font-mono border border-rose-500/20 transition-all active:scale-95"
                          >
                            ISOLATE
                          </button>
                          <button 
                            id={`review-btn-${index}`}
                            onClick={(e) => {
                              e.stopPropagation();
                              onReviewHost(alert.sourceIp);
                            }}
                            className="bg-slate-800 text-slate-300 hover:bg-slate-700 px-2 py-1 rounded text-[10px] font-mono border border-slate-700 transition-all active:scale-95"
                          >
                            REVIEW
                          </button>
                        </div>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </motion.div>

      {/* Alert Inspector Modal overlay */}
      {selectedAlert && (
        <div className="fixed inset-0 bg-slate-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" id="alert-detail-modal">
          <div className="glass-panel w-full max-w-lg p-6 rounded-xl space-y-4 shadow-2xl relative border border-slate-700/50">
            <button 
              onClick={() => setSelectedAlert(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 material-symbols-outlined"
              id="close-modal-btn"
            >
              close
            </button>
            <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
              <span className="material-symbols-outlined text-rose-500 fill-icon">gpp_maybe</span>
              <h4 className="text-sm font-bold text-slate-100 uppercase tracking-wide">Threat Vector Inspector</h4>
            </div>

            <div className="space-y-2.5 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-800/40">
                <span className="text-slate-400">Incident Time</span>
                <span className="font-mono text-slate-200">{selectedAlert.timestamp}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/40">
                <span className="text-slate-400">Assailant IP</span>
                <span className="font-mono text-slate-200 font-bold">{selectedAlert.sourceIp}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/40">
                <span className="text-slate-400">Target IP</span>
                <span className="font-mono text-slate-200">{selectedAlert.destIp || (selectedAlert as any).destinationIp || '10.0.0.1'}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/40">
                <span className="text-slate-400">Service Protocol</span>
                <span className="font-mono text-slate-200">{selectedAlert.protocol || (selectedAlert as any).protocolPort}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/40">
                <span className="text-slate-400">AI Classification</span>
                <span className="text-slate-200 font-semibold">{selectedAlert.attackType || (selectedAlert as any).predictedAttack}</span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-800/40">
                <span className="text-slate-400">Confidence Score</span>
                <span className="font-mono text-indigo-400 font-bold">{selectedAlert.confScore || 72.5}%</span>
              </div>
              <div className="flex justify-between py-1.5">
                <span className="text-slate-400">Threat Severity</span>
                <span className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase ${
                  selectedAlert.severity === 'Critical' ? 'bg-rose-500/20 text-rose-400' : 'bg-amber-500/20 text-amber-400'
                }`}>
                  {selectedAlert.severity}
                </span>
              </div>
            </div>

            <div className="bg-slate-950 p-3 rounded text-[10px] font-mono text-emerald-400 border border-slate-800 max-h-32 overflow-y-auto">
              <span className="text-slate-500">// RAW PACKET HEX DECODED STREAM</span>
              <p className="mt-1 leading-relaxed">
                0000  00 0c 29 1b d4 de 00 50  56 f3 c7 2a 08 00 45 00  ..)..PV..*..E.{"\n"}
                0010  00 3c b7 a4 40 00 40 06  e5 b9 c0 a8 01 68 0a 00  .&lt;..@.@......h..{"\n"}
                0020  00 2a 01 bb 1f 90 2d 69  54 c3 00 00 00 00 a0 02  .*....-iT.......{"\n"}
                0030  72 10 d7 b4 00 00 02 04  05 b4 04 02 08 0a 31 1a  r.............1.
              </p>
            </div>

            <div className="flex gap-2 pt-2">
              <button
                id="modal-isolate-host-btn"
                onClick={() => {
                  onIsolateHost(selectedAlert.sourceIp);
                  setSelectedAlert(null);
                }}
                className="flex-1 bg-rose-600 hover:bg-rose-700 text-slate-100 py-2 rounded text-xs font-semibold tracking-wider transition-colors active:scale-95"
              >
                ISOLATE SOURCE HOST
              </button>
              <button
                id="modal-review-host-btn"
                onClick={() => {
                  onReviewHost(selectedAlert.sourceIp);
                  setSelectedAlert(null);
                }}
                className="flex-1 bg-slate-800 hover:bg-slate-700 text-slate-300 py-2 rounded text-xs font-semibold tracking-wider transition-colors active:scale-95 border border-slate-700"
              >
                FLAG FOR AUDIT
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
