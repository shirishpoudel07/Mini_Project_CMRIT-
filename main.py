"""
CLI Launcher for XRayAI Pro.
Launches the React PACS API Server (Option A) or Streamlit Dashboard (Option B).
"""

import sys
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def main():
    print("=" * 60)
    print("   🩻  XRayAI Pro • Radiology Clinical Platform Launcher    ")
    print("=" * 60)
    print("1. Launch React PACS Workstation & API Server (Port 8000)")
    print("2. Launch Streamlit Clinical Dashboard (Port 8501)")
    print("3. Run Precision Automated Backend Tests")
    print("=" * 60)

    choice = input("Select an option (1, 2, or 3) [default: 1]: ").strip() or "1"

    if choice == "1":
        print("\nStarting React PACS Workstation at http://localhost:8000 ...")
        subprocess.run([sys.executable, str(BASE_DIR / "api_server.py")])
    elif choice == "2":
        print("\nStarting Streamlit Dashboard at http://localhost:8501 ...")
        subprocess.run([sys.executable, "-m", "streamlit", "run", str(BASE_DIR / "app.py")])
    elif choice == "3":
        print("\nRunning unit tests...")
        subprocess.run([sys.executable, "-m", "unittest", "test_backend.py"])
    else:
        print("Invalid choice. Exiting.")

if __name__ == '__main__':
    main()
