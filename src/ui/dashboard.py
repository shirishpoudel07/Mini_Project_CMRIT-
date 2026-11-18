import datetime
import io
import json
import streamlit as st
import pandas as pd
from PIL import Image

from src.services.preprocessing import (
    adjust_image,
    apply_window_preset,
    generate_opencv_heatmap,
)
from src.services.reporting import (
    build_doctor_note,
    build_report_dict,
    build_report_text,
)


def render_welcome_screen():
    with st.container(border=True):
        col_w1, col_w2 = st.columns([1.3, 1])
        with col_w1:
            st.subheader('Welcome to XRayAI Clinical Workstation')
            st.write(
                """
                **AI-Assisted Diagnostic Workstation for Chest Radiography:**
                - **Step 1:** Enter your Patient Name and Age in the left sidebar.
                - **Step 2:** Attach your Chest X-Ray image (PNG, JPG, JPEG).
                - **Instant Analysis:** Generates cardiothoracic ratio (CTR), pleural fluid checks, probability spectrum, and formatted clinical summary.
                """
            )
            st.info('👈 Please enter your patient details and attach your chest X-ray in the sidebar to begin.')
        with col_w2:
            st.metric('Workflow Mode', 'User Scan Upload', 'Ready')
            st.metric('System Status', 'OpenCV & Neural Calibrated', 'Online')
            st.metric('Target Checks', 'Pneumonia / Effusion / Heart Size', 'Active')


def render_analysis_view(uploaded_file, patient_id, patient_age, patient_gender, study_view, results, enhanced_gray):
    st.subheader('Diagnostic Analysis & PACS Inspection')

    col_diag1, col_diag2 = st.columns([1.4, 1])

    with col_diag1:
        # Diagnostic Hero Card
        status = results['status']
        condition = results.get('primary_condition', status)
        confidence = results.get('confidence', 95.0)
        severity = results.get('severity', 'None')

        if status == 'Normal':
            st.success(f"### ✅ {condition}\n**Confidence:** {confidence}% | **Severity:** {severity}")
        else:
            st.error(f"### ⚠️ {condition}\n**Confidence:** {confidence}% | **Severity:** {severity}")

        st.info(f"**Findings:** {results.get('findings')}")

        # Multi-Pathology Probabilities
        st.write('**Pathology Probability Spectrum:**')
        probs = results.get('probabilities', {})
        for cond, prob in probs.items():
            col_bar1, col_bar2 = st.columns([3, 1])
            col_bar1.progress(min(prob / 100.0, 1.0))
            col_bar2.caption(f"{cond}: **{prob}%**")

    with col_diag2:
        # Quantitative Metrics Cards
        ctr_data = results.get('ctr_metrics', {})
        eff_data = results.get('costophrenic_metrics', {})
        asym_data = results.get('asymmetry_summary', {})

        with st.container(border=True):
            st.write('**Quantitative Anatomical Metrics:**')
            st.write(f"• **Transverse CTR:** `{ctr_data.get('ctr', 0.43)}` ({ctr_data.get('status', 'Normal')})")
            st.write(f"• **Costophrenic Recesses:** `{eff_data.get('lateralization', 'Sharp')}`")
            st.write(f"• **Max Asymmetry:** `{asym_data.get('max_asymmetry_pct', 0.0)}%` ({asym_data.get('focal_affected_zone', 'Symmetric')})")

    # Image Inspection & Heatmap Modalities
    st.divider()
    st.subheader('Multi-Window Visual Inspection')

    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns(3)
    preset = col_ctrl1.selectbox('Window Preset', ['STANDARD', 'LUNG', 'BONE', 'MEDIASTINUM', 'INVERTED'])
    brightness = col_ctrl2.slider('Brightness', -80, 80, 0)
    contrast = col_ctrl3.slider('Contrast', 0.5, 2.2, 1.0, 0.1)

    windowed = apply_window_preset(enhanced_gray, preset)
    adjusted = adjust_image(windowed, brightness=brightness, contrast=contrast)
    orig_rgb, heat_rgb, overlay_rgb = generate_opencv_heatmap(adjusted, alpha=0.45, colormap_name='JET')

    col_img1, col_img2, col_img3 = st.columns(3)
    col_img1.image(orig_rgb, caption=f"Active Preset: {preset}", use_container_width=True)
    col_img2.image(heat_rgb, caption="OpenCV Density Heatmap (JET)", use_container_width=True)
    col_img3.image(overlay_rgb, caption="Heatmap Overlay", use_container_width=True)

    # Structured Reporting Section
    st.divider()
    st.subheader('Clinical Documentation & Report Sign-Off')

    filename_str = uploaded_file.name if hasattr(uploaded_file, 'name') else str(uploaded_file)
    default_note = build_doctor_note(patient_id, patient_age, patient_gender, results)
    doctor_note = st.text_area("Attending Radiologist Note", value=default_note, height=130)

    report_text = build_report_text(patient_id, patient_age, patient_gender, study_view, filename_str, results, doctor_note)
    report_dict = build_report_dict(patient_id, patient_age, patient_gender, study_view, filename_str, results, doctor_note)

    col_rep1, col_rep2 = st.columns(2)
    col_rep1.download_button(
        '📄 Download Plaintext Report',
        data=report_text,
        file_name=f"xray_report_{patient_id}.txt",
        mime='text/plain',
        use_container_width=True
    )
    col_rep2.download_button(
        '📊 Export JSON Telemetry',
        data=json.dumps(report_dict, indent=2),
        file_name=f"xray_telemetry_{patient_id}.json",
        mime='application/json',
        use_container_width=True
    )
