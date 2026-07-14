"""
Flask REST API for the NeuroShield attack classification engine.

Endpoints:
    POST /predict                   - Classify a single network connection record
    POST /predict/batch             - Classify multiple records at once
    POST /predict/file              - Classify records from an uploaded CSV/txt file
    GET  /model/info                - Get model metadata and performance metrics
    GET  /alerts                    - Retrieve live security alerts (real-time detections)
    POST /alerts/action             - Update alert action state (ISOLATE, REVIEW, etc.)
    GET  /connections               - Retrieve active connections
    GET  /stats                     - Retrieve real-time server stats (uptime, CPU, memory, packet rate)
    GET  /logs                      - Retrieve real backend log stream from pipeline.log
    GET  /topology                  - Retrieve active topology node and flow mapping data
    GET  /reports                   - List generated compliance reports
    POST /reports/generate          - Generate a new CSV compliance report
    GET  /reports/download/<name>   - Download a generated report file
    GET  /health                    - Health check
"""

import os
import sys
import traceback
import io
import time
import threading
from datetime import datetime
from collections import deque
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory

# Add project root to path so we can import config and src modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from src.predictor import AttackPredictor
from utils.logger import get_logger

logger = get_logger(__name__)

app = Flask(__name__)

# Track server start time
server_start_time = time.time()

# Thread lock for shared mutable state accessed across Flask request threads
_state_lock = threading.Lock()

# In-memory queues for live SOC dashboard data
live_alerts = deque(maxlen=50)
live_connections = {}
live_reports = deque(maxlen=20)
request_timestamps = deque(maxlen=500)

# Global predictor instance
predictor = None

# Global simulation process handle
simulation_process = None

# GPU stats cache (avoids spawning nvidia-smi subprocess on every poll)
_gpu_cache = {"data": None, "timestamp": 0.0}

import atexit

@atexit.register
def cleanup_simulation_on_exit():
    global simulation_process
    if simulation_process and simulation_process.poll() is None:
        try:
            simulation_process.terminate()
            simulation_process.wait(timeout=2)
        except Exception:
            pass


def get_gpu_stats():
    """Attempt to query GPU metrics via nvidia-smi, cached for 5 seconds."""
    now = time.time()
    if now - _gpu_cache["timestamp"] < 5.0:
        return _gpu_cache["data"]

    result_data = None
    try:
        import shutil
        if not shutil.which("nvidia-smi"):
            _gpu_cache["data"] = None
            _gpu_cache["timestamp"] = now
            return None
        import subprocess
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=1.5
        )
        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            if lines:
                parts = lines[0].split(",")
                gpu_util = float(parts[0].strip())
                gpu_mem_used = float(parts[1].strip())
                gpu_mem_total = float(parts[2].strip())
                result_data = {
                    "gpu_util": gpu_util,
                    "gpu_mem_used": gpu_mem_used,
                    "gpu_mem_total": gpu_mem_total,
                    "gpu_mem_percent": round((gpu_mem_used / gpu_mem_total) * 100, 1) if gpu_mem_total > 0 else 0.0
                }
    except Exception:
        pass

    _gpu_cache["data"] = result_data
    _gpu_cache["timestamp"] = now
    return result_data


def get_predictor() -> AttackPredictor:
    """Get or create the global predictor instance."""
    global predictor
    if predictor is None:
        predictor = AttackPredictor()
    return predictor


@app.after_request
def add_cors_headers(response):
    """Enable CORS headers for development."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
    response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
    return response


@app.before_request
def handle_options_preflight():
    """Return early for CORS preflight OPTIONS requests."""
    if request.method == "OPTIONS":
        from flask import make_response
        resp = make_response()
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
        resp.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        return resp, 204


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "model_loaded": predictor is not None,
    })


def record_alert_and_connection(record: dict, prediction: dict):
    """
    Log an active connection and trigger a Security Alert if it's anomalous.
    Thread-safe: uses _state_lock for shared state mutations.
    """
    predicted_class = prediction["predicted_class"]
    confidence = prediction["confidence"]

    # Generate or extract IP addresses
    source_ip = record.get("source_ip", f"192.168.1.{100 + (len(live_connections) % 150)}")
    dest_ip = record.get("dest_ip", f"10.0.0.{50 + (len(live_connections) % 50)}")
    protocol = f"{record.get('protocol_type', 'tcp').upper()} / {record.get('service', 'http')}"

    # Track active connection load
    # Use standard features if present to calculate realistic load
    load_val = 10
    if "count" in record:
        try:
            load_val = min(100, int(float(record["count"]) * 2 + float(record.get("srv_count", 0))))
        except Exception:
            pass

    with _state_lock:
        request_timestamps.append(time.time())

        live_connections[source_ip] = {
            "sourceIp": source_ip,
            "destIp": dest_ip,
            "protocol": record.get("protocol_type", "tcp").upper(),
            "load": load_val,
            "last_active": time.time()
        }

        # Trigger alert if the traffic is classified as an attack
        if predicted_class != "Normal":
            severity = "Critical" if predicted_class in ["DoS", "U2R"] else "High"
            alert = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "sourceIp": source_ip,
                "destIp": dest_ip,
                "attackType": f"{predicted_class} Attack Vector",
                "severity": severity,
                "protocol": protocol,
                "confScore": round(confidence * 100, 1),
                "actionTaken": None
            }
            live_alerts.appendleft(alert)

    if predicted_class != "Normal":
        logger.warning(f"Intrusion Detected: {predicted_class} from {source_ip} to {dest_ip} (Conf: {confidence:.2f})")
    else:
        logger.info(f"Normal Request: Processed standard connection from {source_ip} to {dest_ip} (Conf: {confidence:.2f})")


@app.route("/predict", methods=["POST"])
def predict_single():
    """Classify a single network connection record."""
    try:
        pred = get_predictor()
        record = request.get_json()

        if not record:
            return jsonify({"error": "Request body must be a JSON object with features"}), 400

        # Remove extra tags before predicting
        pred_record = {
            k: v for k, v in record.items()
            if k not in ["source_ip", "dest_ip", "label", "attack_category", "difficulty_level"]
        }

        result = pred.predict_record(pred_record)
        record_alert_and_connection(record, result)

        return jsonify({
            "status": "success",
            "prediction": result,
        })

    except Exception as e:
        logger.error(f"Prediction error: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500


@app.route("/predict/batch", methods=["POST"])
def predict_batch():
    """Classify multiple network connection records."""
    try:
        pred = get_predictor()
        data = request.get_json()

        if not data or "records" not in data:
            return jsonify({
                "error": "Request body must contain a 'records' key with a list of record objects"
            }), 400

        records = data["records"]
        if not isinstance(records, list) or len(records) == 0:
            return jsonify({"error": "'records' must be a non-empty list"}), 400

        # Reset buffer for clean batch
        pred.reset_buffer()

        results = []
        for record in records:
            # Predict
            pred_record = {
                k: v for k, v in record.items()
                if k not in ["source_ip", "dest_ip", "label", "attack_category", "difficulty_level"]
            }
            res = pred.predict_record(pred_record)
            record_alert_and_connection(record, res)
            results.append(res)

        return jsonify({
            "status": "success",
            "count": len(results),
            "predictions": results,
        })

    except Exception as e:
        logger.error(f"Batch prediction error: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500


@app.route("/predict/file", methods=["POST"])
def predict_file():
    """Classify connection records from an uploaded CSV or TXT file."""
    try:
        if "file" not in request.files:
            return jsonify({"error": "No file part in the request"}), 400

        file = request.files["file"]
        if file.filename == "":
            return jsonify({"error": "No selected file"}), 400

        file_bytes = file.read()
        if not file_bytes:
            return jsonify({"error": "Empty file"}), 400

        content_str = file_bytes.decode("utf-8", errors="ignore")

        # Read into DataFrame
        first_line = content_str.split("\n")[0]
        has_headers = "duration" in first_line.lower()

        if has_headers:
            df = pd.read_csv(io.StringIO(content_str))
        else:
            df = pd.read_csv(
                io.StringIO(content_str),
                header=None,
                names=config.COLUMN_NAMES[:len(first_line.split(","))]
            )

        if len(df) == 0:
            return jsonify({"error": "No records found in file"}), 400

        actual_categories = []
        if "label" in df.columns:
            from src.data_loader import map_attack_label
            df["attack_category"] = df["label"].astype(str).str.strip().str.rstrip(".").apply(map_attack_label)
            actual_categories = df["attack_category"].tolist()
        elif "attack_category" in df.columns:
            actual_categories = df["attack_category"].tolist()

        pred = get_predictor()
        pred.reset_buffer()
        pred_df = pred.predict_dataframe(df)

        predictions_list = []
        for idx, row in pred_df.iterrows():
            record_dict = df.iloc[idx].to_dict()
            record_pred = {
                "predicted_class": row["predicted_class"],
                "confidence": float(row["confidence"]),
                "all_probabilities": {
                    class_name: float(row[f"prob_{class_name}"])
                    for class_name in config.CLASS_NAMES
                }
            }
            if idx < len(actual_categories):
                record_pred["actual_class"] = actual_categories[idx]
            predictions_list.append(record_pred)

            # Log prediction to live logs/alerts
            record_alert_and_connection(record_dict, record_pred)

        pred_classes = pred_df["predicted_class"].tolist()
        class_counts = pred_df["predicted_class"].value_counts().to_dict()
        for cls in config.CLASS_NAMES:
            if cls not in class_counts:
                class_counts[cls] = 0

        summary = {
            "total_records": len(df),
            "class_counts": class_counts,
        }

        if actual_categories:
            correct = sum(1 for p, a in zip(pred_classes, actual_categories) if p == a)
            summary["accuracy"] = correct / len(df)

        return jsonify({
            "status": "success",
            "filename": file.filename,
            "summary": summary,
            "predictions": predictions_list[:500],
        })

    except Exception as e:
        logger.error(f"File prediction error: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500


@app.route("/model/info", methods=["GET"])
def model_info():
    """Return model metadata and performance metrics."""
    try:
        pred = get_predictor()
        info = pred.get_model_info()

        report = {}
        if os.path.exists(config.CLASSIFICATION_REPORT_PATH):
            import json
            with open(config.CLASSIFICATION_REPORT_PATH, "r") as f:
                report = json.load(f)

        return jsonify({
            "status": "success",
            "model_info": info,
            "classification_report": report,
        })

    except Exception as e:
        logger.error(f"Model info error: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": str(e),
        }), 500


@app.route("/alerts", methods=["GET"])
def get_alerts():
    """Retrieve the live list of anomalous security alerts."""
    return jsonify(list(live_alerts))


@app.route("/alerts/action", methods=["POST"])
def alert_action():
    """Update action state on a live threat alert."""
    data = request.get_json() or {}
    source_ip = data.get("sourceIp")
    action = data.get("action")  # 'ISOLATE' or 'REVIEW' or 'IGNORE'

    with _state_lock:
        for alert in live_alerts:
            if alert["sourceIp"] == source_ip:
                alert["actionTaken"] = action

    return jsonify({"status": "success"})


@app.route("/connections", methods=["GET"])
def get_connections():
    """Retrieve active connections list (removing inactive ones)."""
    now = time.time()
    with _state_lock:
        inactive = [ip for ip, conn in live_connections.items() if now - conn["last_active"] > 30]
        for ip in inactive:
            del live_connections[ip]
        result = list(live_connections.values())

    return jsonify(result)


@app.route("/stats", methods=["GET"])
def get_stats():
    """Retrieve real-time system stats (uptime, packets rate, resource usage)."""
    now = time.time()

    with _state_lock:
        # Trim old timestamps (older than 10 seconds)
        while request_timestamps and now - request_timestamps[0] > 10:
            request_timestamps.popleft()
        packet_rate = len(request_timestamps) / 10.0

    uptime_seconds = int(now - server_start_time)
    days = uptime_seconds // 86400
    hours = (uptime_seconds % 86400) // 3600
    mins = (uptime_seconds % 3600) // 60
    secs = uptime_seconds % 60

    cpu = 12.5
    memory = 44.1
    try:
        import psutil
        cpu = psutil.cpu_percent()
        memory = psutil.virtual_memory().percent
    except Exception:
        pass

    gpu_info = get_gpu_stats()

    return jsonify({
        "uptime": {
            "days": days,
            "hours": hours,
            "mins": mins,
            "secs": secs
        },
        "packet_rate": round(packet_rate, 2),
        "cpu": cpu,
        "memory": memory,
        "gpu": gpu_info,
        "total_alerts": len(live_alerts),
        "active_connections_count": len(live_connections)
    })


@app.route("/logs", methods=["GET"])
def get_logs():
    """Read the actual server log stream from pipeline.log."""
    log_file = os.path.join(config.LOGS_DIR, "pipeline.log")
    if not os.path.exists(log_file):
        return jsonify([])

    try:
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()[-40:]

        parsed_logs = []
        for line in reversed(lines):
            parts = line.strip().split(" | ")
            if len(parts) >= 4:
                ts = parts[0]
                level = parts[1].strip()
                module = parts[2].strip()
                # File handler format has 5 parts: ts | level | module | funcName:lineno | message
                # Console handler format has 4 parts: ts | level | module | message
                if len(parts) >= 5:
                    message = " | ".join(parts[4:])
                else:
                    message = " | ".join(parts[3:])

                severity = "INFO"
                if level in ["ERROR", "CRITICAL"]:
                    severity = "ERROR"
                elif level == "WARNING":
                    severity = "WARN"
                elif level == "DEBUG":
                    severity = "DEBUG"

                parsed_logs.append({
                    "timestamp": ts,
                    "severity": severity,
                    "module": module,
                    "message": message,
                    "status": "Success" if level == "INFO" else "Warning" if level == "WARNING" else "Failed",
                    "color": "text-secondary" if level == "INFO" else "text-tertiary" if level == "WARNING" else "text-error"
                })
        return jsonify(parsed_logs)
    except Exception as e:
        return jsonify([{
            "timestamp": "",
            "severity": "ERROR",
            "module": "System",
            "message": f"Failed to read logs: {e}",
            "status": "Failed",
            "color": "text-error"
        }])


@app.route("/simulation/start", methods=["POST"])
def start_simulation():
    """Start the attack simulator script as a background process."""
    global simulation_process
    if simulation_process and simulation_process.poll() is None:
        return jsonify({"status": "error", "message": "Simulation is already running"})

    try:
        data = request.get_json() or {}
        attack_type = data.get("attack_type", "auto")  # 'Normal', 'DoS', 'Probe', 'R2L', 'U2R', 'auto'
        
        import subprocess
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "simulate_attacks.py")
        python_exe = sys.executable

        logger.info(f"Triggering background attack simulation loop. Type: {attack_type}")
        simulation_process = subprocess.Popen(
            [python_exe, script_path, "--attack", attack_type, "--duration", "600"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return jsonify({"status": "success", "message": f"Simulation ({attack_type}) started successfully"})
    except Exception as e:
        logger.error(f"Failed to start simulation: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/simulation/stop", methods=["POST"])
def stop_simulation():
    """Stop the background attack simulator process."""
    global simulation_process
    if simulation_process and simulation_process.poll() is None:
        try:
            simulation_process.terminate()
            simulation_process.wait(timeout=2)
        except Exception:
            try:
                simulation_process.kill()
            except Exception:
                pass
        simulation_process = None
        logger.info("Background attack simulation stopped by user command.")
        return jsonify({"status": "success", "message": "Simulation stopped"})
    return jsonify({"status": "error", "message": "Simulation is not currently running"})


@app.route("/simulation/status", methods=["GET"])
def simulation_status():
    """Retrieve running status of the simulation process."""
    global simulation_process
    is_running = simulation_process is not None and simulation_process.poll() is None
    return jsonify({
        "status": "success",
        "running": is_running
    })


@app.route("/topology", methods=["GET"])
def get_topology():
    """Dynamically generate topology nodes and edges based on active hosts."""
    nodes = [
        {
            "id": "2",
            "label": "Core Gateway (192.168.1.1)",
            "type": "Gateway",
            "activeConnections": len(live_connections) + 4,
            "trafficRate": f"{round(0.25 * (len(live_connections) + 4), 2)} Gbps",
            "x": 400,
            "y": 220
        },
        {
            "id": "1",
            "label": "HR Server (10.0.42.115)",
            "type": "Server",
            "activeConnections": 4,
            "trafficRate": "1.2 Gbps",
            "x": 220,
            "y": 150
        },
        {
            "id": "4",
            "label": "DC-01 Controller (10.0.42.1)",
            "type": "Server",
            "activeConnections": 8,
            "trafficRate": "2.1 Gbps",
            "x": 450,
            "y": 340
        },
        {
            "id": "7",
            "label": "Analyst Terminal (10.0.1.55)",
            "type": "Internal",
            "activeConnections": 2,
            "trafficRate": "50 Mbps",
            "x": 310,
            "y": 110
        }
    ]

    connections = [
        {"from": "1", "to": "2", "speed": "1.2 Gbps"},
        {"from": "4", "to": "2", "speed": "2.1 Gbps"},
        {"from": "7", "to": "2", "speed": "50 Mbps"}
    ]

    # Dynamically place active threat nodes
    threat_ips = set()
    for alert in list(live_alerts)[:5]:
        ip = alert["sourceIp"]
        if ip not in threat_ips:
            threat_ips.add(ip)
            node_id = f"threat_{len(nodes)}"
            nodes.append({
                "id": node_id,
                "label": f"Threat ({ip})",
                "type": "Threat",
                "activeConnections": 1,
                "trafficRate": "10 Mbps",
                "x": 620 + (len(threat_ips) * 15),
                "y": 120 + (len(threat_ips) * 20)
            })
            connections.append({"from": node_id, "to": "2", "speed": "10 Mbps", "threat": True})

    # Assemble Top Bandwidth Talkers
    top_talkers = []
    for idx, conn in enumerate(list(live_connections.values())[:4]):
        top_talkers.append({
            "sourceIp": conn["sourceIp"],
            "sourceLabel": "External Host" if not conn["sourceIp"].startswith("10.") else "Internal Host",
            "destIp": conn["destIp"],
            "destLabel": "Gateway",
            "packets": f"{conn['load'] * 12}k",
            "bandwidth": f"{round(conn['load'] * 0.15, 2)} GB" if conn['load'] > 30 else f"{conn['load'] * 3.4} MB",
            "status": "Normal" if conn["load"] < 60 else "High Risk",
            "statusColor": "text-secondary bg-secondary/10 ring-secondary/30" if conn["load"] < 60 else "text-error bg-error/10 ring-error/30 animate-pulse"
        })

    return jsonify({
        "nodes": nodes,
        "connections": connections,
        "top_talkers": top_talkers
    })


@app.route("/evaluation", methods=["GET"])
def get_evaluation():
    """Serve pre-computed evaluation artifacts (confusion matrix, ROC, distribution)."""
    import json as _json

    result = {}

    # Confusion matrix
    cm_json = config.CONFUSION_MATRIX_PATH.replace(".png", ".json")
    if os.path.exists(cm_json):
        with open(cm_json, "r") as f:
            result["confusion_matrix"] = _json.load(f)

    # ROC curves
    roc_json = config.ROC_CURVES_PATH.replace(".png", ".json")
    if os.path.exists(roc_json):
        with open(roc_json, "r") as f:
            result["roc_curves"] = _json.load(f)

    # Attack distribution
    dist_json = config.ATTACK_DISTRIBUTION_PATH.replace(".png", ".json")
    if os.path.exists(dist_json):
        with open(dist_json, "r") as f:
            result["attack_distribution"] = _json.load(f)

    if not result:
        return jsonify({
            "status": "error",
            "message": "No evaluation data found. Run evaluation first: python run_pipeline.py --mode evaluate"
        }), 404

    return jsonify({"status": "success", **result})


@app.route("/model/architecture", methods=["GET"])
def get_model_architecture():
    """Return model architecture configuration details."""
    return jsonify({
        "status": "success",
        "architecture": {
            "model_name": "CNN-LSTM-Attention IDS",
            "cnn_block": {
                "conv1d_1": {"filters": config.CNN_FILTERS_1, "kernel_size": config.CNN_KERNEL_SIZE_1},
                "conv1d_2": {"filters": config.CNN_FILTERS_2, "kernel_size": config.CNN_KERNEL_SIZE_2},
                "pool_size": config.POOL_SIZE,
                "batch_normalization": True,
                "spatial_dropout": 0.2,
            },
            "lstm_block": {
                "bidirectional_lstm": {"units": config.LSTM_UNITS_1, "return_sequences": True},
                "lstm_2": {"units": config.LSTM_UNITS_2},
                "dropout": config.DROPOUT_RATE,
            },
            "attention": {"type": "Bahdanau-style learned attention", "trainable": True},
            "classification_head": {
                "dense_units": config.DENSE_UNITS,
                "dropout": config.DROPOUT_RATE,
                "output_activation": "softmax",
                "num_classes": config.NUM_CLASSES,
                "class_names": config.CLASS_NAMES,
            },
            "training": {
                "optimizer": "Adam",
                "learning_rate": config.LEARNING_RATE,
                "loss": "categorical_crossentropy",
                "batch_size": config.BATCH_SIZE,
                "epochs": config.EPOCHS,
                "early_stopping_patience": config.EARLY_STOPPING_PATIENCE,
                "l2_regularization": config.L2_REGULARIZATION,
                "sequence_length": config.SEQUENCE_LENGTH,
                "dataset": "NSL-KDD",
            },
        },
    })


@app.route("/reports", methods=["GET"])
def get_reports():
    """Retrieve compliance reports catalog."""
    return jsonify(list(live_reports))


@app.route("/reports/generate", methods=["POST"])
def generate_report():
    """Generate a real CSV report based on active system alerts."""
    try:
        data = request.get_json() or {}
        template = data.get("template", "Threat_Incident_Log")
        date_range = data.get("dateRange", "Last 24 Hours")
        file_format = data.get("format", "CSV")

        filename = f"{template}_{date_range.replace(' ', '_')}.{file_format.lower()}"

        import csv
        from io import StringIO

        # Compile CSV
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(["Timestamp", "Source IP", "Destination IP", "Attack Type", "Severity", "Protocol", "Confidence Score", "Action Taken"])
        for alert in live_alerts:
            cw.writerow([
                alert["timestamp"],
                alert["sourceIp"],
                alert["destIp"],
                alert["attackType"],
                alert["severity"],
                alert["protocol"],
                alert["confScore"],
                alert["actionTaken"] or "None"
            ])
        content = si.getvalue()

        report_path = os.path.join(config.OUTPUTS_DIR, filename)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)

        report_item = {
            "id": f"rep_{int(time.time())}",
            "name": filename,
            "type": "Vulnerability" if "Vulnerability" in template or "Audit" in template else "Intelligence",
            "generated": datetime.now().strftime("%b %d, %H:%M"),
            "status": "Ready",
            "hash": f"{int(time.time()):x}c2a1e4"
        }
        live_reports.appendleft(report_item)

        return jsonify({
            "status": "success",
            "report": report_item
        })

    except Exception as e:
        logger.error(f"Report generation error: {traceback.format_exc()}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/reports/download/<filename>", methods=["GET"])
def download_report_file(filename):
    """Download a generated report from the outputs directory."""
    return send_from_directory(config.OUTPUTS_DIR, filename, as_attachment=True)


def start_api():
    """Start the Flask API server."""
    logger.info(f"Starting API server on {config.API_HOST}:{config.API_PORT}")

    try:
        get_predictor()
        logger.info("Model loaded successfully. API ready.")
    except FileNotFoundError as e:
        logger.error(f"Cannot start API: {e}")
        sys.exit(1)

    app.run(host=config.API_HOST, port=config.API_PORT, debug=False)


if __name__ == "__main__":
    start_api()
