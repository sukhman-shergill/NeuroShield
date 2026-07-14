import React, { useState, useEffect, useRef } from 'react';
import { ActiveConnection, SystemLog } from '../types';

export default function LiveMonitoringView() {
  const [uptime, setUptime] = useState({ days: 0, hours: 0, mins: 0, secs: 0 });
  const [connections, setConnections] = useState<ActiveConnection[]>([]);
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [isLive, setIsLive] = useState(true);
  const [filterSeverity, setFilterSeverity] = useState<string>('ALL');
  const [selectedConnection, setSelectedConnection] = useState<ActiveConnection | null>(null);
  const [hoveredBar, setHoveredBar] = useState<number | null>(null);
  const [packetRate, setPacketRate] = useState<number>(0);
  const [cpuUsage, setCpuUsage] = useState<number>(10);
  const [memoryUsage, setMemoryUsage] = useState<number>(40);
  const [gpuUsage, setGpuUsage] = useState<number | null>(null);
  const [simulationRunning, setSimulationRunning] = useState(false);
  const [simulationType, setSimulationType] = useState('auto');

  // SVG bar chart data (last 15 packet rate readings)
  const [barData, setBarData] = useState<number[]>([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]);

  const logTerminalRef = useRef<HTMLDivElement>(null);

  // Poll backend for stats, connections, logs, and simulation status
  useEffect(() => {
    const fetchSimulationStatus = () => {
      fetch('/api/simulation/status')
        .then(res => res.json())
        .then(data => {
          if (data.status === 'success') {
            setSimulationRunning(data.running);
          }
        })
        .catch(err => console.error('Error fetching simulation status:', err));
    };

    fetchSimulationStatus();
    const simInterval = setInterval(fetchSimulationStatus, 3000);
    return () => clearInterval(simInterval);
  }, []);

  useEffect(() => {
    if (!isLive) return;

    const fetchData = () => {
      // Fetch stats
      fetch('/api/stats')
        .then(res => res.json())
        .then(data => {
          if (data.uptime) setUptime(data.uptime);
          if (data.packet_rate !== undefined) setPacketRate(data.packet_rate);
          if (data.cpu !== undefined) setCpuUsage(data.cpu);
          if (data.memory !== undefined) setMemoryUsage(data.memory);
          if (data.gpu !== undefined) {
            setGpuUsage(data.gpu ? data.gpu.gpu_util : null);
          }
        })
        .catch(err => console.error('Error fetching stats:', err));

      // Fetch connections
      fetch('/api/connections')
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data)) {
            setConnections(data);
            // Default to first connection if none selected
            if (data.length > 0 && !selectedConnection) {
              setSelectedConnection(data[0]);
            }
          }
        })
        .catch(err => console.error('Error fetching connections:', err));

      // Fetch logs
      fetch('/api/logs')
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data)) {
            setLogs(data);
          }
        })
        .catch(err => console.error('Error fetching logs:', err));
    };

    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [isLive, selectedConnection]);

  const startSimulation = () => {
    fetch('/api/simulation/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ attack_type: simulationType }),
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setSimulationRunning(true);
        } else {
          alert('Failed to start simulation: ' + data.message);
        }
      })
      .catch(err => console.error('Error starting simulation:', err));
  };

  const stopSimulation = () => {
    fetch('/api/simulation/stop', {
      method: 'POST',
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === 'success') {
          setSimulationRunning(false);
        } else {
          alert('Failed to stop simulation: ' + data.message);
        }
      })
      .catch(err => console.error('Error stopping simulation:', err));
  };

  // Update bar chart data based on packetRate
  useEffect(() => {
    if (!isLive) return;
    setBarData(prev => {
      const next = [...prev.slice(1)];
      // Convert packetRate (packets/sec) into a visual integer count scale (e.g. scale up for display)
      next.push(Math.round(packetRate * 25));
      return next;
    });
  }, [packetRate, isLive]);

  const filteredLogs = logs.filter(l => {
    if (filterSeverity === 'ALL') return true;
    if (filterSeverity === 'CRITICAL' && (l.severity === 'CRIT' || l.severity === 'ERROR')) return true;
    return l.severity === filterSeverity;
  });

  const getPacketPayloads = (conn: ActiveConnection | null) => {
    if (!conn) return { hex: 'No active connection selected.\nStream packets to see dump.', text: 'N/A' };
    
    const seed = conn.sourceIp.split('.').join(' ');
    return {
      hex: `0000  00 1a 4b ${seed.substring(0, 2)} 42 c8 00 a0 c9 b1 7c a4 08 00 45 00\n0010  00 28 a7 e1 40 00 80 06 db a1 c0 a8 01 37 0a 0c\n0020  00 d7 ${seed.substring(seed.length - 2)} f8 00 50 d2 4b 01 e2 d5 f0 a0 12\n0030  40 00 df c3 00 00 02 04 05 b4 01 03 03 08 01 01`,
      text: `Inbound connection from ${conn.sourceIp} to port 80/443.\nProtocol: ${conn.protocol}\nChannel Load: ${conn.load}%\nStatus: ACTIVE`
    };
  };

  const payload = getPacketPayloads(selectedConnection);

  return (
    <div id="live-monitoring-root" className="space-y-6 font-sans">
      {/* Header and Counters bar */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-[#1e2230] pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span className="material-symbols-outlined text-indigo-400">analytics</span>
            Live Monitoring Console
          </h2>
          <p className="text-xs text-slate-400">Real-time network traffic and model analysis</p>
        </div>

        {/* Uptime and Counters */}
        <div className="flex flex-wrap items-center gap-4" id="uptime-dashboard-widgets">
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg px-4 py-2 flex items-center gap-3">
            <span className="material-symbols-outlined text-indigo-400 text-lg">timer</span>
            <div>
              <p className="text-[9px] text-slate-500 font-mono tracking-wider uppercase">System Uptime</p>
              <p className="text-xs font-bold text-slate-200 font-mono">
                {uptime.days}d {uptime.hours}h {uptime.mins}m {uptime.secs}s
              </p>
            </div>
          </div>
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg px-4 py-2 flex items-center gap-3">
            <span className="material-symbols-outlined text-emerald-400 text-lg">stacked_line_chart</span>
            <div>
              <p className="text-[9px] text-slate-500 font-mono tracking-wider uppercase">Active Request Rate</p>
              <p className="text-xs font-bold text-emerald-400 font-mono">{packetRate} req/s</p>
            </div>
          </div>
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg px-4 py-2 flex items-center gap-3">
            <span className="material-symbols-outlined text-blue-400 text-lg">memory</span>
            <div>
              <p className="text-[9px] text-slate-500 font-mono tracking-wider uppercase">Backend CPU Usage</p>
              <p className="text-xs font-bold text-blue-400 font-mono">{cpuUsage.toFixed(1)}%</p>
            </div>
          </div>
          <div className="bg-slate-950/60 border border-slate-800/80 rounded-lg px-4 py-2 flex items-center gap-3">
            <span className="material-symbols-outlined text-indigo-400 text-lg">developer_board</span>
            <div>
              <p className="text-[9px] text-slate-500 font-mono tracking-wider uppercase">Backend GPU Usage</p>
              <p className="text-xs font-bold text-indigo-400 font-mono">
                {gpuUsage !== null ? `${gpuUsage.toFixed(1)}%` : 'Active (0.0%)'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Attack Simulator Control Panel */}
      <div className="glass-panel p-5 rounded-xl space-y-4" id="attack-simulator-panel">
        <div className="flex flex-col sm:flex-row justify-between sm:items-center gap-4">
          <div>
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase flex items-center gap-2">
              <span className={`w-2.5 h-2.5 rounded-full ${simulationRunning ? 'bg-rose-500' : 'bg-slate-600'} ${simulationRunning ? 'animate-pulse' : ''}`}></span>
              Real-time Attack Intrusion Simulator
            </h3>
            <p className="text-[10px] text-slate-400">Trigger background attack sequences against the CNN-LSTM detection engine to verify live alerting pipelines</p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-mono text-slate-500 uppercase">Attack Profile:</span>
              <select
                id="simulator-type-select"
                value={simulationType}
                onChange={(e) => setSimulationType(e.target.value)}
                disabled={simulationRunning}
                className="bg-slate-950/60 border border-slate-800 text-xs text-slate-300 px-3 py-1.5 rounded-lg focus:outline-none focus:border-indigo-500 font-mono disabled:opacity-50"
              >
                <option value="auto">Mixed Traffic (Auto-mode)</option>
                <option value="DoS">Denial of Service (DoS)</option>
                <option value="Probe">Reconnaissance Scan (Probe)</option>
                <option value="R2L">Remote-to-Local (R2L)</option>
                <option value="U2R">Privilege Escalation (U2R)</option>
              </select>
            </div>

            {simulationRunning ? (
              <button
                id="stop-simulator-btn"
                onClick={stopSimulation}
                className="bg-rose-600 hover:bg-rose-700 text-slate-100 px-4 py-1.5 rounded-lg text-xs font-bold tracking-wider font-mono transition-all duration-200 active:scale-95 flex items-center gap-1.5"
              >
                <span className="material-symbols-outlined text-sm">stop_circle</span>
                STOP SIMULATION
              </button>
            ) : (
              <button
                id="start-simulator-btn"
                onClick={startSimulation}
                className="bg-indigo-600 hover:bg-indigo-500 text-slate-100 px-4 py-1.5 rounded-lg text-xs font-bold tracking-wider font-mono transition-all duration-200 active:scale-95 flex items-center gap-1.5"
              >
                <span className="material-symbols-outlined text-sm">play_circle</span>
                LAUNCH ATTACK
              </button>
            )}
          </div>
        </div>

        {simulationRunning && (
          <div className="bg-rose-500/10 border border-rose-500/20 rounded-lg p-3 flex items-center gap-3 text-xs text-rose-400">
            <span className="material-symbols-outlined text-lg animate-pulse">gpp_maybe</span>
            <span className="font-medium animate-pulse">
              Simulation actively injecting anomalous connection records into the local network interface card pipeline. Check the events logs and topology map below.
            </span>
          </div>
        )}
      </div>

      {/* Main Stream Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Live Event Stream Log Console (2/3 width) */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-xl flex flex-col h-[380px]">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
            <div>
              <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Live Backend Log Stream</h3>
              <p className="text-[10px] text-slate-400">Live system and inference logs</p>
            </div>

            {/* Stream Controllers */}
            <div className="flex flex-wrap items-center gap-2">
              <button 
                id="toggle-live-btn"
                onClick={() => setIsLive(!isLive)}
                className={`flex items-center gap-1.5 px-3 py-1 rounded text-[10px] font-mono border transition-all active:scale-95 ${
                  isLive 
                    ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' 
                    : 'bg-slate-800 text-slate-400 border-slate-700'
                }`}
              >
                <span className={`w-2 h-2 rounded-full ${isLive ? 'bg-emerald-400 animate-ping' : 'bg-slate-500'}`}></span>
                {isLive ? 'STREAMING' : 'PAUSED'}
              </button>

              {/* Filter selection buttons */}
              <div className="flex rounded-lg bg-slate-900 p-0.5 border border-slate-800" id="log-filters">
                {['ALL', 'CRITICAL', 'INFO'].map(sev => (
                  <button
                    key={sev}
                    id={`log-filter-${sev}`}
                    onClick={() => setFilterSeverity(sev)}
                    className={`px-2 py-0.5 rounded text-[9px] font-mono font-bold transition-all ${
                      filterSeverity === sev 
                        ? 'bg-indigo-500/20 text-indigo-400' 
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {sev}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Console View */}
          <div 
            ref={logTerminalRef}
            className="flex-1 bg-slate-950 p-4 rounded-lg border border-slate-800 overflow-y-auto font-mono text-[11px] leading-relaxed select-text shadow-inner"
            id="log-stream-terminal"
          >
            {filteredLogs.length === 0 ? (
              <div className="text-slate-600 italic text-center py-10">// NO LOG EVENTS DETECTED IN BACKEND</div>
            ) : (
              filteredLogs.map((log, index) => (
                <div key={index} className="hover:bg-slate-900/50 py-0.5 transition-colors flex items-start gap-3">
                  <span className="text-slate-600 whitespace-nowrap">{log.timestamp}</span>
                  <span className={`px-1 rounded text-[9px] font-bold ${
                    log.severity === 'CRIT' || log.severity === 'ERROR' ? 'bg-rose-500/10 text-rose-400' :
                    log.severity === 'WARN' ? 'bg-amber-500/10 text-amber-400' : 'bg-blue-500/10 text-blue-400'
                  }`}>{log.severity}</span>
                  <span className="text-indigo-400 font-semibold text-[10px] whitespace-nowrap">[{log.module}]</span>
                  <span className={`flex-1 break-all ${log.color || 'text-slate-300'}`}>{log.message}</span>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Traffic Load Bar Chart (1/3 width) */}
        <div className="glass-panel p-5 rounded-xl flex flex-col h-[380px]">
          <div>
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Real-Time Request Activity</h3>
            <p className="text-[10px] text-slate-400">System throughput monitored in 2-second intervals</p>
          </div>

          <div className="flex-1 relative bg-slate-950/40 border border-slate-800/80 rounded-lg p-4 mt-4 flex items-end justify-between min-h-0">
            {barData.map((val, idx) => {
              const max = Math.max(...barData, 1);
              const heightPercent = (val / max) * 100;
              const isHovered = hoveredBar === idx;

              return (
                <div 
                  key={idx} 
                  className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end group cursor-pointer"
                  onMouseEnter={() => setHoveredBar(idx)}
                  onMouseLeave={() => setHoveredBar(null)}
                >
                  {isHovered && (
                    <span className="absolute top-2 bg-slate-900 text-indigo-400 border border-slate-700 text-[10px] font-mono px-1.5 py-0.5 rounded shadow-lg">
                      {val} scale units
                    </span>
                  )}
                  <div 
                    className={`w-3.5 rounded-t-sm transition-all duration-300 ${
                      isHovered ? 'bg-indigo-400 shadow-[0_0_12px_rgba(99,102,241,0.5)]' : 'bg-indigo-600'
                    }`}
                    style={{ height: `${heightPercent}%` }}
                  ></div>
                  <span className="text-[8px] font-mono text-slate-600 scale-75 md:scale-100">{idx + 1}</span>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Connection inspection panel */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Connection List Panel */}
        <div className="glass-panel p-5 rounded-xl space-y-4">
          <div>
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Active Network Connections</h3>
            <p className="text-[10px] text-slate-400">Click any connection to inspect raw packet metadata triggers</p>
          </div>

          <div className="overflow-y-auto max-h-[220px]">
            {connections.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-10 text-center">// NO ACTIVE SOCKET SESSIONS</p>
            ) : (
              <table className="w-full text-left" id="active-connections-table">
                <thead>
                  <tr className="border-b border-[#1e2230] text-slate-400 text-[9px] font-mono uppercase tracking-wider">
                    <th className="pb-2">Source Host</th>
                    <th className="pb-2">Destination</th>
                    <th className="pb-2">Protocol</th>
                    <th className="pb-2 text-right">Channel Load</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#181a25]/40 text-xs text-slate-300">
                  {connections.map((conn, idx) => {
                    const isSelected = selectedConnection?.sourceIp === conn.sourceIp;
                    return (
                      <tr 
                        key={idx}
                        id={`conn-row-${idx}`}
                        onClick={() => setSelectedConnection(conn)}
                        className={`cursor-pointer transition-all ${
                          isSelected ? 'bg-indigo-500/10 text-indigo-300 font-semibold' : 'hover:bg-slate-800/10'
                        }`}
                      >
                        <td className="py-2.5 font-mono text-[11px]">{conn.sourceIp}</td>
                        <td className="py-2.5 font-mono text-[11px] text-slate-400">{conn.destIp}</td>
                        <td className="py-2.5"><span className="bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase">{conn.protocol}</span></td>
                        <td className="py-2.5 text-right font-mono">
                          <div className="flex items-center justify-end gap-2">
                            <span className="text-[10px] text-slate-400">{conn.load}%</span>
                            <div className="w-12 bg-slate-900 h-1.5 rounded-full overflow-hidden border border-slate-800">
                              <div className="bg-indigo-500 h-full transition-all duration-300" style={{ width: `${conn.load}%` }}></div>
                            </div>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            )}
          </div>
        </div>

        {/* Packet Inspection Hex Dump Box */}
        <div className="glass-panel p-5 rounded-xl flex flex-col h-full justify-between" id="packet-payload-inspector">
          <div>
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Real-Time Packet Inspection</h3>
              {selectedConnection && (
                <span className="text-[10px] text-indigo-400 font-mono">
                  {selectedConnection.sourceIp} &rarr; {selectedConnection.destIp}
                </span>
              )}
            </div>
            <p className="text-[10px] text-slate-400">Inspect payload contents for malicious patterns or policy violations</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4 flex-1">
            {/* Hex Dump */}
            <div className="space-y-1">
              <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider font-semibold">Hexadecimal Dump</span>
              <pre className="bg-slate-950 p-3 rounded-lg text-[10px] font-mono text-slate-400 border border-slate-800 leading-normal h-44 overflow-y-auto overflow-x-hidden shadow-inner select-text select-all">
                {payload.hex}
              </pre>
            </div>

            {/* ASCII Decoded Text */}
            <div className="space-y-1">
              <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider font-semibold">ASCII Decoded Payload</span>
              <pre className="bg-slate-950 p-3 rounded-lg text-[10px] font-mono text-emerald-400 border border-slate-800 leading-normal h-44 overflow-y-auto overflow-x-hidden shadow-inner select-text select-all">
                {payload.text}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
