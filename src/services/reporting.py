"""
Radiological Reporting and Clinical Note Generation Service.
Generates structured ACR-standard radiology reports, doctor notes, and export schemas.
"""

import datetime


def build_doctor_note(patient_id, patient_age, patient_gender, results):
    """Generates an initial clinician progress note draft."""
    condition = results.get('primary_condition', results.get('status', 'Examination'))
    conf = results.get('confidence', 95.0)
    sev = results.get('severity', 'None')

    lines = [
        f"ASSESSMENT & CLINICAL IMPRESSION ({condition}):",
        f"- Patient: {patient_id} ({patient_age}y, {patient_gender}).",
        f"- Automated radiographic feature extraction indicates {condition} (Confidence: {conf}%).",
    ]

    ctr = results.get('ctr_metrics', {})
    if ctr.get('is_enlarged'):
        lines.append(f"- Cardiomegaly alert: Cardiothoracic Ratio measured at {ctr.get('ctr')} (> 0.50 threshold).")

    eff = results.get('costophrenic_metrics', {})
    if eff.get('is_effusion_present'):
        lines.append(f"- Pleural space alert: Dependent blunting noted in {eff.get('lateralization')}.")

    lines.append(f"- Clinical Severity Grade: {sev}.")
    lines.append("- Next steps: Clinical correlation and radiologist verification required prior to intervention.")
    return "\n".join(lines)


def build_report_text(patient_id, patient_age, patient_gender, study_view, filename, results, doctor_note):
    """Assembles a clean, structured plaintext radiology study report."""
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sections = [
        "================================================================================",
        "                    XRAYAI RADIOLOGY CLINICAL REPORT                            ",
        "================================================================================",
        f"Date of Study:     {now_str}",
        f"Patient ID:        {patient_id}",
        f"Age / Gender:      {patient_age} years / {patient_gender}",
        f"Study Modality:    {study_view}",
        f"Source Image:      {filename}",
        "--------------------------------------------------------------------------------",
        "CLINICAL INDICATION & TECHNIQUE:",
        f"Diagnostic radiograph processed via high-resolution adaptive contrast enhancement",
        f"and multi-organ OpenCV anatomical feature arbitration.",
        "--------------------------------------------------------------------------------",
        "QUANTITATIVE METRICS:",
        f"• Cardiothoracic Ratio (CTR): {results.get('ctr_metrics', {}).get('ctr', 'N/A')} ({results.get('ctr_metrics', {}).get('status', 'N/A')})",
        f"• Costophrenic Sulci:         {results.get('costophrenic_metrics', {}).get('lateralization', 'N/A')}",
        f"• Maximum Bilateral Asymmetry: {results.get('asymmetry_summary', {}).get('max_asymmetry_pct', 0.0)}% ({results.get('asymmetry_summary', {}).get('focal_affected_zone', 'N/A')})",
        "--------------------------------------------------------------------------------",
        "DETAILED FINDINGS:",
        results.get('findings', 'Lungs clear bilaterally.'),
        "",
        "SYSTEM-BY-SYSTEM OBSERVATIONS:",
    ]

    for obs in results.get('observations', []):
        sections.append(f"  • {obs}")

    sections.extend([
        "--------------------------------------------------------------------------------",
        "DIAGNOSTIC CONCLUSION:",
        f"  IMPRESSION: {results.get('conclusion', results.get('primary_condition', 'Normal'))}",
        f"  SEVERITY:   {results.get('severity', 'None')}",
        f"  CONFIDENCE: {results.get('confidence', 95.0)}%",
        "--------------------------------------------------------------------------------",
        "RECOMMENDED CLINICAL ACTION:",
        f"  {results.get('recommendation', 'Routine clinical screening.')}",
        "--------------------------------------------------------------------------------",
        "ATTENDING PHYSICIAN / RADIOLOGIST NOTES:",
        doctor_note or "(No additional clinician notes entered)",
        "================================================================================",
        "NOTICE: Computer-aided detection tool. Diagnostic sign-off required by licensed MD.",
        "================================================================================",
    ])

    return "\n".join(sections)


def build_report_dict(patient_id, patient_age, patient_gender, study_view, filename, results, doctor_note):
    """Returns a structured dictionary suitable for JSON serialization."""
    return {
        'timestamp': datetime.datetime.now().isoformat(),
        'patient': {
            'id': patient_id,
            'age': patient_age,
            'gender': patient_gender,
            'study_view': study_view,
            'filename': filename,
        },
        'diagnosis': {
            'status': results.get('status'),
            'primary_condition': results.get('primary_condition'),
            'confidence': results.get('confidence'),
            'severity': results.get('severity'),
            'probabilities': results.get('probabilities'),
        },
        'metrics': {
            'ctr': results.get('ctr_metrics'),
            'costophrenic': results.get('costophrenic_metrics'),
            'asymmetry': results.get('asymmetry_summary'),
            'hotspots_count': len(results.get('hotspots', [])),
        },
        'narrative': {
            'findings': results.get('findings'),
            'observations': results.get('observations'),
            'conclusion': results.get('conclusion'),
            'recommendation': results.get('recommendation'),
        },
        'doctor_note': doctor_note,
    }
