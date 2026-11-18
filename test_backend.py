"""
Comprehensive Precision Diagnostic & Dataset Test Suite for XRayAI.
Tests clinical accuracy across dataset scans in data/ and verifies OpenCV
feature extraction (CTR, costophrenic sulci, zonal asymmetry).
"""

import unittest
from pathlib import Path
import numpy as np
from PIL import Image

from src.services.preprocessing import (
    preprocess_medical_image,
    analyze_costophrenic_angles,
    estimate_cardiothoracic_ratio,
    segment_anatomical_zones,
    apply_window_preset,
    generate_opencv_heatmap,
)
from src.services.inference import run_model_inference
from src.services.reporting import build_doctor_note, build_report_text
from src.services.calibration import load_calibration

DATA_DIR = Path(__file__).resolve().parent / 'data'


class TestPreciseRadiologyDiagnosis(unittest.TestCase):

    def test_calibration_metrics_exist(self):
        calib = load_calibration()
        self.assertIn('lung_density_baseline', calib)
        self.assertIn('ctr_thresholds', calib)

    def test_dataset_folder_structure(self):
        """Verifies that the data/ directory contains the 5 clinical categories."""
        self.assertTrue((DATA_DIR / 'normal').exists())
        self.assertTrue((DATA_DIR / 'pneumonia').exists())
        self.assertTrue((DATA_DIR / 'effusion').exists())
        self.assertTrue((DATA_DIR / 'cardiomegaly').exists())
        self.assertTrue((DATA_DIR / 'pneumothorax').exists())
        self.assertTrue((DATA_DIR / 'dataset_catalog.json').exists())
        self.assertTrue((DATA_DIR / 'dataset_catalog.csv').exists())

    def test_real_dataset_image_loading(self):
        """Verifies reading and preprocessing real dataset images from data/."""
        norm_img_path = DATA_DIR / 'normal' / 'cxr_normal_001.png'
        if norm_img_path.exists():
            pil_img = Image.open(norm_img_path)
            enhanced, normalized = preprocess_medical_image(pil_img)
            self.assertEqual(enhanced.shape, (224, 224))
            self.assertEqual(normalized.shape, (224, 224))

            results = run_model_inference(normalized, enhanced_gray=enhanced)
            self.assertEqual(results['status'], 'Normal')
            self.assertIn('Normal', results['primary_condition'])
            self.assertTrue(results['probabilities']['Normal'] > 90.0)

    def test_normal_scan_precision(self):
        normal_gray = np.full((224, 224), 80, dtype=np.uint8)
        normal_gray[30:170, 25:95] = 40
        normal_gray[30:170, 129:199] = 40
        normal_gray[90:170, 85:140] = 135

        norm_float = normal_gray.astype(np.float32) / 255.0
        results = run_model_inference(norm_float, enhanced_gray=normal_gray)

        self.assertEqual(results['status'], 'Normal')
        self.assertIn('Normal', results['primary_condition'])
        self.assertTrue(results['probabilities']['Normal'] >= 94.0)
        self.assertLessEqual(results['ctr_metrics']['ctr'], 0.50)

    def test_cardiomegaly_precision(self):
        cardio_gray = np.full((224, 224), 80, dtype=np.uint8)
        cardio_gray[30:170, 20:85] = 40
        cardio_gray[30:170, 139:204] = 40
        cardio_gray[85:175, 65:165] = 145

        norm_float = cardio_gray.astype(np.float32) / 255.0
        results = run_model_inference(norm_float, enhanced_gray=cardio_gray)

        self.assertEqual(results['status'], 'Abnormality Detected')
        self.assertIn('Cardiomegaly', results['primary_condition'])
        self.assertTrue(results['ctr_metrics']['is_enlarged'])
        self.assertGreater(results['ctr_metrics']['ctr'], 0.50)

    def test_pleural_effusion_precision(self):
        effusion_gray = np.full((224, 224), 80, dtype=np.uint8)
        effusion_gray[30:170, 25:95] = 40
        effusion_gray[30:170, 129:199] = 40
        effusion_gray[90:170, 90:135] = 135
        effusion_gray[175:224, 180:224] = 185

        norm_float = effusion_gray.astype(np.float32) / 255.0
        results = run_model_inference(norm_float, enhanced_gray=effusion_gray)

        self.assertEqual(results['status'], 'Abnormality Detected')
        self.assertIn('Pleural Effusion', results['primary_condition'])
        self.assertTrue(results['probabilities']['Effusion'] > 80.0)

    def test_pneumonia_focal_consolidation_precision(self):
        pneumonia_gray = np.full((224, 224), 80, dtype=np.uint8)
        pneumonia_gray[30:170, 129:199] = 40
        pneumonia_gray[30:100, 25:95] = 40
        pneumonia_gray[100:170, 25:95] = 195
        pneumonia_gray[90:170, 90:135] = 135

        norm_float = pneumonia_gray.astype(np.float32) / 255.0
        results = run_model_inference(norm_float, enhanced_gray=pneumonia_gray)

        self.assertEqual(results['status'], 'Abnormality Detected')
        self.assertIn('Pneumonia', results['primary_condition'])
        self.assertTrue(results['probabilities']['Pneumonia'] > 85.0)


if __name__ == '__main__':
    unittest.main()
