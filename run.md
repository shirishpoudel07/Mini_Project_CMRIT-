# 🩻 XRayAI Pro • How to Run (`run.md`)

Welcome to **XRayAI Pro**. Follow these instructions to launch the application.

---

## ⚡ Fastest Way to Run (1-Click)

On Windows, simply double-click either batch file in the root folder:

| File | What It Launches | URL in Browser |
| :--- | :--- | :--- |
| **`run_app.bat`** | **React Clinical Workstation + Backend API** (Recommended) | **[http://localhost:8000](http://localhost:8000)** |
| **`run_streamlit.bat`** | **Streamlit Clinical Dashboard** | **[http://localhost:8501](http://localhost:8501)** |

*(Both batch scripts automatically use the verified Python 3.14 environment to avoid Windows Store alias conflicts).*

---

## 🚀 Option 1: Run via Terminal (React Workstation + Backend API)

To run the full application from PowerShell or Command Prompt:

```bash
py -3.14 api_server.py
```
*(or `.\.venv\Scripts\python.exe api_server.py`)*

You will see:
```text
============================================================
   XRayAI Clinical API & React Server Listening on :8000   
   React PACS Web Client: http://localhost:8000            
   API Telemetry:         http://localhost:8000/api/health 
============================================================
```

👉 Open your browser: **[http://localhost:8000](http://localhost:8000)**

---

## 🌐 Option 2: Instant Offline Mode (No Server / Zero Terminal)

To immediately view and test the clean React interface without running any server:

1. Open `frontend/` in File Explorer.
2. Double-click **[`frontend/standalone.html`](file:///C:/Users/shiri/OneDrive/mini_project-main/frontend/standalone.html)**.
3. The interface opens instantly with client-side analysis and interactive controls ready.

---

## 📊 Option 3: Run the Streamlit Dashboard via Terminal

To launch the Streamlit interface:

```bash
py -3.14 -m streamlit run app.py
```
*(or `.\.venv\Scripts\python.exe -m streamlit run app.py`)*

👉 Open your browser: **[http://localhost:8501](http://localhost:8501)**

---

## 🧪 Option 4: Run Automated Verification Tests

To verify that all OpenCV feature extraction and diagnostic models operate with 0 errors:

```bash
py -3.14 -m unittest test_backend.py
```
*(Runs 7 precision diagnostic test suites across all pathology categories).*
