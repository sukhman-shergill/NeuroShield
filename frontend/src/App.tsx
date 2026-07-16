import React, { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import DashboardView from './components/DashboardView';
import LiveMonitoringView from './components/LiveMonitoringView';
import NetworkTrafficView from './components/NetworkTrafficView';
import AttackDetectionView from './components/AttackDetectionView';
import AIPredictionsView from './components/AIPredictionsView';
import ModelPerformanceView from './components/ModelPerformanceView';
import ReportsView from './components/ReportsView';
import SystemLogsView from './components/SystemLogsView';
import SettingsView from './components/SettingsView';

import { SecurityAlert } from './types';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [alerts, setAlerts] = useState<SecurityAlert[]>([]);

  // Fetch real security alerts from backend periodically
  useEffect(() => {
    const fetchAlerts = () => {
      fetch('/api/alerts')
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data)) {
            setAlerts(data);
          }
        })
        .catch(err => console.error('Error fetching live alerts:', err));
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleIsolateHost = (ip: string) => {
    fetch('/api/alerts/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sourceIp: ip, action: 'ISOLATE' })
    })
      .then(() => {
        setAlerts(prev => prev.map(alert => {
          if (alert.sourceIp === ip) {
            return { ...alert, actionTaken: 'ISOLATE' };
          }
          return alert;
        }));
      })
      .catch(err => console.error('Error isolating host:', err));
  };

  const handleReviewHost = (ip: string) => {
    fetch('/api/alerts/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sourceIp: ip, action: 'REVIEW' })
    })
      .then(() => {
        setAlerts(prev => prev.map(alert => {
          if (alert.sourceIp === ip) {
            return { ...alert, actionTaken: 'REVIEW' };
          }
          return alert;
        }));
      })
      .catch(err => console.error('Error marking host for review:', err));
  };

  const handleIgnoreHost = (ip: string) => {
    fetch('/api/alerts/action', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sourceIp: ip, action: 'IGNORE' })
    })
      .then(() => {
        setAlerts(prev => prev.filter(alert => alert.sourceIp !== ip));
      })
      .catch(err => console.error('Error ignoring host:', err));
  };

  // Count active/unhandled critical threats
  const activeThreatsCount = alerts.filter(a => !a.actionTaken).length;

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#0c0e16] text-[#e1e2ed] font-sans selection:bg-indigo-500/30 selection:text-indigo-200 relative">
      {/* Animated Background Blobs */}
      <div className="absolute top-0 -left-4 w-72 h-72 bg-indigo-500 rounded-full mix-blend-multiply filter blur-[128px] opacity-20 animate-blob pointer-events-none"></div>
      <div className="absolute top-0 -right-4 w-72 h-72 bg-purple-500 rounded-full mix-blend-multiply filter blur-[128px] opacity-20 animate-blob animation-delay-2000 pointer-events-none"></div>
      <div className="absolute -bottom-8 left-20 w-72 h-72 bg-emerald-500 rounded-full mix-blend-multiply filter blur-[128px] opacity-20 animate-blob animation-delay-4000 pointer-events-none"></div>

      {/* Sidebar navigation */}
      <Sidebar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        threatCount={activeThreatsCount}
      />

      {/* Main content frame */}
      <main className="flex-1 overflow-y-auto p-6 md:p-8 bg-transparent z-10 relative">
        <div className="max-w-7xl mx-auto w-full">
          {activeTab === 'dashboard' && (
            <DashboardView 
              alerts={alerts} 
              onIsolateHost={handleIsolateHost} 
              onReviewHost={handleReviewHost} 
            />
          )}
          {activeTab === 'live_monitoring' && (
            <LiveMonitoringView />
          )}
          {activeTab === 'network_traffic' && (
            <NetworkTrafficView />
          )}
          {activeTab === 'attack_detection' && (
            <AttackDetectionView 
              alerts={alerts}
              onIsolateHost={handleIsolateHost}
              onReviewHost={handleReviewHost}
              onIgnoreHost={handleIgnoreHost}
            />
          )}
          {activeTab === 'ai_predictions' && (
            <AIPredictionsView />
          )}
          {activeTab === 'model_performance' && (
            <ModelPerformanceView />
          )}
          {activeTab === 'reports' && (
            <ReportsView />
          )}
          {activeTab === 'system_logs' && (
            <SystemLogsView />
          )}
          {activeTab === 'settings' && (
            <SettingsView />
          )}
        </div>
      </main>
    </div>
  );
}
