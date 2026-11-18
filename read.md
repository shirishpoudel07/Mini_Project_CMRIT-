# XRayAI Pro • Radiology Clinical Precision Workstation & Platform (`read.md`)

**Date of Update:** November 16, 2026  
**System Status:** Clean, Calibrated, Error-Free, React PACS Integrated  
**Workspace:** `mini_project-main`

---

## 1. Project Overview & Architecture

**XRayAI Pro** is a modern clinical-grade medical imaging platform for chest radiography analysis. It offers two user interfaces:
1. **React Clinical PACS Workstation ([frontend/](file:///C:/Users/shiri/OneDrive/mini_project-main/frontend)):** Dark radiology PACS interface with interactive caliper measurements, windowing presets, multi-colormap heatmaps, 6-zone segmentation, and dataset library.
2. **Streamlit Clinical Dashboard ([app.py](file:///C:/Users/shiri/OneDrive/mini_project-main/app.py)):** Diagnostic interface with multi-modal inspection cards and data export.

Both are powered by the modular computer vision and deep learning services in `src/`, calibrated against the reference dataset in `data/`.

---

## 2. Directory Layout (Simplified & Cleaned)

```text
mini_project-main/
├── api_server.py                  # High-performance REST API & Static React Server
├── app.py                         # Streamlit Application Coordinator
├── main.py                        # Executable CLI Launcher
├── medical_model.h5               # Trained CNN Weights File (~9.14 MB)
├── requirements.txt               # Backend Dependencies
├── test_backend.py                # Automated Precision Unit Test Suite
├── read.md                        # Documentation & Update Log (this file)
├── run.md                         # Complete Execution & Deployment Guide
│
├── data/                          # Reference Calibrated Chest Radiographs
│   ├── dataset_catalog.json       # JSON Metadata Catalog
│   ├── dataset_catalog.csv        # Tabular CSV Manifest
│   ├── calibration_metrics.json   # Empirical OpenCV Calibration Thresholds
│   ├── normal/                    # 4 Normal chest X-rays
│   ├── pneumonia/                 # 4 Lobar consolidation / pneumonia scans
│   ├── effusion/                  # 3 Pleural effusion scans
│   ├── cardiomegaly/              # 3 Cardiomegaly scans
│   └── pneumothorax/              # 1 Apical pneumothorax scan
│
├── frontend/                      # React 18 PACS Single-Page Application
│   ├── index.html                 # Vite HTML entry point
│   ├── standalone.html            # Standalone double-clickable browser PACS viewer
│   ├── package.json               # Node.js manifest
│   ├── vite.config.js             # Vite configuration
│   ├── tailwind.config.js         # Tailwind configuration
│   ├── postcss.config.js          # PostCSS configuration
│   ├── dist/                      # Compiled production bundle
│   └── src/                       # Modular React components
│       ├── main.jsx
│       ├── App.jsx
│       └── index.css
│
└── src/                           # Clean Modular Services
    ├── core/
    │   ├── config.py              # Environment paths & clinical patient defaults
    │   └── model_loader.py        # Safe cached TensorFlow model loader with fallback
    ├── services/
    │   ├── preprocessing.py       # Exposure normalization, CTR, costophrenic sulci, windows
    │   ├── inference.py           # Multi-organ feature arbitration & condition-specific diagnoses
    │   ├── reporting.py           # Clinical reports, CSV exports, JSON schemas
    │   └── calibration.py         # Empirical statistical calibration service
    └── ui/
        ├── sidebar.py             # Streamlit patient metadata & dataset picker
        └── dashboard.py           # Streamlit clinical workspace with PACS tools
```

---

## 3. UI/UX Enhancements: React PACS Workstation

1. **Interactive PACS Viewport:**
   - Smooth mouse pan ($X, Y$) and wheel zoom ($25\%$ - $500\%$) with instant reset.
   - Caliper measurement tool: click two anatomical landmarks to calculate distances in pixels ($px$) and millimeters ($mm$).
   - Synchronized Split-Screen / Curtain comparator between original radiograph and AI heatmap overlay.
   - Radiographic window presets: Chest PA, Lung Parenchyma, Bone Detail, Mediastinum, and Negative Invert.
   - Dynamic colormaps: JET, TURBO, VIRIDIS, HOT with real-time alpha blend opacity slider.
2. **Clinical Decision Support Panel:**
   - Diagnostic Hero Card with status, severity badge, and calibrated confidence percentage.
   - Transverse Cardiothoracic Ratio (CTR) indicator and Costophrenic Sulcus acuity check.
   - 6-Zone Thoracic Density quadrant grid and Anomaly Hotspot cluster table.
   - ACR Structured Reporting with editable clinician notes and printable report sheet.
3. **Reference Dataset Library:**
   - 15 Preloaded clinical radiographs across 5 pathology categories with search, category filtering, and one-click loading.

---

## 4. Execution Quick-Start

```bash
# Launch React PACS Workstation & API Server (Port 8000)
python api_server.py

# Launch Streamlit Dashboard (Port 8501)
streamlit run app.py

# Run Automated Test Suite
python -m unittest test_backend.py
```

---

## 5. Package Resolution & Environment Status

- **Virtual Environment (`.venv`):** Rebuilt with verified Python 3.14 runtime linked to system packages (`streamlit`, `pandas`, `pillow`, `opencv-python`, `numpy`), resolving Windows Smart App Control DLL restrictions.
- **Editor Settings (`.vscode/settings.json`):** Configured `python.defaultInterpreterPath` and `python.analysis.extraPaths` so that all IDE imports for `import streamlit as st`, `import pandas as pd`, and `from PIL import Image` resolve cleanly without any warnings or red squiggly lines.
- **Verification:** Unit tests and module import checks execute with 0 errors across all services.
