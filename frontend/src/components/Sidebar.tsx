import React, { useState, useEffect } from 'react';

interface SidebarProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  threatCount: number;
}

export default function Sidebar({ activeTab, setActiveTab, threatCount }: SidebarProps) {
  const [currentTime, setCurrentTime] = useState(new Date().toISOString().substring(11, 19));

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toISOString().substring(11, 19));
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  const menuItems = [
    { id: 'dashboard', label: 'SOC Dashboard', icon: 'grid_view' },
    { id: 'live_monitoring', label: 'Live Monitoring', icon: 'analytics', badge: 'LIVE' },
    { id: 'network_traffic', label: 'Network Traffic', icon: 'hub' },
    { id: 'attack_detection', label: 'Attack Detection', icon: 'gpp_bad', badge: threatCount > 0 ? String(threatCount) : undefined, badgeColor: 'bg-red-500/10 text-red-400 ring-red-500/20' },
    { id: 'ai_predictions', label: 'AI Predictions', icon: 'psychology' },
    { id: 'model_performance', label: 'Model Performance', icon: 'insights' },
    { id: 'reports', label: 'Reports', icon: 'assessment' },
    { id: 'system_logs', label: 'System Logs', icon: 'terminal' },
    { id: 'settings', label: 'Settings', icon: 'settings' }
  ];

  return (
    <aside id="sidebar-nav" className="w-64 bg-[#0e1017] border-r border-[#1e2230] flex flex-col h-screen shrink-0 font-sans">
      {/* Brand Logo Header */}
      <div className="p-6 border-b border-[#1e2230] flex items-center gap-3">
        <span className="material-symbols-outlined text-indigo-400 text-3xl fill-icon animate-pulse" id="brand-logo-icon">shield</span>
        <div>
          <h1 className="text-sm font-extrabold tracking-wider text-slate-100 uppercase" id="brand-name">NeuroShield</h1>
          <p className="text-[10px] text-slate-500 font-mono tracking-widest uppercase">Intrusion Detection System</p>
        </div>
      </div>

      {/* System Status Panel */}
      <div className="p-5 border-b border-[#1e2230] bg-[#12151f]/50" id="sidebar-status-panel">
        <div className="flex items-center gap-2 mb-2">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#4caf50] opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-[#4caf50]"></span>
          </span>
          <span className="text-[9px] text-[#4caf50] uppercase font-mono tracking-wider font-semibold">SYSTEM ONLINE</span>
        </div>
        <div className="space-y-1 text-[10px] font-mono text-slate-500">
          <div className="flex justify-between">
            <span>Model</span>
            <span className="text-slate-400">CNN-LSTM-Attention</span>
          </div>
          <div className="flex justify-between">
            <span>API</span>
            <span className="text-emerald-400">Connected</span>
          </div>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className="flex-1 overflow-y-auto p-4 space-y-1.5" id="sidebar-nav-menu">
        {menuItems.map((item) => {
          const isSelected = activeTab === item.id;
          return (
            <button
              key={item.id}
              id={`sidebar-item-${item.id}`}
              onClick={() => setActiveTab(item.id)}
              className={`w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all duration-200 relative group text-left ${
                isSelected
                  ? 'bg-indigo-500/10 text-indigo-400 font-semibold border-l-2 border-indigo-400'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/30'
              }`}
            >
              <span className={`material-symbols-outlined text-lg ${
                isSelected ? 'text-indigo-400 fill-icon' : 'text-slate-500 group-hover:text-slate-400'
              }`}>
                {item.icon}
              </span>
              <span className="flex-1">{item.label}</span>
              {item.badge && (
                <span className={`px-2 py-0.5 text-[9px] rounded-full font-mono font-bold uppercase ${
                  item.badgeColor || 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                }`}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* System Pulse Footer */}
      <div className="p-4 border-t border-[#1e2230] bg-[#0b0c12]" id="sidebar-footer">
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-500">
          <span>SYSTEM TIME (UTC)</span>
          <span className="text-slate-400 font-semibold">{currentTime}</span>
        </div>
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 mt-1">
          <span>ENGINE</span>
          <span className="text-slate-400 font-semibold">TensorFlow + Flask</span>
        </div>
        <div className="flex items-center justify-between text-[10px] font-mono text-slate-500 mt-1.5 pt-1.5 border-t border-[#1e2230]">
          <span>VERSION</span>
          <span className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-[9px] font-bold">v1.0.0</span>
        </div>
        <div className="flex flex-col gap-0.5 text-[9px] font-mono text-slate-500 mt-2 pt-2 border-t border-[#1e2230] text-center opacity-70">
          <span>Sukhman Singh</span>
          <span>C-DAC Mohali Summer Training</span>
        </div>
      </div>
    </aside>
  );
}
