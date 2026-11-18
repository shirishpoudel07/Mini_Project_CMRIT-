import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / 'data'
MODEL_PATH = BASE_DIR / 'medical_model.h5'

# Image Preprocessing Constants
IMAGE_SIZE = (224, 224)
CLAHE_CLIP_LIMIT = 2.0
CLAHE_GRID_SIZE = (8, 8)
NORM_PERCENTILE_LOW = 2.0
NORM_PERCENTILE_HIGH = 98.0

# Clinical CTR Thresholds
CTR_NORMAL_MAX = 0.50
CTR_MILD_MAX = 0.55
CTR_MODERATE_MAX = 0.60

# Asymmetry Thresholds
ASYMMETRY_NORMAL_MAX = 18.0
ASYMMETRY_CONSOLIDATION_CUTOFF = 22.0

# Patient Defaults
DEFAULT_PATIENT_ID = "PT-84291"
DEFAULT_PATIENT_AGE = 45
DEFAULT_PATIENT_GENDER = "Male"
DEFAULT_STUDY_VIEW = "Chest X-Ray (PA View)"
