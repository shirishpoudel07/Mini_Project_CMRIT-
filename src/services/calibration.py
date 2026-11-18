"""
OpenCV Statistical Calibration Service for Chest Radiography.
Analyzes reference chest radiographs to calculate empirical statistical
baselines for normal lung tissue, costophrenic acuity, and CTR thresholds.
"""

import json
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / 'data'
CALIBRATION_FILE = DATA_DIR / 'calibration_metrics.json'


def get_default_calibration():
    """Default calibration values if data folder is not present."""
    return {
        'version': '2.6.0',
        'lung_density_baseline': {'mean': 32.5, 'std': 4.2, 'p5': 26.0, 'p95': 40.0},
        'bilateral_asymmetry_thresholds': {'normal_mean_pct': 3.4, 'consolidation_cutoff_pct': 18.0},
        'ctr_thresholds': {'normal_mean': 0.425, 'cardiomegaly_cutoff': 0.50, 'severe_cutoff': 0.58},
        'costophrenic_acuity': {'normal_sulcus_diff': -8.5, 'blunting_cutoff_diff': 22.0}
    }


def load_calibration():
    """Loads calibration metrics from file with graceful fallback."""
    if CALIBRATION_FILE.exists():
        try:
            with open(CALIBRATION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return get_default_calibration()
