"""Run the five offline synthetic examples from any working directory."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
DEMOS = [
    "gtfs-traffic-monitoring/demo/synthetic_demo.py",
    "hurricane-ian-traffic/demo/rdit_demo.py",
    "wildfire-evacuation/demo/evacuation_metrics_demo.py",
    "mobility-data-bias/demo/representation_demo.py",
    "geoai-activity-inference/demo/activity_demo.py",
]

if __name__ == "__main__":
    for demo in DEMOS:
        print(f"\n--- {demo} ---", flush=True)
        subprocess.run([sys.executable, str(ROOT / "projects" / demo)], check=True)
