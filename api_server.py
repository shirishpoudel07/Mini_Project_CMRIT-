"""
High-Performance Clinical REST API & Static React Workstation Server.
Serves the React PACS Single Page Application and powers clinical endpoints:
- POST /api/analyze       -> Multi-organ diagnostic arbitration & visual modalities
- POST /api/adjust        -> Real-time brightness & contrast adjustment
- GET  /api/dataset       -> Preloaded reference radiograph catalog
- GET  /api/calibration   -> Empirical OpenCV calibration benchmarks
- GET  /api/health        -> System operational telemetry
"""

import base64
import io
import json
import mimetypes
import os
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse

import cv2
import numpy as np
from PIL import Image

from src.core.config import (
    DEFAULT_PATIENT_AGE,
    DEFAULT_PATIENT_GENDER,
    DEFAULT_PATIENT_ID,
    DEFAULT_STUDY_VIEW,
)
from src.core.model_loader import load_medical_model
from src.services.calibration import load_calibration
from src.services.inference import run_model_inference
from src.services.preprocessing import (
    adjust_image,
    apply_window_preset,
    generate_opencv_heatmap,
    preprocess_medical_image,
)
from src.services.reporting import (
    build_doctor_note,
    build_report_dict,
    build_report_text,
)

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = BASE_DIR / 'frontend' / 'dist'
FRONTEND_DIR = BASE_DIR / 'frontend'
DATA_DIR = BASE_DIR / 'data'
PORT = 8000

# Cache neural model
MEDICAL_MODEL = load_medical_model()


def encode_image_to_base64(img_rgb):
    """Encodes RGB numpy array to base64 PNG data URL."""
    pil = Image.fromarray(img_rgb)
    buf = io.BytesIO()
    pil.save(buf, format='PNG')
    encoded = base64.b64encode(buf.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{encoded}"


def load_dataset_catalog_with_previews():
    """Loads dataset catalog from data/dataset_catalog.json."""
    catalog_path = DATA_DIR / 'dataset_catalog.json'
    if not catalog_path.exists():
        return []
    try:
        with open(catalog_path, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
    except Exception:
        return []

    results = []
    for item in catalog.get('samples', []):
        img_path = DATA_DIR / item.get('filename')
        thumb_b64 = None
        if img_path.exists():
            try:
                raw = cv2.imread(str(img_path))
                if raw is not None:
                    thumb = cv2.resize(raw, (96, 96))
                    thumb_b64 = encode_image_to_base64(cv2.cvtColor(thumb, cv2.COLOR_BGR2RGB))
            except Exception:
                pass
        item_copy = dict(item)
        item_copy['preview_b64'] = thumb_b64
        results.append(item_copy)
    return results


class XRayAPIRequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler supporting REST API endpoints and static React serving."""

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(HTTPStatus.NO_CONTENT)
        self.end_headers()

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path

            if path == '/api/health':
                self._handle_health()
            elif path == '/api/dataset':
                self._handle_dataset()
            elif path == '/api/calibration':
                self._handle_calibration()
            else:
                self._handle_static_files(path)
        except Exception as e:
            import traceback
            traceback.print_exc()
            self._send_json({'error': str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/api/analyze':
            self._handle_analyze()
        elif path == '/api/adjust':
            self._handle_adjust()
        elif path == '/api/report':
            self._handle_report()
        else:
            self._send_json({'success': False, 'error': f"Endpoint '{path}' not found"}, status=HTTPStatus.NOT_FOUND)

    def _handle_health(self):
        payload = {
            'status': 'healthy',
            'version': '2.6.0',
            'precision_mode': 'OpenCV Calibrated Multi-Organ Feature Arbitration',
            'model_loaded': bool(MEDICAL_MODEL is not None),
            'dataset_available': bool((DATA_DIR / 'dataset_catalog.json').exists()),
            'endpoints': ['/api/health', '/api/dataset', '/api/calibration', '/api/analyze', '/api/adjust', '/api/report']
        }
        self._send_json(payload)

    def _handle_dataset(self):
        """Returns the full catalog of clinical chest X-rays stored in data/."""
        samples = load_dataset_catalog_with_previews()
        self._send_json({
            'total_samples': len(samples),
            'samples': samples
        })

    def _handle_calibration(self):
        """Returns empirical OpenCV calibration parameters derived from data/."""
        calib = load_calibration()
        self._send_json(calib)

    def _handle_analyze(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))

            dataset_id = body.get('dataset_id')
            image_data = body.get('image')
            patient_name = body.get('patient_name', '').strip()
            patient_id = body.get('patient_id', '').strip()
            if not patient_name:
                patient_name = patient_id if patient_id else 'Patient'
            if not patient_id:
                clean_name = ''.join(c for c in patient_name if c.isalnum()).upper()[:6]
                patient_id = f"PT-{clean_name or 'USR'}-{abs(hash(patient_name)) % 10000:04d}"

            patient_age = int(body.get('patient_age', DEFAULT_PATIENT_AGE))
            patient_gender = body.get('patient_gender', DEFAULT_PATIENT_GENDER)
            study_view = body.get('study_view', DEFAULT_STUDY_VIEW)
            filename = body.get('filename', 'scan_001.png')

            pil_img = None

            # Check if loading from data/ by dataset_id (kept for API compatibility)
            if dataset_id:
                catalog_path = DATA_DIR / 'dataset_catalog.json'
                if catalog_path.exists():
                    with open(catalog_path, 'r', encoding='utf-8') as f:
                        catalog = json.load(f)
                    for item in catalog.get('samples', []):
                        if item['id'] == dataset_id:
                            target_file = DATA_DIR / item['filename']
                            if target_file.exists():
                                pil_img = Image.open(target_file)
                                patient_id = item.get('patient_id', patient_id)
                                patient_name = item.get('patient_name', patient_id)
                                patient_age = item.get('age', patient_age)
                                patient_gender = item.get('gender', patient_gender)
                                filename = Path(item['filename']).name
                            break

            if pil_img is None and image_data:
                if ',' in image_data:
                    image_data = image_data.split(',', 1)[1]
                img_bytes = base64.b64decode(image_data)
                pil_img = Image.open(io.BytesIO(img_bytes))

            if pil_img is None:
                self._send_json({'success': False, 'error': 'No image data or valid dataset_id provided.'}, status=HTTPStatus.BAD_REQUEST)
                return

            enhanced_gray, normalized = preprocess_medical_image(pil_img)
            results = run_model_inference(normalized, nn_model=MEDICAL_MODEL, enhanced_gray=enhanced_gray)

            orig_rgb, heat_rgb, overlay_rgb = generate_opencv_heatmap(enhanced_gray, alpha=0.45, colormap_name='JET')
            lung_view = apply_window_preset(enhanced_gray, 'LUNG')
            bone_view = apply_window_preset(enhanced_gray, 'BONE')
            inverted_view = apply_window_preset(enhanced_gray, 'INVERTED')
            mediastinum_view = apply_window_preset(enhanced_gray, 'MEDIASTINUM')

            disp_patient = f"{patient_name} ({patient_id})" if patient_name != patient_id else patient_id
            doctor_note_draft = build_doctor_note(disp_patient, patient_age, patient_gender, results)
            report_text = build_report_text(disp_patient, patient_age, patient_gender, study_view, filename, results, doctor_note_draft)
            report_dict = build_report_dict(disp_patient, patient_age, patient_gender, study_view, filename, results, doctor_note_draft)

            response_payload = {
                'success': True,
                'metadata': {
                    'patient_name': patient_name,
                    'patient_id': patient_id,
                    'patient_age': patient_age,
                    'patient_gender': patient_gender,
                    'study_view': study_view,
                    'filename': filename,
                },
                'diagnostic': results,
                'visualizations': {
                    'original': encode_image_to_base64(orig_rgb),
                    'heatmap': encode_image_to_base64(heat_rgb),
                    'overlay': encode_image_to_base64(overlay_rgb),
                    'lung_window': encode_image_to_base64(cv2.cvtColor(lung_view, cv2.COLOR_GRAY2RGB)),
                    'bone_window': encode_image_to_base64(cv2.cvtColor(bone_view, cv2.COLOR_GRAY2RGB)),
                    'inverted': encode_image_to_base64(cv2.cvtColor(inverted_view, cv2.COLOR_GRAY2RGB)),
                    'mediastinum': encode_image_to_base64(cv2.cvtColor(mediastinum_view, cv2.COLOR_GRAY2RGB)),
                },
                'report': {
                    'text': report_text,
                    'structured': report_dict,
                    'doctor_note_draft': doctor_note_draft,
                }
            }
            self._send_json(response_payload)

        except Exception as e:
            self._send_json({'success': False, 'error': f"Inference processing failed: {str(e)}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_adjust(self):
        """Applies dynamic real-time contrast, brightness, and colormap blend."""
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))

            image_data = body.get('image')
            brightness = int(body.get('brightness', 0))
            contrast = float(body.get('contrast', 1.0))
            preset = body.get('preset', 'STANDARD')
            colormap = body.get('colormap', 'JET')
            alpha = float(body.get('alpha', 0.45))

            if not image_data:
                self._send_json({'success': False, 'error': 'Missing image data'}, status=HTTPStatus.BAD_REQUEST)
                return

            if ',' in image_data:
                image_data = image_data.split(',', 1)[1]
            img_bytes = base64.b64decode(image_data)
            pil_img = Image.open(io.BytesIO(img_bytes)).convert('RGB')
            gray = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2GRAY)

            # Apply window preset
            windowed = apply_window_preset(gray, preset)

            # Apply brightness & contrast
            adjusted = adjust_image(windowed, brightness=brightness, contrast=contrast)

            # Generate heatmap overlay
            _, heat_rgb, overlay_rgb = generate_opencv_heatmap(adjusted, alpha=alpha, colormap_name=colormap)

            self._send_json({
                'success': True,
                'adjusted_original': encode_image_to_base64(cv2.cvtColor(adjusted, cv2.COLOR_GRAY2RGB)),
                'adjusted_heatmap': encode_image_to_base64(heat_rgb),
                'adjusted_overlay': encode_image_to_base64(overlay_rgb)
            })
        except Exception as e:
            self._send_json({'success': False, 'error': f"Adjustment failed: {str(e)}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_report(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))

            patient_id = body.get('patient_id', DEFAULT_PATIENT_ID)
            patient_age = body.get('patient_age', DEFAULT_PATIENT_AGE)
            patient_gender = body.get('patient_gender', DEFAULT_PATIENT_GENDER)
            study_view = body.get('study_view', DEFAULT_STUDY_VIEW)
            filename = body.get('filename', 'scan.png')
            results = body.get('results', {})
            doctor_note = body.get('doctor_note', '')

            report_text = build_report_text(patient_id, patient_age, patient_gender, study_view, filename, results, doctor_note)
            report_dict = build_report_dict(patient_id, patient_age, patient_gender, study_view, filename, results, doctor_note)

            self._send_json({
                'success': True,
                'report_text': report_text,
                'report_dict': report_dict
            })
        except Exception as e:
            self._send_json({'success': False, 'error': str(e)}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _handle_static_files(self, req_path):
        """Serves static files from frontend/dist (production SPA) or data/."""
        if req_path.startswith('/data/'):
            rel_file = req_path[len('/data/'):]
            target = DATA_DIR / rel_file
            if target.exists() and target.is_file():
                self._serve_file(target)
                return

        serve_dir = FRONTEND_DIST if FRONTEND_DIST.exists() else FRONTEND_DIR
        clean_path = req_path.lstrip('/')
        if not clean_path:
            clean_path = 'index.html'

        target_file = serve_dir / clean_path

        # SPA routing: fallback to index.html if file not found
        if not target_file.exists() or not target_file.is_file():
            target_file = serve_dir / 'index.html'

        if target_file.exists() and target_file.is_file():
            self._serve_file(target_file)
        else:
            self._send_json({'error': 'Static file not found'}, status=HTTPStatus.NOT_FOUND)

    def _serve_file(self, file_path):
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type is None:
            mime_type = 'application/octet-stream'

        try:
            with open(file_path, 'rb') as f:
                content = f.read()

            self.send_response(HTTPStatus.OK)
            self.send_header('Content-Type', mime_type)
            self.send_header('Content-Length', str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self._send_json({'error': f"Failed to read file: {e}"}, status=HTTPStatus.INTERNAL_SERVER_ERROR)

    def _send_json(self, data, status=HTTPStatus.OK):
        body = json.dumps(data).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        # Quiet standard HTTP access logs
        pass


def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, XRayAPIRequestHandler)
    print(f"============================================================")
    print(f"   XRayAI Clinical API & React Server Listening on :{PORT}   ")
    print(f"   React PACS Web Client: http://localhost:{PORT}            ")
    print(f"   API Telemetry:         http://localhost:{PORT}/api/health ")
    print(f"============================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down XRayAI server.")
        httpd.server_close()


if __name__ == '__main__':
    run_server()
