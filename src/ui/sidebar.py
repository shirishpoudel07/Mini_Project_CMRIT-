import json
from pathlib import Path
import pandas as pd
import streamlit as st
from PIL import Image

from src.core.config import DEFAULT_PATIENT_AGE, DEFAULT_PATIENT_GENDER, DEFAULT_PATIENT_ID, DEFAULT_STUDY_VIEW

DATA_DIR = Path(__file__).resolve().parents[2] / 'data'


def load_dataset_options():
    catalog_path = DATA_DIR / 'dataset_catalog.json'
    if not catalog_path.exists():
        return []
    try:
        with open(catalog_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('samples', [])
    except Exception:
        return []


def render_sidebar():
    with st.sidebar:
        st.title('🩻 XRayAI Clinical')
        st.caption('Personal Chest Radiography Analysis')

        # Step 1: Patient Information (Always first)
        with st.container(border=True):
            st.subheader('👤 Step 1: Patient Details')
            patient_name = st.text_input('Full Name', value='', placeholder='Enter your name')
            col_p1, col_p2 = st.columns(2)
            patient_age = col_p1.number_input('Age', min_value=1, max_value=120, value=35)
            patient_gender = col_p2.selectbox('Gender', ['Male', 'Female', 'Other'], index=0)
            study_view = st.selectbox('Study View', ['Chest X-Ray (PA View)', 'Chest X-Ray (AP View)', 'Lateral View'], index=0)

            disp_id = patient_name.strip() if patient_name.strip() else DEFAULT_PATIENT_ID

        # Step 2: User Scan Upload (User uploads their own image)
        with st.container(border=True):
            st.subheader('📤 Step 2: Attach X-Ray')
            uploaded_file = st.file_uploader(
                'Select Chest Radiograph',
                type=['png', 'jpg', 'jpeg'],
                help='Attach your chest X-ray image (PNG, JPG, JPEG).'
            )

        effective_file_or_image = uploaded_file
        scan_filename = uploaded_file.name if uploaded_file is not None else 'user_scan.png'

        with st.container(border=True):
            st.subheader('🕒 Session History')
            if st.session_state.history:
                history_df = pd.DataFrame(st.session_state.history)
                st.dataframe(
                    history_df[['Filename', 'Diagnosis', 'Confidence', 'Time']],
                    use_container_width=True,
                    hide_index=True
                )
                if st.button('🗑️ Clear History', use_container_width=True):
                    st.session_state.history = []
                    st.rerun()
            else:
                st.info('No scans analyzed in this session yet.')

    return effective_file_or_image, scan_filename, disp_id, patient_age, patient_gender, study_view
