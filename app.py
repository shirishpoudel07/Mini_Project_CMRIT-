import datetime
import streamlit as st
from PIL import Image

from src.core.model_loader import load_medical_model
from src.services.inference import run_model_inference
from src.services.preprocessing import preprocess_medical_image
from src.ui.dashboard import render_analysis_view, render_welcome_screen
from src.ui.sidebar import render_sidebar


def initialize_session_state():
    if 'history' not in st.session_state:
        st.session_state.history = []
    if 'current_file_name' not in st.session_state:
        st.session_state.current_file_name = None


def main():
    st.set_page_config(
        page_title='XRayAI • Radiology Clinical Dashboard',
        page_icon='🩻',
        layout='wide',
        initial_sidebar_state='expanded'
    )

    initialize_session_state()

    model = load_medical_model()
    effective_img_or_file, scan_filename, patient_id, patient_age, patient_gender, study_view = render_sidebar()

    if effective_img_or_file is None:
        render_welcome_screen()
        return

    if isinstance(effective_img_or_file, Image.Image):
        pil_image = effective_img_or_file
    else:
        pil_image = Image.open(effective_img_or_file)

    enhanced_gray, normalized_img = preprocess_medical_image(pil_image)
    results = run_model_inference(normalized_img, model, enhanced_gray=enhanced_gray)

    if st.session_state.current_file_name != scan_filename:
        st.session_state.current_file_name = scan_filename
        timestamp_str = datetime.datetime.now().strftime('%H:%M:%S')
        st.session_state.history.append({
            'Filename': scan_filename,
            'Patient ID': patient_id,
            'Diagnosis': results.get('primary_condition', results['status']),
            'Confidence': f"{results['confidence']}%",
            'Time': timestamp_str
        })

    render_analysis_view(
        uploaded_file=scan_filename,
        patient_id=patient_id,
        patient_age=patient_age,
        patient_gender=patient_gender,
        study_view=study_view,
        results=results,
        enhanced_gray=enhanced_gray,
    )


if __name__ == '__main__':
    main()
