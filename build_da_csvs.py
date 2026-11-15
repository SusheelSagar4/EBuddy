"""
build_da_csvs.py - Knowledge Base Pipeline Forwarder
Delegates to da/scripts/build_da_csvs.py
"""
import os
import sys
import subprocess

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target = os.path.join(script_dir, "da", "scripts", "build_da_csvs.py")
    sys.exit(subprocess.run([sys.executable, target] + sys.argv[1:]).returncode)
