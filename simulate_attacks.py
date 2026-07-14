import os
import sys
import time
import random
import requests
import numpy as np
import pandas as pd

# Add current dir to path to import config and loader
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import config
from src.data_loader import map_attack_label

API_URL = "http://127.0.0.1:5000/predict"
TEST_FILE = config.TEST_FILE


def load_and_group_records():
    """Load the KDDTest+.txt file and group connection records by attack category."""
    if not os.path.exists(TEST_FILE):
        print(f"Error: Test dataset not found at {TEST_FILE}.")
        print("Starting local API server once will automatically download it.")
        sys.exit(1)

    print(f"Loading NSL-KDD test dataset from {TEST_FILE}...")
    df = pd.read_csv(TEST_FILE, header=None, names=config.COLUMN_NAMES)
    df["label"] = df["label"].astype(str).str.strip().str.rstrip(".")
    df["attack_category"] = df["label"].apply(map_attack_label)

    # Group by attack category
    groups = {
        "Normal": df[df["attack_category"] == "Normal"],
        "DoS": df[df["attack_category"] == "DoS"],
        "Probe": df[df["attack_category"] == "Probe"],
        "R2L": df[df["attack_category"] == "R2L"],
        "U2R": df[df["attack_category"] == "U2R"],
    }

    for name, group in groups.items():
        print(f"  - {name}: {len(group)} records available")

    return groups


def send_record(record: dict, attack_cat: str):
    """Format and send a single connection record to the Flask API."""
    # Convert numpy types to native Python types for JSON serialization
    payload = {}
    for k, v in record.items():
        if pd.isna(v):
            payload[k] = 0
        elif isinstance(v, (np.integer,)):
            payload[k] = int(v)
        elif isinstance(v, (np.floating,)):
            payload[k] = float(v)
        elif isinstance(v, (int, float)):
            payload[k] = v
        else:
            payload[k] = str(v)

    # Generate random realistic IPs for visual variation
    octet1 = random.choice([103, 114, 185, 192, 198, 203])
    octet2 = random.randint(10, 220)
    octet3 = random.randint(0, 255)
    octet4 = random.randint(2, 254)

    # If it is an attack, make the source IP look anomalous / external
    if attack_cat != "Normal":
        # Attackers come from specific threat IPs
        payload["source_ip"] = f"{octet1}.{octet2}.{octet3}.{octet4}"
        payload["dest_ip"] = random.choice(["10.0.42.115", "10.0.42.1"])
    else:
        # Normal traffic comes from internal range or safe external CDN
        payload["source_ip"] = f"10.0.1.{random.randint(10, 250)}"
        payload["dest_ip"] = f"10.0.42.{random.choice([1, 115])}"

    try:
        response = requests.post(API_URL, json=payload, timeout=2)
        if response.status_code == 200:
            res_data = response.json()
            pred = res_data.get("prediction", {})
            pred_class = pred.get("predicted_class", "Unknown")
            conf = pred.get("confidence", 0.0) * 100
            
            # Print status log
            print(f"Sent {attack_cat:6} | Source IP: {payload['source_ip']:15} | Predicted: {pred_class:6} ({conf:.1f}%)")
        else:
            print(f"Error: Server returned status code {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to API server. Is Flask running on port 5000?")
    except Exception as e:
        print(f"Error sending request: {e}")


def send_burst(groups, category: str, count: int = 5):
    """Send a quick burst of connection records of a specific category."""
    group = groups.get(category)
    if group is None or len(group) == 0:
        print(f"No records available for category {category}")
        return

    print(f"\n>>> Sending burst of {count} {category} connections...")
    samples = group.sample(min(count, len(group)))
    for _, row in samples.iterrows():
        send_record(row.to_dict(), category)
        time.sleep(0.3)
    print(">>> Burst completed.\n")


def auto_loop(groups):
    """Run an automated continuous traffic loop (mix of normal and attacks)."""
    print("\nStarting continuous traffic simulation. Press Ctrl+C to stop.")
    print("Mixing normal traffic (90%) with periodic attacks (10%)...\n")
    try:
        while True:
            # Decide traffic type
            # 90% normal, 10% chance of random attack category
            if random.random() < 0.90:
                category = "Normal"
            else:
                category = random.choice(["DoS", "Probe", "R2L", "U2R"])

            group = groups.get(category)
            if group is not None and len(group) > 0:
                row = group.sample(1).iloc[0].to_dict()
                send_record(row, category)

            # Random interval between requests (e.g. 0.5 to 2.0 seconds)
            time.sleep(random.uniform(0.5, 2.0))
    except KeyboardInterrupt:
        print("\nContinuous simulation stopped.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="NeuroShield Real-time Intrusion Attack Simulator")
    parser.add_argument("--attack", choices=["Normal", "DoS", "Probe", "R2L", "U2R", "auto"], help="Run attack directly without menu")
    parser.add_argument("--count", type=int, default=5, help="Number of requests for burst")
    parser.add_argument("--duration", type=int, default=0, help="Duration for auto loop in seconds (0 = infinite)")
    args = parser.parse_args()

    print("====================================================")
    print(" NeuroShield Real-time Intrusion Attack Simulator  ")
    print("====================================================")
    
    # Load and group connection records
    groups = load_and_group_records()

    if args.attack:
        if args.attack == "auto":
            if args.duration > 0:
                print(f"Running auto loop for {args.duration} seconds...")
                start_time = time.time()
                try:
                    while time.time() - start_time < args.duration:
                        category = "Normal" if random.random() < 0.90 else random.choice(["DoS", "Probe", "R2L", "U2R"])
                        group = groups.get(category)
                        if group is not None and len(group) > 0:
                            row = group.sample(1).iloc[0].to_dict()
                            send_record(row, category)
                        time.sleep(random.uniform(0.5, 1.5))
                except KeyboardInterrupt:
                    print("Auto loop stopped.")
            else:
                auto_loop(groups)
        else:
            if args.duration > 0:
                print(f"Running continuous loop for {args.attack} attacks for {args.duration} seconds...")
                start_time = time.time()
                try:
                    while time.time() - start_time < args.duration:
                        group = groups.get(args.attack)
                        if group is not None and len(group) > 0:
                            row = group.sample(1).iloc[0].to_dict()
                            send_record(row, args.attack)
                        time.sleep(random.uniform(0.4, 1.2))
                except KeyboardInterrupt:
                    print(f"{args.attack} loop stopped.")
            else:
                send_burst(groups, args.attack, count=args.count)
        return

    while True:
        print("\nSelect traffic pattern to simulate:")
        print("  1. Send Normal traffic burst (5 requests)")
        print("  2. Simulate DoS Attack (Denial of Service)")
        print("  3. Simulate Probe Attack (Reconnaissance Scan)")
        print("  4. Simulate R2L Attack (Remote Unauthorized Access)")
        print("  5. Simulate U2R Attack (Local Privilege Escalation)")
        print("  6. Run continuous mixed traffic loop (Auto-mode)")
        print("  7. Exit")
        
        choice = input("\nEnter choice (1-7): ").strip()
        if choice == "1":
            send_burst(groups, "Normal", count=5)
        elif choice == "2":
            send_burst(groups, "DoS", count=5)
        elif choice == "3":
            send_burst(groups, "Probe", count=5)
        elif choice == "4":
            send_burst(groups, "R2L", count=5)
        elif choice == "5":
            send_burst(groups, "U2R", count=5)
        elif choice == "6":
            auto_loop(groups)
        elif choice == "7":
            print("Exiting simulator.")
            break
        else:
            print("Invalid choice, please enter 1-7.")


if __name__ == "__main__":
    main()
