import React, { useState } from 'react';

export default function AIPredictionsView() {
  const [modelThreshold, setModelThreshold] = useState(0.85);
  const [gpuAccelerate, setGpuAccelerate] = useState(true);
  const [activeModel, setActiveModel] = useState('CNN-LSTM-V4.2');
  const [isUploading, setIsUploading] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisStep, setAnalysisStep] = useState(0);
  const [fileName, setFileName] = useState<string | null>(null);
  
  // Custom states that update when a custom file is loaded
  const [predictionResult, setPredictionResult] = useState({
    classification: 'DDoS (TCP SYN Flood)',
    confidence: 96.8,
    status: 'Critical Alert',
    badgeColor: 'bg-rose-500/15 text-rose-400 border border-rose-500/30',
    description: 'Volumetric connection saturation detected on port 443. High-rate packet signatures match known Mirai botnet handshake profiles.'
  });

  const [probabilities, setProbabilities] = useState([
    { label: 'DDoS TCP Flood', value: 96.8, color: 'bg-rose-500' },
    { label: 'SQL Injection', value: 2.1, color: 'bg-slate-700' },
    { label: 'SSH Brute Force', value: 0.8, color: 'bg-slate-700' },
    { label: 'Normal Traffic', value: 0.3, color: 'bg-slate-700' }
  ]);

  const [fileResults, setFileResults] = useState<any[]>([]);
  const [selectedRecordIdx, setSelectedRecordIdx] = useState<number>(0);
  const [batchSummary, setBatchSummary] = useState<any | null>(null);

  const analysisLogSteps = [
    'Parsing file header block and validating byte boundaries...',
    'Running CNN spatial convolution layers on payload structures...',
    'Running sequence through LSTM layers...',
    'Normalizing final probability layer scores against threshold...'
  ];

  // Drag and Drop simulation
  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      const file = files[0];
      const isCsv = file.name.toLowerCase().endsWith('.csv') || file.name.toLowerCase().endsWith('.txt');
      if (isCsv) {
        uploadFile(file);
      } else {
        alert('Please upload a valid CSV or TXT file with UNSW-NB15 network features.');
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      const file = files[0];
      const isCsv = file.name.toLowerCase().endsWith('.csv') || file.name.toLowerCase().endsWith('.txt');
      if (isCsv) {
        uploadFile(file);
      } else {
        alert('Please upload a valid CSV or TXT file with UNSW-NB15 network features.');
      }
    }
  };

  const uploadFile = (file: File) => {
    setFileName(file.name);
    setIsUploading(true);
    setIsAnalyzing(false);
    setFileResults([]);
    setBatchSummary(null);

    const formData = new FormData();
    formData.append('file', file);

    fetch('/api/predict/file', {
      method: 'POST',
      body: formData,
    })
      .then(res => res.json())
      .then(data => {
        setIsUploading(false);
        if (data.status === 'success') {
          setIsAnalyzing(true);
          setAnalysisStep(0);

          let step = 0;
          const interval = setInterval(() => {
            if (step >= analysisLogSteps.length - 1) {
              clearInterval(interval);
              setIsAnalyzing(false);
              const predictions = data.predictions;
              setFileResults(predictions);
              setBatchSummary(data.summary);
              setSelectedRecordIdx(0);
              updateViewWithPrediction(predictions, 0);
            } else {
              step++;
              setAnalysisStep(step);
            }
          }, 600);
        } else {
          alert('Error during prediction: ' + (data.message || data.error));
        }
      })
      .catch(err => {
        setIsUploading(false);
        console.error('API Error:', err);
        alert('Could not connect to Flask API server. Make sure it is running on port 5000.');
      });
  };

  const updateViewWithPrediction = (predictions: any[], index: number) => {
    if (!predictions || predictions.length === 0) return;
    const pred = predictions[index];
    const category = pred.predicted_class;
    const conf = pred.confidence * 100;

    let status = 'Normal';
    let badgeColor = 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30';
    let description = 'Zero malicious vectors flagged. Internal socket queues and handshake profiles match standard web request baselines safely.';

    if (category === 'DoS') {
      status = 'Critical Alert';
      badgeColor = 'bg-rose-500/15 text-rose-400 border border-rose-500/30';
      description = `Denial of Service (DoS) attack signature identified with high confidence (${conf.toFixed(1)}%). Recommended action: rate-limit or block incoming packets from this source host immediately.`;
    } else if (category === 'Probe') {
      status = 'High Severity';
      badgeColor = 'bg-amber-500/15 text-amber-400 border border-amber-500/30';
      description = `Reconnaissance probing / network scanning behavior identified (${conf.toFixed(1)}%). Port scan vectors or host sweeps were recognized from the source host.`;
    } else if (category === 'R2L') {
      status = 'High Severity';
      badgeColor = 'bg-amber-500/15 text-amber-400 border border-amber-500/30';
      description = `Remote-to-Local (R2L) unauthorized access attempt recognized (${conf.toFixed(1)}%). Handshake anomalies match known brute-force login or credential access vectors.`;
    } else if (category === 'U2R') {
      status = 'Critical Alert';
      badgeColor = 'bg-rose-500/15 text-rose-400 border border-rose-500/30';
      description = `User-to-Root (U2R) local privilege escalation exploit vector flagged (${conf.toFixed(1)}%). Critical administrative privilege escalation attempts were detected.`;
    }

    setPredictionResult({
      classification: `${category} Intrusion Vector`,
      confidence: conf,
      status: status,
      badgeColor: badgeColor,
      description: description
    });

    const probs = pred.all_probabilities;
    const colorMap: Record<string, string> = {
      Normal: 'bg-emerald-500',
      DoS: 'bg-rose-500',
      Probe: 'bg-amber-500',
      R2L: 'bg-blue-500',
      U2R: 'bg-purple-500'
    };

    const probArray = Object.keys(probs).map(key => ({
      label: `${key} Class`,
      value: probs[key] * 100,
      color: colorMap[key] || 'bg-slate-700'
    })).sort((a, b) => b.value - a.value);

    setProbabilities(probArray);
  };

  return (
    <div id="ai-predictions-root" className="space-y-6 font-sans">
      {/* Header Panel */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-[#1e2230] pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span className="material-symbols-outlined text-indigo-400">psychology</span>
            CNN-LSTM AI Prediction Engine
          </h2>
          <p className="text-xs text-slate-400">Classify network connection records using deep recurrent convolution weights</p>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className="text-slate-500">Acceleration Core:</span>
          <span className="text-emerald-400 font-bold">CUDA / TensorRT Enabled</span>
        </div>
      </div>

      {/* Model Parameter Configuration Bar */}
      <div className="glass-panel p-4 rounded-xl grid grid-cols-1 md:grid-cols-3 gap-6 items-center" id="model-config-bar">
        {/* Model Version Dropdown */}
        <div className="space-y-1.5">
          <label className="text-[10px] font-mono text-slate-500 uppercase tracking-widest block">Inference Weight Model</label>
          <select 
            id="weight-model-select"
            value={activeModel} 
            onChange={(e) => setActiveModel(e.target.value)}
            className="w-full bg-slate-950/60 border border-slate-800 text-xs text-slate-300 px-3 py-2 rounded-lg focus:outline-none focus:border-indigo-500 font-mono"
          >
            <option value="CNN-LSTM-V4.2">Aegis CNN-LSTM Enterprise (v4.2.0)</option>
            <option value="ResNet-GRU-V1.8">ResNet-GRU Lightweight (v1.8.5)</option>
            <option value="Transformer-IDS-V1.0">Transformer Multihead (v1.0.1)</option>
          </select>
        </div>

        {/* Confidence Threshold slider */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-[10px] font-mono text-slate-500 uppercase tracking-widest">
            <span>Detection Confidence Threshold</span>
            <span className="text-indigo-400 font-bold">{(modelThreshold * 100).toFixed(0)}%</span>
          </div>
          <input
            id="threshold-range-slider"
            type="range"
            min="0.5"
            max="0.99"
            step="0.01"
            value={modelThreshold}
            onChange={(e) => setModelThreshold(parseFloat(e.target.value))}
            className="w-full h-1 bg-slate-950 rounded-lg appearance-none cursor-pointer accent-indigo-500"
          />
        </div>

        {/* Acceleration Toggle */}
        <div className="flex items-center justify-between md:justify-end gap-3 pt-3 md:pt-0">
          <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">Hardware Acceleration</span>
          <button
            id="gpu-accelerate-toggle"
            onClick={() => setGpuAccelerate(!gpuAccelerate)}
            className={`w-12 h-6 rounded-full p-0.5 transition-colors duration-200 focus:outline-none ${
              gpuAccelerate ? 'bg-indigo-600' : 'bg-slate-900 border border-slate-800'
            }`}
          >
            <div className={`w-5 h-5 rounded-full bg-slate-100 shadow-md transform transition-transform duration-200 ${
              gpuAccelerate ? 'translate-x-6' : 'translate-x-0'
            }`}></div>
          </button>
        </div>
      </div>

      {/* Main Analysis Section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column: Drag & Drop Area */}
        <div className="glass-panel p-5 rounded-xl flex flex-col h-[360px] justify-between">
          <div className="space-y-1">
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Ingest Traffic Feature Data</h3>
            <p className="text-[10px] text-slate-400">Upload UNSW-NB15 formatted CSV files for batch model inference</p>
          </div>

          {/* Interactive Drag Drop stage */}
          <div
            id="pcap-drop-zone"
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            className="flex-1 border-2 border-dashed border-slate-800/80 rounded-lg mt-4 flex flex-col items-center justify-center p-6 text-center hover:border-indigo-500/60 hover:bg-slate-900/10 transition-colors cursor-pointer relative"
          >
            <input
              id="file-upload-input"
              type="file"
              accept=".csv,.txt"
              onChange={handleFileChange}
              className="absolute inset-0 opacity-0 cursor-pointer"
            />
            
            {isUploading ? (
              <div className="space-y-3 animate-pulse">
                <span className="material-symbols-outlined text-4xl text-indigo-400 fill-icon">cloud_upload</span>
                <p className="text-xs font-bold text-slate-200 font-mono">UPLOADING DATA FILE...</p>
                <p className="text-[10px] text-slate-400 truncate max-w-[180px]">{fileName}</p>
              </div>
            ) : isAnalyzing ? (
              <div className="space-y-3">
                <span className="material-symbols-outlined text-4xl text-indigo-400 fill-icon animate-spin">sync</span>
                <p className="text-xs font-bold text-slate-200 font-mono">MODEL INFERENCE RUNNING...</p>
                <p className="text-[9px] text-indigo-400 font-mono italic max-w-[200px] leading-relaxed">
                  {analysisLogSteps[analysisStep]}
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                <span className="material-symbols-outlined text-4xl text-slate-500 group-hover:text-indigo-400">file_upload</span>
                <div>
                  <p className="text-xs font-bold text-slate-300">Drag & drop feature table here</p>
                  <p className="text-[10px] text-slate-500 mt-1">Supports standard UNSW-NB15 CSV/TXT tables</p>
                </div>
                {fileName && (
                  <div className="bg-slate-950 px-2 py-1 rounded text-[10px] font-mono text-indigo-400 border border-slate-800 inline-block max-w-[180px] truncate">
                    Loaded: {fileName}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Right Column: AI Output Diagnostic Card (2/3 width) */}
        <div className="lg:col-span-2 glass-panel p-5 rounded-xl flex flex-col h-[360px] justify-between" id="prediction-result-panel">
          <div className="flex items-center justify-between pb-3 border-b border-slate-800">
            <div>
              <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Model Diagnostic Report</h3>
              <p className="text-[10px] text-slate-400">Classified probability maps and mitigation suggestions</p>
            </div>
            {isAnalyzing ? (
              <span className="text-xs font-mono text-amber-400 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/20 animate-pulse">CLASSIFYING...</span>
            ) : (
              <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20">REPORT READY</span>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 flex-1 mt-4 items-center">
            {/* Radial Confidence score */}
            <div className="flex flex-col items-center justify-center space-y-2">
              <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest">Model Confidence</span>
              <div className="relative w-28 h-28">
                <svg className="w-full h-full rotate-[-90deg]" viewBox="0 0 36 36">
                  <circle cx="18" cy="18" r="15.915" fill="none" stroke="#12151e" strokeWidth="3.5" />
                  <circle
                    cx="18"
                    cy="18"
                    r="15.915"
                    fill="none"
                    stroke={predictionResult.confidence > 90 ? '#f43f5e' : '#6366f1'}
                    strokeWidth="4"
                    strokeDasharray={`${predictionResult.confidence} ${100 - predictionResult.confidence}`}
                    className="transition-all duration-1000 ease-out"
                  />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className="text-lg font-black text-slate-200">{predictionResult.confidence.toFixed(1)}%</span>
                  <span className="text-[8px] text-slate-500 font-mono">MATCH SCORE</span>
                </div>
              </div>
            </div>

            {/* Classification Result Card */}
            <div className="md:col-span-2 bg-slate-950/60 p-4 rounded-xl border border-slate-800/80 h-full flex flex-col justify-between" id="diagnosis-result-card">
              <div className="space-y-1.5">
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-0.5 rounded-full text-[9px] font-mono font-bold uppercase ${predictionResult.badgeColor}`}>
                    {predictionResult.status}
                  </span>
                  <span className="text-[10px] font-mono text-slate-500">MODEL: {activeModel}</span>
                </div>
                <h4 className="text-sm font-bold text-slate-100 tracking-tight" id="predicted-attack-label">{predictionResult.classification}</h4>
                <p className="text-xs text-slate-400 leading-relaxed" id="predicted-attack-desc">{predictionResult.description}</p>
              </div>

              <div className="flex gap-2 pt-3 border-t border-slate-900" id="diagnosis-actions">
                <button 
                  id="diag-isolate-host-btn"
                  onClick={() => alert(`Isolating simulated threat host for classification: ${predictionResult.classification}`)}
                  className="bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/20 px-3.5 py-1.5 rounded text-[10px] font-mono transition-all active:scale-95"
                >
                  ISOLATE HOST
                </button>
                <button 
                  id="diag-ignore-vector-btn"
                  onClick={() => alert(`Vector disregarded`)}
                  className="bg-slate-800 hover:bg-slate-700 text-slate-300 border border-slate-700 px-3 py-1.5 rounded text-[10px] font-mono transition-all active:scale-95"
                >
                  DISREGARD
                </button>
              </div>
            </div>
          </div>

          {/* Probability Distribution bars */}
          <div className="mt-4 border-t border-slate-900 pt-3 flex flex-col md:flex-row gap-4 items-center justify-between" id="probability-distribution-bars">
            <span className="text-[10px] font-mono text-slate-500 uppercase tracking-widest shrink-0">Class Probabilities</span>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 w-full">
              {probabilities.map(prob => (
                <div key={prob.label} className="space-y-1">
                  <div className="flex justify-between text-[10px]">
                    <span className="text-slate-400 truncate max-w-[80px]">{prob.label}</span>
                    <span className="font-mono text-indigo-400 font-bold">{prob.value.toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-slate-900 h-1.5 rounded-full overflow-hidden border border-slate-800">
                    <div className={`${prob.color} h-full rounded-full transition-all duration-1000`} style={{ width: `${prob.value}%` }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>

      {fileResults.length > 0 && (
        <div className="glass-panel p-5 rounded-xl mt-6 animate-fade-in" id="batch-results-catalog">
          <div className="flex items-center justify-between mb-4 border-b border-[#1e2230] pb-3">
            <div>
              <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Batch Classification Log ({fileResults.length} records)</h3>
              <p className="text-[10px] text-slate-400">Click any row to load its detailed features and class probabilities in the diagnostic panel</p>
            </div>
            {batchSummary && (
              <span className="text-xs font-mono text-emerald-400 bg-emerald-500/10 px-2 py-0.5 rounded border border-emerald-500/20 font-bold">
                {batchSummary.accuracy !== undefined ? `Batch Accuracy: ${(batchSummary.accuracy * 100).toFixed(1)}%` : 'Batch Predict Completed'}
              </span>
            )}
          </div>
          <div className="overflow-y-auto max-h-[300px]">
            <table className="w-full text-left">
              <thead>
                <tr className="border-b border-[#1e2230] text-slate-400 text-[10px] font-mono uppercase tracking-wider">
                  <th className="pb-2">Index</th>
                  <th className="pb-2">Actual Class (Ground Truth)</th>
                  <th className="pb-2">Predicted Class</th>
                  <th className="pb-2 text-right">Confidence Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#181a25]/40 text-xs text-slate-300">
                {fileResults.map((record, idx) => {
                  const isSelected = selectedRecordIdx === idx;
                  const isCorrect = record.actual_class ? record.predicted_class === record.actual_class : true;
                  return (
                    <tr 
                      key={idx} 
                      onClick={() => {
                        setSelectedRecordIdx(idx);
                        updateViewWithPrediction(fileResults, idx);
                      }}
                      className={`cursor-pointer hover:bg-slate-800/10 transition-colors ${isSelected ? 'bg-indigo-500/10 text-indigo-300 font-semibold' : ''}`}
                    >
                      <td className="py-2 font-mono text-[10px]">{idx + 1}</td>
                      <td className="py-2 font-mono text-[10px]">
                        {record.actual_class ? (
                          <span className={isCorrect ? 'text-emerald-400' : 'text-rose-400'}>
                            {record.actual_class}
                          </span>
                        ) : 'N/A'}
                      </td>
                      <td className="py-2">
                        <span className={`px-1.5 py-0.5 rounded text-[9px] font-mono font-bold uppercase ${
                          record.predicted_class === 'Normal' ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/20' : 
                          record.predicted_class === 'DoS' ? 'bg-rose-500/15 text-rose-400 border border-rose-500/20' :
                          record.predicted_class === 'Probe' ? 'bg-amber-500/15 text-amber-400 border border-amber-500/20' :
                          record.predicted_class === 'R2L' ? 'bg-blue-500/15 text-blue-400 border border-blue-500/20' :
                          'bg-purple-500/15 text-purple-400 border border-purple-500/20'
                        }`}>
                          {record.predicted_class}
                        </span>
                      </td>
                      <td className="py-2 text-right font-mono text-slate-200">{(record.confidence * 100).toFixed(1)}%</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
