import React, { useState, useEffect } from 'react';

interface ClassMetrics {
  precision: number;
  recall: number;
  'f1-score': number;
  support: number;
}

interface ConfusionMatrixData {
  matrix: number[][];
  normalized_matrix: number[][];
  labels: string[];
}

interface ArchitectureData {
  model_name: string;
  cnn_block: any;
  lstm_block: any;
  attention: any;
  classification_head: any;
  training: any;
}

export default function ModelPerformanceView() {
  const [modelInfo, setModelInfo] = useState<any>(null);
  const [classReport, setClassReport] = useState<Record<string, ClassMetrics> | null>(null);
  const [overallAccuracy, setOverallAccuracy] = useState<number | null>(null);
  const [weightedF1, setWeightedF1] = useState<number | null>(null);
  const [confusionMatrix, setConfusionMatrix] = useState<ConfusionMatrixData | null>(null);
  const [rocCurves, setRocCurves] = useState<Record<string, { auc: number }> | null>(null);
  const [attackDist, setAttackDist] = useState<any>(null);
  const [architecture, setArchitecture] = useState<ArchitectureData | null>(null);
  const [loading, setLoading] = useState(true);

  const classNames = ['Normal', 'DoS', 'Probe', 'R2L', 'U2R'];
  const classColors: Record<string, string> = {
    Normal: '#10b981', DoS: '#f43f5e', Probe: '#f59e0b', R2L: '#3b82f6', U2R: '#a855f7'
  };

  useEffect(() => {
    const fetchAll = async () => {
      try {
        const [infoRes, evalRes, archRes] = await Promise.all([
          fetch('/api/model/info'),
          fetch('/api/evaluation'),
          fetch('/api/model/architecture'),
        ]);

        const infoData = await infoRes.json();
        if (infoData.status === 'success') {
          setModelInfo(infoData.model_info);
          const report = infoData.classification_report;
          if (report) {
            setOverallAccuracy(report.overall_accuracy || report.accuracy);
            setWeightedF1(report.weighted_f1 || (report['weighted avg'] && report['weighted avg']['f1-score']));
            const classMetrics: Record<string, ClassMetrics> = {};
            for (const cls of classNames) {
              if (report[cls]) classMetrics[cls] = report[cls];
            }
            setClassReport(classMetrics);
          }
        }

        if (evalRes.ok) {
          const evalData = await evalRes.json();
          if (evalData.confusion_matrix) setConfusionMatrix(evalData.confusion_matrix);
          if (evalData.roc_curves) setRocCurves(evalData.roc_curves);
          if (evalData.attack_distribution) setAttackDist(evalData.attack_distribution);
        }

        const archData = await archRes.json();
        if (archData.status === 'success') {
          setArchitecture(archData.architecture);
        }
      } catch (err) {
        console.error('Error fetching model data:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, []);

  // Helper: draw a simple bar chart in SVG
  const renderBarChart = (values: number[], labels: string[], colors: string[], maxVal: number, height = 120, width = 400) => {
    const barWidth = width / (values.length * 2 + 1);
    const gap = barWidth;

    return (
      <svg className="w-full" viewBox={`0 0 ${width} ${height + 20}`} preserveAspectRatio="xMidYMid meet">
        {/* Grid lines */}
        {[0.25, 0.5, 0.75, 1.0].map(frac => (
          <line key={frac} x1="0" y1={height - frac * height} x2={width} y2={height - frac * height} stroke="#1e293b" strokeWidth="0.5" strokeDasharray="3,3" />
        ))}

        {values.map((val, idx) => {
          const barH = (val / maxVal) * height;
          const x = gap + idx * (barWidth + gap);
          return (
            <g key={idx}>
              <rect x={x} y={height - barH} width={barWidth} height={barH} fill={colors[idx]} rx="2" opacity="0.85" />
              <text x={x + barWidth / 2} y={height - barH - 4} textAnchor="middle" fill="#94a3b8" fontSize="8" fontFamily="monospace">{val.toFixed(2)}</text>
              <text x={x + barWidth / 2} y={height + 12} textAnchor="middle" fill="#64748b" fontSize="7" fontFamily="monospace">{labels[idx]}</text>
            </g>
          );
        })}
      </svg>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center space-y-3">
          <span className="material-symbols-outlined text-4xl text-indigo-400 animate-spin">sync</span>
          <p className="text-xs text-slate-400 font-mono">LOADING MODEL METRICS...</p>
        </div>
      </div>
    );
  }

  return (
    <div id="model-performance-root" className="space-y-6 font-sans">
      {/* Header */}
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-4 border-b border-[#1e2230] pb-4">
        <div>
          <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2">
            <span className="material-symbols-outlined text-indigo-400 fill-icon">insights</span>
            Model Performance Analytics
          </h2>
          <p className="text-xs text-slate-400">Evaluation metrics from trained CNN-LSTM-Attention intrusion detection model</p>
        </div>
        <div className="flex items-center gap-3">
          {overallAccuracy !== null && (
            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-xs font-mono font-bold">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              ACC: {(overallAccuracy * 100).toFixed(1)}%
            </span>
          )}
          {weightedF1 !== null && (
            <span className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 text-xs font-mono font-bold">
              F1: {(weightedF1 * 100).toFixed(1)}%
            </span>
          )}
        </div>
      </div>

      {/* Colab Training Info Banner */}
      <div className="bg-[#12151f] border-l-4 border-indigo-500/80 p-4 rounded-r-xl border border-slate-800/80">
        <h4 className="text-xs font-bold text-slate-200 uppercase tracking-wide flex items-center gap-1.5 font-mono">
          <span className="material-symbols-outlined text-indigo-400 text-sm fill-icon">school</span>
          Training Pipeline — Google Colab
        </h4>
        <p className="text-[11px] text-slate-400 leading-relaxed mt-1">
          This model was trained using <code className="bg-slate-950 px-1 py-0.5 rounded font-mono text-indigo-300">Hybrid_CNN_LSTM_Training.ipynb</code> on
          the UNSW-NB15 dataset.
          {modelInfo && (
            <span> Trained for <strong className="text-slate-300">{modelInfo.total_epochs_trained} epochs</strong> in <strong className="text-slate-300">{Math.round(modelInfo.training_time_seconds)}s</strong> on <strong className="text-slate-300">{modelInfo.trained_at?.split('T')[0]}</strong>.</span>
          )}
        </p>
      </div>

      {/* Top Metrics Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4" id="model-metric-cards">
        <div className="glass-card p-4 rounded-xl">
          <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider block">Overall Accuracy</span>
          <p className="text-2xl font-black text-emerald-400 font-mono mt-1">{overallAccuracy !== null ? (overallAccuracy * 100).toFixed(1) + '%' : '—'}</p>
        </div>
        <div className="glass-card p-4 rounded-xl">
          <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider block">Weighted F1-Score</span>
          <p className="text-2xl font-black text-indigo-400 font-mono mt-1">{weightedF1 !== null ? (weightedF1 * 100).toFixed(1) + '%' : '—'}</p>
        </div>
        <div className="glass-card p-4 rounded-xl">
          <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider block">Input Shape</span>
          <p className="text-2xl font-black text-slate-200 font-mono mt-1">{modelInfo ? `${modelInfo.input_shape[0]}×${modelInfo.input_shape[1]}` : '—'}</p>
          <span className="text-[8px] text-slate-500 font-mono">(seq_len × features)</span>
        </div>
        <div className="glass-card p-4 rounded-xl">
          <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider block">Output Classes</span>
          <p className="text-2xl font-black text-slate-200 font-mono mt-1">{modelInfo ? modelInfo.num_classes : '—'}</p>
          <span className="text-[8px] text-slate-500 font-mono">{classNames.join(', ')}</span>
        </div>
      </div>

      {/* Main Row: Per-Class Metrics + Confusion Matrix */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Per-Class Metrics */}
        <div className="glass-panel p-5 rounded-xl space-y-4">
          <div>
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Per-Class Classification Metrics</h3>
            <p className="text-[10px] text-slate-400">Precision, Recall, and F1-Score for each attack category</p>
          </div>

          {classReport ? (
            <div className="overflow-x-auto">
              <table className="w-full text-left" id="per-class-metrics-table">
                <thead>
                  <tr className="border-b border-[#1e2230] text-slate-400 text-[10px] font-mono uppercase tracking-wider">
                    <th className="pb-2">Class</th>
                    <th className="pb-2 text-right">Precision</th>
                    <th className="pb-2 text-right">Recall</th>
                    <th className="pb-2 text-right">F1-Score</th>
                    <th className="pb-2 text-right">Support</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-[#181a25]/40 text-xs text-slate-300">
                  {classNames.map(cls => {
                    const m = classReport[cls];
                    if (!m) return null;
                    return (
                      <tr key={cls} className="hover:bg-slate-800/10">
                        <td className="py-2.5 font-semibold flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: classColors[cls] }}></span>
                          {cls}
                        </td>
                        <td className="py-2.5 text-right font-mono">{(m.precision * 100).toFixed(1)}%</td>
                        <td className="py-2.5 text-right font-mono">{(m.recall * 100).toFixed(1)}%</td>
                        <td className="py-2.5 text-right font-mono font-bold text-indigo-400">{(m['f1-score'] * 100).toFixed(1)}%</td>
                        <td className="py-2.5 text-right font-mono text-slate-500">{m.support}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic text-center py-10">No classification report available. Run evaluation first.</p>
          )}

          {/* Visual bar chart of F1 scores */}
          {classReport && (
            <div className="pt-3 border-t border-slate-800">
              <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider block mb-2">F1-Score Distribution</span>
              {renderBarChart(
                classNames.map(c => classReport[c]?.['f1-score'] || 0),
                classNames,
                classNames.map(c => classColors[c]),
                1.0
              )}
            </div>
          )}
        </div>

        {/* Confusion Matrix */}
        <div className="glass-panel p-5 rounded-xl space-y-4">
          <div>
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Confusion Matrix (Normalized)</h3>
            <p className="text-[10px] text-slate-400">How well each class is predicted vs actual labels</p>
          </div>

          {confusionMatrix ? (
            <div className="space-y-4">
              {/* Heatmap grid */}
              <div className="overflow-x-auto">
                <table className="w-full border-collapse" id="confusion-matrix-heatmap">
                  <thead>
                    <tr>
                      <th className="text-[9px] font-mono text-slate-500 p-1"></th>
                      {confusionMatrix.labels.map(label => (
                        <th key={label} className="text-[9px] font-mono text-slate-400 p-1 text-center">{label}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {confusionMatrix.normalized_matrix.map((row, rowIdx) => (
                      <tr key={rowIdx}>
                        <td className="text-[9px] font-mono text-slate-400 p-1 font-bold">{confusionMatrix.labels[rowIdx]}</td>
                        {row.map((val, colIdx) => {
                          const intensity = Math.round(val * 255);
                          const isDiag = rowIdx === colIdx;
                          return (
                            <td
                              key={colIdx}
                              className="p-1 text-center"
                            >
                              <div
                                className="rounded px-1 py-2 font-mono text-[10px] font-bold transition-all"
                                style={{
                                  backgroundColor: isDiag
                                    ? `rgba(99, 102, 241, ${Math.max(0.1, val)})`
                                    : `rgba(244, 63, 94, ${Math.max(0.02, val * 0.8)})`,
                                  color: val > 0.5 ? '#e2e8f0' : '#94a3b8',
                                }}
                              >
                                {(val * 100).toFixed(1)}%
                              </div>
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className="flex items-center justify-between text-[9px] font-mono text-slate-500">
                <span>← ACTUAL CLASS (rows)</span>
                <span>PREDICTED CLASS (columns) →</span>
              </div>

              {/* Raw counts below */}
              <div className="border-t border-slate-800 pt-3">
                <span className="text-[9px] font-mono text-slate-500 uppercase tracking-wider block mb-2">Raw Sample Counts</span>
                <div className="grid grid-cols-5 gap-1 text-center">
                  {confusionMatrix.labels.map((label, i) => {
                    const total = confusionMatrix.matrix[i].reduce((a: number, b: number) => a + b, 0);
                    const correct = confusionMatrix.matrix[i][i];
                    return (
                      <div key={label} className="bg-slate-950/50 rounded p-2 border border-slate-800/50">
                        <span className="text-[8px] font-mono text-slate-500 block">{label}</span>
                        <span className="text-sm font-black text-slate-200 block">{correct}</span>
                        <span className="text-[8px] text-slate-600">/ {total}</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic text-center py-10">No confusion matrix data. Run: <code className="bg-slate-950 px-1 rounded font-mono text-indigo-400">python run_pipeline.py --mode evaluate</code></p>
          )}
        </div>
      </div>

      {/* ROC-AUC + Attack Distribution Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* ROC-AUC Scores */}
        <div className="glass-panel p-5 rounded-xl space-y-4">
          <div>
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">ROC-AUC Scores (One-vs-Rest)</h3>
            <p className="text-[10px] text-slate-400">Area Under the Curve for each class discriminator</p>
          </div>

          {rocCurves ? (
            <div className="space-y-3">
              {classNames.map(cls => {
                const data = rocCurves[cls];
                if (!data) return null;
                const auc = data.auc;
                return (
                  <div key={cls} className="space-y-1">
                    <div className="flex justify-between text-[10px]">
                      <span className="text-slate-300 flex items-center gap-1.5">
                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: classColors[cls] }}></span>
                        {cls}
                      </span>
                      <span className="font-mono font-bold" style={{ color: classColors[cls] }}>{(auc * 100).toFixed(1)}%</span>
                    </div>
                    <div className="w-full bg-slate-900 h-2 rounded-full overflow-hidden border border-slate-800">
                      <div className="h-full rounded-full transition-all duration-1000" style={{ width: `${auc * 100}%`, backgroundColor: classColors[cls] }}></div>
                    </div>
                  </div>
                );
              })}
              <div className="pt-2 border-t border-slate-800 flex justify-between text-[10px] font-mono text-slate-500">
                <span>1.0 = Perfect Discriminator</span>
                <span>Mean AUC: {((Object.values(rocCurves) as Array<{auc: number}>).reduce((sum, d) => sum + d.auc, 0) / Object.keys(rocCurves).length * 100).toFixed(1)}%</span>
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic text-center py-10">No ROC data available</p>
          )}
        </div>

        {/* Attack Distribution */}
        <div className="glass-panel p-5 rounded-xl space-y-4">
          <div>
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Test Set Attack Distribution</h3>
            <p className="text-[10px] text-slate-400">Actual vs. predicted class counts on the test dataset</p>
          </div>

          {attackDist ? (
            <div className="space-y-4">
              <div className="grid grid-cols-5 gap-2">
                {attackDist.labels.map((label: string, idx: number) => (
                  <div key={label} className="text-center">
                    <div className="bg-slate-950/50 rounded-lg p-3 border border-slate-800/50 space-y-1">
                      <span className="w-3 h-3 rounded-full mx-auto block" style={{ backgroundColor: classColors[label] }}></span>
                      <span className="text-[8px] font-mono text-slate-500 block uppercase">{label}</span>
                      <div>
                        <span className="text-xs font-black text-slate-200 block">{attackDist.actual_counts[idx]}</span>
                        <span className="text-[8px] text-slate-600">actual</span>
                      </div>
                      <div>
                        <span className="text-xs font-bold text-indigo-400 block">{attackDist.predicted_counts[idx]}</span>
                        <span className="text-[8px] text-slate-600">predicted</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-xs text-slate-500 italic text-center py-10">No distribution data available</p>
          )}
        </div>
      </div>

      {/* Model Architecture Panel */}
      {architecture && (
        <div className="glass-panel p-5 rounded-xl space-y-4" id="model-architecture-panel">
          <div>
            <h3 className="text-xs font-bold text-slate-200 tracking-wide uppercase">Model Architecture — {architecture.model_name}</h3>
            <p className="text-[10px] text-slate-400">Hybrid CNN-LSTM-Attention network configuration</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            {/* CNN Block */}
            <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/50 space-y-2">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-indigo-400 text-sm">layers</span>
                <span className="text-[10px] font-mono text-indigo-400 font-bold uppercase">CNN Block</span>
              </div>
              <div className="space-y-1 text-[10px] font-mono text-slate-400">
                <p>Conv1D: {architecture.cnn_block.conv1d_1.filters} filters, k={architecture.cnn_block.conv1d_1.kernel_size}</p>
                <p>Conv1D: {architecture.cnn_block.conv1d_2.filters} filters, k={architecture.cnn_block.conv1d_2.kernel_size}</p>
                <p>MaxPool: size={architecture.cnn_block.pool_size}</p>
                <p>BatchNorm + SpatialDropout</p>
              </div>
            </div>

            {/* LSTM Block */}
            <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/50 space-y-2">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-emerald-400 text-sm">timeline</span>
                <span className="text-[10px] font-mono text-emerald-400 font-bold uppercase">LSTM Block</span>
              </div>
              <div className="space-y-1 text-[10px] font-mono text-slate-400">
                <p>BiLSTM: {architecture.lstm_block.bidirectional_lstm.units} units</p>
                <p>Return sequences: true</p>
                <p>Dropout: {(architecture.lstm_block.dropout * 100).toFixed(0)}%</p>
              </div>
            </div>

            {/* Attention */}
            <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/50 space-y-2">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-amber-400 text-sm">center_focus_strong</span>
                <span className="text-[10px] font-mono text-amber-400 font-bold uppercase">Attention</span>
              </div>
              <div className="space-y-1 text-[10px] font-mono text-slate-400">
                <p>{architecture.attention.type}</p>
                <p>Trainable weights: Yes</p>
                <p>Context vector → Dense</p>
              </div>
            </div>

            {/* Training Config */}
            <div className="bg-slate-950/50 p-4 rounded-xl border border-slate-800/50 space-y-2">
              <div className="flex items-center gap-1.5">
                <span className="material-symbols-outlined text-rose-400 text-sm">tune</span>
                <span className="text-[10px] font-mono text-rose-400 font-bold uppercase">Training</span>
              </div>
              <div className="space-y-1 text-[10px] font-mono text-slate-400">
                <p>Optimizer: {architecture.training.optimizer}</p>
                <p>LR: {architecture.training.learning_rate}</p>
                <p>Batch: {architecture.training.batch_size}</p>
                <p>Early Stop: patience={architecture.training.early_stopping_patience}</p>
                <p>Dataset: {architecture.training.dataset}</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
