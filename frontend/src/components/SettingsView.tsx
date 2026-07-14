import React, { useState, useEffect } from 'react';

export default function SettingsView() {
  const [saveBanner, setSaveBanner] = useState(false);

  // Real model and system info from backend
  const [modelInfo, setModelInfo] = useState<any>(null);
  const [systemStats, setSystemStats] = useState<any>(null);

  // Configuration settings (local state — in a real deployment these would persist to a config endpoint)
  const [settings, setSettings] = useState({
    apiEndpoint: 'http://127.0.0.1:5000',
    confidenceThreshold: 0.85,
    alertRetention: 50,
    autoRefreshInterval: 2,
    enableSoundAlerts: false,
    enableCriticalNotifications: true,
    enableLogStreaming: true,
    darkMode: true,
  });

  useEffect(() => {
    // Fetch model info
    fetch('/api/model/info')
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setModelInfo(data.model_info);
        }
      })
      .catch(err => console.error('Error fetching model info:', err));

    // Fetch system stats
    fetch('/api/stats')
      .then(res => res.json())
      .then(data => setSystemStats(data))
      .catch(err => console.error('Error fetching stats:', err));
  }, []);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaveBanner(true);
    setTimeout(() => setSaveBanner(false), 3000);
  };

  return (
    <div id="settings-root" className="space-y-6 font-sans">
      {/* Save banner */}
      {saveBanner && (
        <div className="bg-[#12151f] border-l-4 border-emerald-500 text-slate-200 px-4 py-3 rounded-r-lg shadow-xl flex items-center gap-2" id="settings-toast">
          <span className="material-symbols-outlined text-emerald-400 fill-icon">check_circle</span>
          <span className="text-xs font-mono">Settings saved successfully.</span>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-[#1e2230] pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span className="material-symbols-outlined text-indigo-400">settings</span>
            System Settings
          </h2>
          <p className="text-xs text-slate-400">Configure detection thresholds, alert preferences, and view system information</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Detection Configuration (2/3 width) */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-xl space-y-4">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
            <span className="material-symbols-outlined text-indigo-400">tune</span>
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Detection Configuration</h3>
          </div>

          <form onSubmit={handleSave} className="space-y-5 text-xs text-slate-300">
            {/* Confidence Threshold */}
            <div className="space-y-2">
              <div className="flex justify-between">
                <label className="text-[10px] font-mono text-slate-500 uppercase">Detection Confidence Threshold</label>
                <span className="text-indigo-400 font-mono font-bold">{(settings.confidenceThreshold * 100).toFixed(0)}%</span>
              </div>
              <input
                id="setting-threshold"
                type="range"
                min="0.5"
                max="0.99"
                step="0.01"
                value={settings.confidenceThreshold}
                onChange={(e) => setSettings(p => ({ ...p, confidenceThreshold: parseFloat(e.target.value) }))}
                className="w-full h-1 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-indigo-500"
              />
              <p className="text-[10px] text-slate-600">Predictions below this threshold will not trigger alerts. Lower = more sensitive, higher = fewer false positives.</p>
            </div>

            {/* Alert Retention */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-1.5">
                <label className="text-[10px] font-mono text-slate-500 uppercase">Alert Retention (max alerts)</label>
                <input
                  id="setting-retention"
                  type="number"
                  value={settings.alertRetention}
                  onChange={(e) => setSettings(p => ({ ...p, alertRetention: parseInt(e.target.value) || 50 }))}
                  className="w-full bg-slate-950/60 border border-slate-800 text-xs text-slate-300 px-3 py-2 rounded-lg focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-[10px] font-mono text-slate-500 uppercase">Auto-Refresh Interval (seconds)</label>
                <input
                  id="setting-refresh"
                  type="number"
                  value={settings.autoRefreshInterval}
                  onChange={(e) => setSettings(p => ({ ...p, autoRefreshInterval: parseInt(e.target.value) || 2 }))}
                  className="w-full bg-slate-950/60 border border-slate-800 text-xs text-slate-300 px-3 py-2 rounded-lg focus:outline-none focus:border-indigo-500 font-mono"
                />
              </div>
            </div>

            {/* API Endpoint */}
            <div className="space-y-1.5">
              <label className="text-[10px] font-mono text-slate-500 uppercase">Backend API Endpoint</label>
              <input
                id="setting-api-endpoint"
                type="text"
                value={settings.apiEndpoint}
                onChange={(e) => setSettings(p => ({ ...p, apiEndpoint: e.target.value }))}
                className="w-full bg-slate-950/60 border border-slate-800 text-xs text-slate-300 px-3 py-2 rounded-lg focus:outline-none focus:border-indigo-500 font-mono"
              />
            </div>

            <div className="pt-2 text-right">
              <button
                id="save-settings-btn"
                type="submit"
                className="bg-indigo-600 hover:bg-indigo-500 text-slate-100 font-bold px-5 py-2.5 rounded-lg text-xs tracking-wider transition-all duration-200 active:scale-95"
              >
                SAVE SETTINGS
              </button>
            </div>
          </form>
        </div>

        {/* Right Column: Alert Preferences */}
        <div className="glass-panel p-5 rounded-xl space-y-4" id="alert-preferences">
          <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
            <span className="material-symbols-outlined text-indigo-400">notifications</span>
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Alert Preferences</h3>
          </div>

          <div className="space-y-4 text-xs text-slate-300">
            {/* Critical Notifications Toggle */}
            <div className="flex items-center justify-between pb-2 border-b border-slate-900">
              <div>
                <p className="font-bold text-slate-200">Critical Threat Alerts</p>
                <p className="text-[10px] text-slate-500">Show notifications for critical detections</p>
              </div>
              <button
                id="toggle-critical-alerts"
                onClick={() => setSettings(p => ({ ...p, enableCriticalNotifications: !p.enableCriticalNotifications }))}
                className={`w-10 h-5 rounded-full p-0.5 transition-colors duration-200 ${
                  settings.enableCriticalNotifications ? 'bg-indigo-600' : 'bg-slate-900 border border-slate-800'
                }`}
              >
                <div className={`w-4 h-4 rounded-full bg-slate-100 transform transition-transform duration-200 ${
                  settings.enableCriticalNotifications ? 'translate-x-5' : 'translate-x-0'
                }`}></div>
              </button>
            </div>

            {/* Sound Alerts */}
            <div className="flex items-center justify-between pb-2 border-b border-slate-900">
              <div>
                <p className="font-bold text-slate-200">Sound Alerts</p>
                <p className="text-[10px] text-slate-500">Audible alert on threat detection</p>
              </div>
              <button
                id="toggle-sound-alerts"
                onClick={() => setSettings(p => ({ ...p, enableSoundAlerts: !p.enableSoundAlerts }))}
                className={`w-10 h-5 rounded-full p-0.5 transition-colors duration-200 ${
                  settings.enableSoundAlerts ? 'bg-indigo-600' : 'bg-slate-900 border border-slate-800'
                }`}
              >
                <div className={`w-4 h-4 rounded-full bg-slate-100 transform transition-transform duration-200 ${
                  settings.enableSoundAlerts ? 'translate-x-5' : 'translate-x-0'
                }`}></div>
              </button>
            </div>

            {/* Log Streaming */}
            <div className="flex items-center justify-between pb-2 border-b border-slate-900">
              <div>
                <p className="font-bold text-slate-200">Live Log Streaming</p>
                <p className="text-[10px] text-slate-500">Stream backend logs in real-time</p>
              </div>
              <button
                id="toggle-log-streaming"
                onClick={() => setSettings(p => ({ ...p, enableLogStreaming: !p.enableLogStreaming }))}
                className={`w-10 h-5 rounded-full p-0.5 transition-colors duration-200 ${
                  settings.enableLogStreaming ? 'bg-indigo-600' : 'bg-slate-900 border border-slate-800'
                }`}
              >
                <div className={`w-4 h-4 rounded-full bg-slate-100 transform transition-transform duration-200 ${
                  settings.enableLogStreaming ? 'translate-x-5' : 'translate-x-0'
                }`}></div>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* System Information Panel */}
      <div className="glass-panel p-5 rounded-xl space-y-4">
        <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
          <span className="material-symbols-outlined text-indigo-400">info</span>
          <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">System Information</h3>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4" id="system-info-grid">
          {/* Model Info */}
          <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/50 space-y-2">
            <span className="text-[9px] font-mono text-indigo-400 font-bold uppercase block">Loaded Model</span>
            <div className="space-y-1 text-[10px] font-mono text-slate-400">
              <div className="flex justify-between">
                <span>Name</span>
                <span className="text-slate-200">{modelInfo?.model_name || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span>Trained</span>
                <span className="text-slate-200">{modelInfo?.trained_at?.split('T')[0] || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span>Epochs</span>
                <span className="text-slate-200">{modelInfo?.total_epochs_trained || 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span>Input Shape</span>
                <span className="text-slate-200">{modelInfo ? `${modelInfo.input_shape[0]}×${modelInfo.input_shape[1]}` : 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span>Dataset</span>
                <span className="text-slate-200">{modelInfo?.dataset_used?.toUpperCase() || 'N/A'}</span>
              </div>
            </div>
          </div>

          {/* System Stats */}
          <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/50 space-y-2">
            <span className="text-[9px] font-mono text-emerald-400 font-bold uppercase block">Backend Server</span>
            <div className="space-y-1 text-[10px] font-mono text-slate-400">
              <div className="flex justify-between">
                <span>Uptime</span>
                <span className="text-slate-200">
                  {systemStats ? `${systemStats.uptime.days}d ${systemStats.uptime.hours}h ${systemStats.uptime.mins}m` : 'N/A'}
                </span>
              </div>
              <div className="flex justify-between">
                <span>CPU Usage</span>
                <span className="text-slate-200">{systemStats ? `${systemStats.cpu.toFixed(1)}%` : 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span>Memory Usage</span>
                <span className="text-slate-200">{systemStats ? `${systemStats.memory.toFixed(1)}%` : 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span>Request Rate</span>
                <span className="text-slate-200">{systemStats ? `${systemStats.packet_rate} req/s` : 'N/A'}</span>
              </div>
              <div className="flex justify-between">
                <span>Active Alerts</span>
                <span className="text-slate-200">{systemStats?.total_alerts ?? 'N/A'}</span>
              </div>
            </div>
          </div>

          {/* Project Info */}
          <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/50 space-y-2">
            <span className="text-[9px] font-mono text-amber-400 font-bold uppercase block">Project</span>
            <div className="space-y-1 text-[10px] font-mono text-slate-400">
              <div className="flex justify-between">
                <span>Name</span>
                <span className="text-slate-200">NeuroShield IDS</span>
              </div>
              <div className="flex justify-between">
                <span>Architecture</span>
                <span className="text-slate-200">CNN-LSTM-Attention</span>
              </div>
              <div className="flex justify-between">
                <span>Framework</span>
                <span className="text-slate-200">TensorFlow / Keras</span>
              </div>
              <div className="flex justify-between">
                <span>API</span>
                <span className="text-slate-200">Flask REST</span>
              </div>
              <div className="flex justify-between">
                <span>Frontend</span>
                <span className="text-slate-200">React + Vite</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
