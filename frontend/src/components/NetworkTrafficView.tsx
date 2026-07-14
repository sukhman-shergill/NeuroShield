import React, { useState, useEffect } from 'react';
import { TopologyNode } from '../types';

export default function NetworkTrafficView() {
  const [nodes, setNodes] = useState<TopologyNode[]>([]);
  const [selectedNode, setSelectedNode] = useState<TopologyNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [connections, setConnections] = useState<any[]>([]);
  const [topTalkers, setTopTalkers] = useState<any[]>([]);
  const [activeSubTab, setActiveSubTab] = useState<'topology' | 'sequences'>('topology');
  const [selectedSeqStep, setSelectedSeqStep] = useState<number>(7); // Default to step 8 (index 7)

  const mockSequenceSteps = [
    { step: 1, duration: 0, protocol: 'tcp', service: 'http', src_bytes: 232, dst_bytes: 815, count: 2, srv_count: 2, serror_rate: 0.0, rerror_rate: 0.0, label: 'Normal', attention: 0.02 },
    { step: 2, duration: 0, protocol: 'tcp', service: 'http', src_bytes: 228, dst_bytes: 920, count: 4, srv_count: 4, serror_rate: 0.0, rerror_rate: 0.0, label: 'Normal', attention: 0.03 },
    { step: 3, duration: 0, protocol: 'tcp', service: 'http', src_bytes: 230, dst_bytes: 840, count: 6, srv_count: 6, serror_rate: 0.0, rerror_rate: 0.0, label: 'Normal', attention: 0.03 },
    { step: 4, duration: 0, protocol: 'tcp', service: 'private', src_bytes: 0, dst_bytes: 0, count: 12, srv_count: 1, serror_rate: 0.5, rerror_rate: 0.0, label: 'Probe', attention: 0.06 },
    { step: 5, duration: 0, protocol: 'tcp', service: 'private', src_bytes: 0, dst_bytes: 0, count: 24, srv_count: 2, serror_rate: 0.8, rerror_rate: 0.0, label: 'Probe', attention: 0.09 },
    { step: 6, duration: 0, protocol: 'tcp', service: 'http', src_bytes: 0, dst_bytes: 0, count: 120, srv_count: 4, serror_rate: 1.0, rerror_rate: 0.0, label: 'DoS (Neptune)', attention: 0.12 },
    { step: 7, duration: 0, protocol: 'tcp', service: 'http', src_bytes: 0, dst_bytes: 0, count: 240, srv_count: 8, serror_rate: 1.0, rerror_rate: 0.0, label: 'DoS (Neptune)', attention: 0.15 },
    { step: 8, duration: 0, protocol: 'tcp', service: 'http', src_bytes: 0, dst_bytes: 0, count: 380, srv_count: 12, serror_rate: 1.0, rerror_rate: 0.0, label: 'DoS (Neptune)', attention: 0.22 },
    { step: 9, duration: 0, protocol: 'tcp', service: 'http', src_bytes: 0, dst_bytes: 0, count: 511, srv_count: 16, serror_rate: 1.0, rerror_rate: 0.0, label: 'DoS (Neptune)', attention: 0.18 },
    { step: 10, duration: 0, protocol: 'tcp', service: 'http', src_bytes: 0, dst_bytes: 0, count: 511, srv_count: 20, serror_rate: 1.0, rerror_rate: 0.0, label: 'DoS (Neptune)', attention: 0.10 },
  ];

  // Poll backend for dynamic topology mapping
  useEffect(() => {
    const fetchTopology = () => {
      fetch('/api/topology')
        .then(res => res.json())
        .then(data => {
          if (data.nodes && data.connections) {
            setNodes(prev => {
              return data.nodes.map((node: any) => {
                const existing = prev.find(n => n.id === node.id);
                // Keep existing coordinates for smooth float animation!
                if (existing) {
                  return { ...node, x: existing.x, y: existing.y };
                }
                return node;
              });
            });
            setConnections(data.connections);
            if (data.top_talkers) {
              setTopTalkers(data.top_talkers);
            }
          }
        })
        .catch(err => console.error('Topology fetch error:', err));
    };

    fetchTopology();
    const interval = setInterval(fetchTopology, 3000);
    return () => clearInterval(interval);
  }, []);

  // Float animation physics
  useEffect(() => {
    if (nodes.length === 0) return;
    const animationFrame = setInterval(() => {
      setNodes(prev => 
        prev.map(node => {
          // Keep core gateway stationary
          if (node.id === '2') return node;

          const dx = (Math.random() - 0.5) * 1.5;
          const dy = (Math.random() - 0.5) * 1.5;

          const nextX = Math.max(50, Math.min(750, node.x + dx));
          const nextY = Math.max(50, Math.min(350, node.y + dy));

          return { ...node, x: nextX, y: nextY };
        })
      );
    }, 150);

    return () => clearInterval(animationFrame);
  }, [nodes.length > 0]);

  // Synchronize selected node
  useEffect(() => {
    if (nodes.length > 0) {
      if (!selectedNode) {
        setSelectedNode(nodes.find(n => n.id === '2') || nodes[0]);
      } else {
        const updated = nodes.find(n => n.id === selectedNode.id);
        if (updated) setSelectedNode(updated);
      }
    }
  }, [nodes]);

  const getNodeColor = (type: string, isSelected: boolean) => {
    if (type === 'Threat') return isSelected ? '#f43f5e' : '#be123c';
    if (type === 'Gateway') return isSelected ? '#a5b4fc' : '#4f46e5';
    if (type === 'Server') return isSelected ? '#38bdf8' : '#0284c7';
    if (type === 'External') return isSelected ? '#fbbf24' : '#d97706';
    return isSelected ? '#34d399' : '#059669';
  };

  const protocolData = [
    { name: 'TCP Traffic', percentage: 76, color: 'bg-indigo-500' },
    { name: 'UDP Traffic', percentage: 18, color: 'bg-emerald-500' },
    { name: 'ICMP Traffic', percentage: 6, color: 'bg-amber-500' }
  ];

  return (
    <div id="network-traffic-root" className="space-y-6 font-sans">
      {/* Header Panel */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-[#1e2230] pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span className="material-symbols-outlined text-indigo-400">hub</span>
            Network Traffic Intelligence
          </h2>
          <p className="text-xs text-slate-400">Interactive live graph of active cluster routing and sliding window temporal network sequences</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex rounded-lg bg-slate-900 p-0.5 border border-slate-800" id="subtab-toggles">
            <button
              onClick={() => setActiveSubTab('topology')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold font-mono transition-all ${
                activeSubTab === 'topology'
                  ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200 border border-transparent'
              }`}
            >
              Topology Map
            </button>
            <button
              onClick={() => setActiveSubTab('sequences')}
              className={`px-3 py-1.5 rounded-lg text-xs font-bold font-mono transition-all ${
                activeSubTab === 'sequences'
                  ? 'bg-indigo-500/20 text-indigo-400 border border-indigo-500/30'
                  : 'text-slate-400 hover:text-slate-200 border border-transparent'
              }`}
            >
              Sequence Dashboard
            </button>
          </div>
        </div>
      </div>

      {activeSubTab === 'topology' ? (
        /* Main Interactive Topology Visualizer */
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Topology map box (3/4 width) */}
          <div className="lg:col-span-3 glass-panel p-5 rounded-xl flex flex-col h-[480px] relative overflow-hidden select-none">
            <div className="absolute top-4 left-4 z-10 space-y-1">
              <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Active Flow Topology Map</h3>
              <p className="text-[10px] text-slate-400">Click any system node to inspect connection details</p>
            </div>

            {/* Quick Graph Legends */}
            <div className="absolute top-4 right-4 z-10 flex items-center gap-3 text-[9px] font-mono">
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-[#4f46e5]"></span>Gateway</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-[#0284c7]"></span>Server</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-[#059669]"></span>Internal</span>
              <span className="flex items-center gap-1"><span className="w-2.5 h-2.5 rounded bg-[#be123c] animate-pulse"></span>Threat Source</span>
            </div>

            {/* Core SVG Topology Canvas */}
            <div className="flex-1 min-h-0 bg-slate-950/50 rounded-lg border border-slate-800/80 mt-10 relative">
              <svg className="w-full h-full" viewBox="0 0 800 400" id="topology-svg-canvas">
                {/* Draw Connections */}
                {connections.map((conn, idx) => {
                  const nodeFrom = nodes.find(n => n.id === conn.from);
                  const nodeTo = nodes.find(n => n.id === conn.to);
                  if (!nodeFrom || !nodeTo) return null;

                  const isThreat = conn.threat;
                  return (
                    <g key={idx} className="group">
                      <line
                        x1={nodeFrom.x}
                        y1={nodeFrom.y}
                        x2={nodeTo.x}
                        y2={nodeTo.y}
                        stroke={isThreat ? '#ef4444' : '#4f46e5'}
                        strokeWidth={isThreat ? '2.5' : '1.5'}
                        strokeOpacity={isThreat ? '0.7' : '0.4'}
                        strokeDasharray={isThreat ? '5,5' : 'none'}
                        className={isThreat ? 'animate-pulse' : ''}
                      />
                      <circle r={isThreat ? '3.5' : '2'} fill={isThreat ? '#ef4444' : '#818cf8'}>
                        <animateMotion
                          path={`M ${nodeFrom.x} ${nodeFrom.y} L ${nodeTo.x} ${nodeTo.y}`}
                          dur={isThreat ? "1s" : `${3 + Math.random() * 2}s`}
                          repeatCount="indefinite"
                        />
                      </circle>
                      <title>{`${nodeFrom.label.split(' ')[0]} to ${nodeTo.label.split(' ')[0]} (${conn.speed})`}</title>
                    </g>
                  );
                })}

                {/* Draw Nodes */}
                {nodes.map(node => {
                  const isSelected = selectedNode?.id === node.id;
                  const isHovered = hoveredNode === node.id;
                  const nodeColor = getNodeColor(node.type, isSelected || isHovered);

                  return (
                    <g
                      key={node.id}
                      id={`topo-node-${node.id}`}
                      transform={`translate(${node.x}, ${node.y})`}
                      className="cursor-pointer"
                      onClick={() => setSelectedNode(node)}
                      onMouseEnter={() => setHoveredNode(node.id)}
                      onMouseLeave={() => setHoveredNode(null)}
                    >
                      {node.type === 'Threat' && (
                        <circle r="22" fill="none" stroke="#ef4444" strokeWidth="1.5" className="animate-ping opacity-25" />
                      )}
                      <circle
                        r={isSelected ? "16" : "12"}
                        fill="#0c0e16"
                        stroke={nodeColor}
                        strokeWidth={isSelected ? "4" : "2.5"}
                        className="transition-all duration-300"
                      />
                      <text
                        textAnchor="middle"
                        dy="4"
                        fill={nodeColor}
                        fontSize="10px"
                        className="material-symbols-outlined select-none fill-icon pointer-events-none"
                      >
                        {node.type === 'Threat' ? 'gpp_maybe' : node.type === 'Gateway' ? 'router' : node.type === 'Server' ? 'dns' : 'laptop_mac'}
                      </text>
                      <text
                        textAnchor="middle"
                        y={isSelected ? "32" : "26"}
                        fill="#e2e8f0"
                        fontSize="9px"
                        fontWeight="600"
                        className="font-mono bg-slate-900 pointer-events-none drop-shadow-md select-none"
                      >
                        {node.label.split(' ')[0]}
                      </text>
                    </g>
                  );
                })}
              </svg>
            </div>
          </div>

          {/* Selected Node Details Side panel (1/4 width) */}
          <div className="glass-panel p-5 rounded-xl flex flex-col justify-between h-[480px]" id="topology-inspector-card">
            {selectedNode ? (
              <div className="space-y-4 flex-1 flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
                    <span className="material-symbols-outlined text-indigo-400">info</span>
                    <h4 className="text-xs font-bold text-slate-200 tracking-wider uppercase">Node Diagnostics</h4>
                  </div>
                  <div className="space-y-2 text-xs">
                    <div>
                      <p className="text-[10px] text-slate-500 font-mono">Assigned Hostname / Identity</p>
                      <p className="font-semibold text-slate-100 mt-0.5">{selectedNode.label}</p>
                    </div>
                    <div>
                      <p className="text-[10px] text-slate-500 font-mono">Platform Interface Role</p>
                      <span className={`inline-block px-2 py-0.5 rounded text-[9px] font-mono font-bold uppercase mt-1 ${
                        selectedNode.type === 'Threat' ? 'bg-rose-500/15 text-rose-400' :
                        selectedNode.type === 'Gateway' ? 'bg-indigo-500/15 text-indigo-400' :
                        'bg-blue-500/15 text-blue-400'
                      }`}>
                        {selectedNode.type}
                      </span>
                    </div>
                    <div className="grid grid-cols-2 gap-2 pt-1">
                      <div>
                        <p className="text-[10px] text-slate-500 font-mono">Socket Connections</p>
                        <p className="font-bold text-slate-200 font-mono mt-0.5">{selectedNode.activeConnections} Active</p>
                      </div>
                      <div>
                        <p className="text-[10px] text-slate-500 font-mono">Throughput Rate</p>
                        <p className="font-bold text-slate-200 font-mono mt-0.5">{selectedNode.trafficRate}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-950 p-4 rounded-lg border border-slate-900/60 flex flex-col items-center">
                  <span className="text-[9px] font-mono text-slate-500 uppercase tracking-widest mb-2">Node Capacity Indicator</span>
                  <div className="relative w-20 h-20">
                    <svg className="w-full h-full rotate-[-90deg]" viewBox="0 0 36 36">
                      <circle cx="18" cy="18" r="15.915" fill="none" stroke="#12151e" strokeWidth="3" />
                      <circle
                        cx="18"
                        cy="18"
                        r="15.915"
                        fill="none"
                        stroke={selectedNode.type === 'Threat' ? '#be123c' : '#6366f1'}
                        strokeWidth="3.5"
                        strokeDasharray={`${Math.min(100, selectedNode.activeConnections * 5)} ${100 - Math.min(100, selectedNode.activeConnections * 5)}`}
                        className="transition-all duration-300"
                      />
                    </svg>
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                      <span className="text-xs font-black text-slate-200">{Math.min(100, selectedNode.activeConnections * 5)}%</span>
                      <span className="text-[7px] text-slate-500 font-mono">LOAD</span>
                    </div>
                  </div>
                </div>

                <div className="text-[10px] text-slate-500 leading-normal bg-slate-900/20 p-2.5 rounded border border-slate-800/40">
                  <span className="font-bold text-slate-400 font-mono flex items-center gap-1 mb-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                    AI Security Assessment
                  </span>
                  {selectedNode.type === 'Threat' ? (
                    <span className="text-rose-400">Anomalous connection bursts matching intrusion weights detected on this external host. Recommended action: ISOLATE host.</span>
                  ) : (
                    <span>Normal operating thresholds. Heartbeat latency is within target metrics. No anomalous requests identified in active socket channels.</span>
                  )}
                </div>
              </div>
            ) : (
              <div className="text-slate-500 italic text-center py-20">// SELECT NODE TO VIEW DETAILS</div>
            )}
          </div>
        </div>
      ) : (
        /* CDAC Project Requirement: Temporal Sequence Visualization Dashboard */
        <div className="space-y-6 animate-fade-in" id="sequence-dashboard-view">
          {/* Step sliding window timeline */}
          <div className="glass-panel p-5 rounded-xl space-y-3">
            <div>
              <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Sliding Window Sequence Timeline</h3>
              <p className="text-[10px] text-slate-400">Inspect the 10 sequential packets inside the sliding window feed currently queued in the LSTM recurrent stack</p>
            </div>
            
            <div className="grid grid-cols-5 md:grid-cols-10 gap-2">
              {mockSequenceSteps.map((step, idx) => {
                const isSelected = selectedSeqStep === idx;
                const isThreat = step.label.includes('DoS') || step.label.includes('Probe');
                return (
                  <button
                    key={idx}
                    onClick={() => setSelectedSeqStep(idx)}
                    className={`p-3 rounded-lg border text-center transition-all ${
                      isSelected 
                        ? 'bg-indigo-500/15 border-indigo-500 text-indigo-200 font-bold shadow-lg ring-1 ring-indigo-500/30' 
                        : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <span className="text-[10px] font-mono block text-slate-500">STEP {step.step}</span>
                    <span className={`text-[11px] font-bold block mt-1 ${
                      step.label === 'Normal' ? 'text-emerald-400' : isThreat ? 'text-rose-400' : 'text-amber-400'
                    }`}>{step.label.split(' ')[0]}</span>
                    <span className="text-[9px] font-mono text-slate-500 block mt-1">Attn: {(step.attention * 100).toFixed(0)}%</span>
                  </button>
                );
              })}
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left: Spatial-Temporal Feature & Attention weights charts */}
            <div className="lg:col-span-2 space-y-6">
              {/* Attention Weights Bar Chart */}
              <div className="glass-panel p-5 rounded-xl space-y-4">
                <div>
                  <h4 className="text-xs font-bold text-slate-200 tracking-wide uppercase">LSTM Temporal Attention Weights</h4>
                  <p className="text-[10px] text-slate-400">Attention coefficients allocated to each step of the sliding sequence window by Bahdanau-style Attention layer</p>
                </div>
                
                <div className="h-40 flex items-end justify-between gap-3 px-2 pt-4 bg-slate-950/40 border border-slate-800/80 rounded-lg relative">
                  {mockSequenceSteps.map((step, idx) => {
                    const heightPercent = (step.attention / 0.25) * 100;
                    const isSelected = selectedSeqStep === idx;
                    return (
                      <div 
                        key={idx} 
                        className="flex-1 flex flex-col items-center h-full justify-end cursor-pointer group"
                        onClick={() => setSelectedSeqStep(idx)}
                      >
                        <span className="text-[9px] font-mono text-slate-400 mb-1 group-hover:text-indigo-400">
                          {(step.attention * 100).toFixed(0)}%
                        </span>
                        <div 
                          className={`w-full rounded-t-md transition-all duration-300 ${
                            isSelected 
                              ? 'bg-indigo-400 shadow-[0_0_12px_rgba(99,102,241,0.5)]' 
                              : 'bg-indigo-600/60 group-hover:bg-indigo-500/80'
                          }`}
                          style={{ height: `${heightPercent}%` }}
                        ></div>
                        <span className="text-[8px] font-mono text-slate-600 mt-1">S{step.step}</span>
                      </div>
                    );
                  })}
                </div>
                <p className="text-[10px] text-slate-500 leading-normal">
                  <strong className="text-indigo-400 font-mono">Attention Insight:</strong> The model focuses most heavily (<strong className="text-slate-300">22%</strong> weight) on <strong className="text-slate-300">Step 8</strong>, which is precisely where the connection request count surged to <code className="bg-slate-950 px-1 py-0.5 rounded text-indigo-300 font-mono">380</code> and the serror_rate hit <code className="bg-slate-950 px-1 py-0.5 rounded text-rose-300 font-mono">1.0</code>, marking the onset of the DOS attack.
                </p>
              </div>

              {/* CNN Spatial Activations Heatmap */}
              <div className="glass-panel p-5 rounded-xl space-y-4">
                <div>
                  <h4 className="text-xs font-bold text-slate-200 tracking-wide uppercase">CNN Spatial Feature Activation Heatmap</h4>
                  <p className="text-[10px] text-slate-400">Visual mapping of feature matching activation layers in 1D Convolution blocks (Filters: 128)</p>
                </div>

                <div className="grid grid-cols-12 gap-1.5 p-3 bg-slate-950/60 rounded-lg border border-slate-800">
                  {Array.from({ length: 60 }).map((_, idx) => {
                    const stepIdx = idx % 10;
                    const isSelectedStep = selectedSeqStep === stepIdx;
                    const isThreat = mockSequenceSteps[stepIdx].label !== 'Normal';
                    let intensity = 0.1 + (idx * 37 % 50) / 100;
                    if (isThreat) intensity += 0.4;
                    if (isSelectedStep) intensity = Math.min(1.0, intensity + 0.15);

                    return (
                      <div
                        key={idx}
                        className={`aspect-square rounded transition-all ${
                          isSelectedStep ? 'ring-1 ring-slate-100 scale-105' : 'opacity-80'
                        }`}
                        style={{
                          backgroundColor: `rgba(99, 102, 241, ${intensity})`
                        }}
                        title={`Layer Activation: ${(intensity * 100).toFixed(0)}%`}
                      />
                    );
                  })}
                </div>
                <div className="flex items-center justify-between text-[9px] font-mono text-slate-500">
                  <span>← LOW CONVOLUTION ACTIVATION</span>
                  <span>HIGH CONVOLUTION ACTIVATION →</span>
                </div>
              </div>
            </div>

            {/* Right: Selected Step's detailed tabular NSL-KDD features */}
            <div className="glass-panel p-5 rounded-xl flex flex-col justify-between h-full min-h-[460px]">
              <div className="space-y-4">
                <div className="flex items-center gap-2 pb-2 border-b border-slate-800">
                  <span className="material-symbols-outlined text-indigo-400">list_alt</span>
                  <h4 className="text-xs font-bold text-slate-200 tracking-wider uppercase">Sequence Feature Dump</h4>
                </div>
                
                <div className="space-y-2 text-xs font-mono">
                  <div className="flex justify-between py-1.5 border-b border-slate-800/40">
                    <span className="text-slate-500">Timeline Position</span>
                    <span className="text-slate-300 font-bold">Step {mockSequenceSteps[selectedSeqStep].step} of 10</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800/40">
                    <span className="text-slate-500">Feature: duration</span>
                    <span className="text-slate-300">{mockSequenceSteps[selectedSeqStep].duration}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800/40">
                    <span className="text-slate-500">Feature: protocol_type</span>
                    <span className="text-indigo-400 font-bold">{mockSequenceSteps[selectedSeqStep].protocol.toUpperCase()}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800/40">
                    <span className="text-slate-500">Feature: service</span>
                    <span className="text-slate-300">{mockSequenceSteps[selectedSeqStep].service}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800/40">
                    <span className="text-slate-500">Feature: src_bytes</span>
                    <span className="text-slate-300">{mockSequenceSteps[selectedSeqStep].src_bytes}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800/40">
                    <span className="text-slate-500">Feature: dst_bytes</span>
                    <span className="text-slate-300">{mockSequenceSteps[selectedSeqStep].dst_bytes}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800/40">
                    <span className="text-slate-500">Feature: count</span>
                    <span className="text-slate-300">{mockSequenceSteps[selectedSeqStep].count}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800/40">
                    <span className="text-slate-500">Feature: srv_count</span>
                    <span className="text-slate-300">{mockSequenceSteps[selectedSeqStep].srv_count}</span>
                  </div>
                  <div className="flex justify-between py-1.5 border-b border-slate-800/40">
                    <span className="text-slate-500">Feature: serror_rate</span>
                    <span className={mockSequenceSteps[selectedSeqStep].serror_rate > 0.5 ? 'text-rose-400 font-bold' : 'text-slate-300'}>
                      {mockSequenceSteps[selectedSeqStep].serror_rate.toFixed(2)}
                    </span>
                  </div>
                  <div className="flex justify-between py-1.5">
                    <span className="text-slate-500">Feature: rerror_rate</span>
                    <span className="text-slate-300">{mockSequenceSteps[selectedSeqStep].rerror_rate.toFixed(2)}</span>
                  </div>
                </div>
              </div>

              <div className="bg-[#121520] p-3 rounded-lg border border-slate-800 text-[10px] text-slate-400 font-sans mt-4">
                <strong className="text-indigo-400 font-mono block mb-1">Spatial-Temporal Fusion</strong>
                CNN convolutions learn spatial features from individual packets, while LSTM tracks their progression over the sliding window. The Attention weight displays how much focus the model placed on each packet to reach its final classification.
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Protocol Mix and Top Bandwidth Talkers row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Protocol Mix Bar List */}
        <div className="glass-panel p-5 rounded-xl space-y-4">
          <div>
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Protocol Mix</h3>
            <p className="text-[10px] text-slate-400">Distribution of network transport classes across cluster</p>
          </div>

          <div className="space-y-4" id="protocol-mix-list">
            {protocolData.map(prot => (
              <div key={prot.name} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="text-slate-300 font-medium">{prot.name}</span>
                  <span className="font-mono text-indigo-400 font-bold">{prot.percentage}%</span>
                </div>
                <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
                  <div className={`${prot.color} h-full rounded-full transition-all duration-500`} style={{ width: `${prot.percentage}%` }}></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Talkers */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-xl space-y-3">
          <div>
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Highest Traffic Talkers</h3>
            <p className="text-[10px] text-slate-400">Network endpoints transmitting the highest byte counts over past hour</p>
          </div>

          <div className="overflow-x-auto">
            {topTalkers.length === 0 ? (
              <p className="text-xs text-slate-500 italic py-10 text-center">// NO BANDWIDTH ENDPOINTS ACTIVE</p>
            ) : (
              <table className="w-full text-left" id="top-talkers-table">
                <thead>
                  <tr className="border-b border-[#1e2230] text-slate-400 text-[9px] font-mono uppercase tracking-wider">
                    <th className="pb-2">Source Machine</th>
                    <th className="pb-2">Target Host</th>
                    <th className="pb-2 text-right">Packets Sent</th>
                    <th className="pb-2 text-right">Bandwidth Used</th>
                    <th className="pb-2 text-center">Threat Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#181a25]/40 text-xs text-slate-300">
                  {topTalkers.map((talker, idx) => (
                    <tr key={idx} className="hover:bg-slate-800/10 transition-colors">
                      <td className="py-2.5 font-mono">
                        <div className="flex flex-col">
                          <span className="font-semibold text-slate-100">{talker.sourceIp}</span>
                          <span className="text-[9px] text-slate-500 font-sans">({talker.sourceLabel})</span>
                        </div>
                      </td>
                      <td className="py-2.5 font-mono">
                        <div className="flex flex-col">
                          <span className="text-slate-300">{talker.destIp}</span>
                          <span className="text-[9px] text-slate-500 font-sans">({talker.destLabel})</span>
                        </div>
                      </td>
                      <td className="py-2.5 text-right font-mono text-slate-400">{talker.packets}</td>
                      <td className="py-2.5 text-right font-mono font-bold text-indigo-400">{talker.bandwidth}</td>
                      <td className="py-2.5 text-center">
                        <span className={`px-2 py-0.5 rounded-full text-[9px] font-mono font-bold uppercase ring-1 ${talker.statusColor}`}>
                          {talker.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
