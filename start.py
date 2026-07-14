"""
NeuroShield — Unified Launch Script

Starts both the Flask API backend (port 5000) and the Vite React
frontend (port 3000) with a single command.

Usage:
    python start.py

The dashboard will be available at http://localhost:3000
The API server will be available at http://localhost:5000
Press Ctrl+C to stop both servers.
"""

import os
import sys
import signal
import subprocess
import threading
import time
import webbrowser

# Ensure project root is on the Python path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Track subprocesses for cleanup
processes = []
shutdown_event = threading.Event()


def start_flask_api():
    """Start the Flask API server in a background thread."""
    print("\n[NeuroShield] Starting Flask API server on http://127.0.0.1:5000 ...")

    # Import here to avoid loading TF before we need it
    from api.engine import start_api

    try:
        start_api()
    except Exception as e:
        print(f"[NeuroShield] Flask API error: {e}")
        shutdown_event.set()


def start_vite_frontend():
    """Start the Vite dev server as a subprocess."""
    frontend_dir = os.path.join(PROJECT_ROOT, "frontend")

    if not os.path.exists(os.path.join(frontend_dir, "node_modules")):
        print("[NeuroShield] Installing frontend dependencies (first run)...")
        install_proc = subprocess.run(
            ["npm", "install"],
            cwd=frontend_dir,
            shell=True,
            capture_output=True,
            text=True,
        )
        if install_proc.returncode != 0:
            print(f"[NeuroShield] npm install failed:\n{install_proc.stderr}")
            shutdown_event.set()
            return

    print("[NeuroShield] Starting Vite frontend on http://localhost:3000 ...")

    proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=frontend_dir,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    processes.append(proc)

    # Stream Vite output
    try:
        for line in proc.stdout:
            if shutdown_event.is_set():
                break
            stripped = line.strip()
            if stripped:
                print(f"[Vite] {stripped}")
    except Exception:
        pass


def open_browser():
    """Open the browser after a short delay to let servers start."""
    time.sleep(4)
    if not shutdown_event.is_set():
        url = "http://localhost:3000"
        print(f"\n[NeuroShield] Opening dashboard at {url}")
        webbrowser.open(url)


def cleanup(signum=None, frame=None):
    """Gracefully shut down all servers."""
    print("\n[NeuroShield] Shutting down...")
    shutdown_event.set()

    for proc in processes:
        try:
            proc.terminate()
            proc.wait(timeout=5)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass

    print("[NeuroShield] All servers stopped. Goodbye!")
    sys.exit(0)


def main():
    print("=" * 60)
    print("  NeuroShield — Network Intrusion Detection System")
    print("  Hybrid CNN-LSTM-Attention Classification Engine")
    print("=" * 60)
    print()
    print("  Dashboard:  http://localhost:3000")
    print("  API:        http://localhost:5000")
    print("  Press Ctrl+C to stop all servers")
    print()
    print("=" * 60)

    # Register signal handlers for clean shutdown
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Start Flask API in a daemon thread
    api_thread = threading.Thread(target=start_flask_api, daemon=True)
    api_thread.start()

    # Start browser opener in a daemon thread
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    # Start Vite frontend (this blocks in the main-ish flow)
    vite_thread = threading.Thread(target=start_vite_frontend, daemon=True)
    vite_thread.start()

    # Keep main thread alive
    try:
        while not shutdown_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        cleanup()


if __name__ == "__main__":
    main()
