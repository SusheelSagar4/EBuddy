"""
Forwarder script to run the SDE Quiz Assessment Knowledge Base pipeline.
"""
import os
import sys

# Ensure sde/scripts is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
scripts_dir = os.path.join(current_dir, "sde", "scripts")
if scripts_dir not in sys.path:
    sys.path.insert(0, scripts_dir)

from build_sde_quiz_csvs import build_sde_quiz_pipeline

if __name__ == "__main__":
    build_sde_quiz_pipeline(base_dir=current_dir)
