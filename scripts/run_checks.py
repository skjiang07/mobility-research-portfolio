"""Run project behavior checks in separate processes to avoid import collisions."""
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]

if __name__ == "__main__":
    for project in sorted((ROOT / "projects").iterdir()):
        checks = project / ("demo" if project.name == "gtfs-traffic-monitoring" else "tests")
        subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", str(checks),
                        "-p", "test_*.py", "-v"], check=True)
