"""
Upload Section Module

Handles Job Description and Resume uploads with backend integration.

Workflow:
1. User uploads JD PDF
2. User uploads multiple resume PDFs
3. Files are saved to uploads/jd/ and uploads/resumes/
4. User clicks "Analyze Candidates"
5. Backend pipeline (app.py) is triggered via backend_connector
6. Results are loaded and displayed in dashboard
"""

import streamlit as st
from pathlib import Path
from typing import Optional
import time
import os
import uuid

import backend_connector
import utils

# Upload directories
PROJECT_ROOT = Path(__file__).resolve().parents[1]
UPLOADS_DIR = PROJECT_ROOT / "uploads"
JD_DIR = UPLOADS_DIR / "jd"
RESUMES_DIR = UPLOADS_DIR / "resumes"

# Ensure directories exist
JD_DIR.mkdir(parents=True, exist_ok=True)
RESUMES_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_EXTENSIONS = {".pdf"}


def save_uploaded_file(uploaded_file, destination: Path) -> Optional[Path]:
    """
    Save uploaded file to destination.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        destination (Path): Directory to save to
    
    Returns:
        Path to saved file or None if failed
    """
    try:
        dest_path = destination / uploaded_file.name
        
        # Avoid overwriting by appending unique id
        if dest_path.exists():
            name, ext = os.path.splitext(uploaded_file.name)
            dest_path = destination / f"{name}_{uuid.uuid4().hex[:6]}{ext}"
        
        with open(dest_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return dest_path
    
    except Exception as e:
        st.error(f"Failed to save {uploaded_file.name}: {str(e)}")
        return None


def validate_file_type(filename: str) -> bool:
    """Validate file is PDF."""
    return Path(filename).suffix.lower() in ALLOWED_EXTENSIONS


def clear_uploads_ui():
    """Clear all uploaded files."""
    try:
        utils.clear_uploads()
        st.success("✅ All uploads cleared. Ready for new analysis.")
    except Exception as e:
        st.error(f"Error clearing uploads: {str(e)}")


def render_upload_page() -> None:
    """Render the upload and analysis page."""
    st.title("📤 Upload & Analyze Candidates")
    st.markdown("Upload your Job Description and candidate resumes to start the AI-powered screening process.")
    st.markdown("---")
    
    # Initialize session state to track processed files
    if "processed_jd_files" not in st.session_state:
        st.session_state.processed_jd_files = set()
    
    if "processed_resume_files" not in st.session_state:
        st.session_state.processed_resume_files = set()
    
    # Check for existing uploads
    upload_status = utils.get_upload_status()
    
    # Show current upload status
    if upload_status["jd_count"] > 0 or upload_status["resume_count"] > 0:
        with st.status("Current Uploads", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.metric("JD Files", upload_status["jd_count"])
            with col2:
                st.metric("Resume Files", upload_status["resume_count"])
            
            if st.button("🗑️ Clear All Uploads", use_container_width=True):
                clear_uploads_ui()
                # Reset processed files tracking
                st.session_state.processed_jd_files = set()
                st.session_state.processed_resume_files = set()
                st.rerun()
        
        st.markdown("---")
    
    # Step 1: JD Upload
    st.subheader("Step 1: Upload Job Description")
    st.markdown("Upload the job description PDF for the position you're hiring for.")
    
    jd_file = st.file_uploader(
        "📄 JD PDF",
        type=["pdf"],
        key="jd_uploader",
        help="Drag and drop or click to browse"
    )
    
    if jd_file is not None:
        # Create unique file identifier to track if already processed
        file_id = f"{jd_file.name}_{jd_file.size}"
        
        # Only save if this specific file hasn't been processed yet
        if file_id not in st.session_state.processed_jd_files:
            if validate_file_type(jd_file.name):
                with st.spinner(f"Saving {jd_file.name}..."):
                    saved_path = save_uploaded_file(jd_file, JD_DIR)
                
                if saved_path:
                    st.session_state.processed_jd_files.add(file_id)
                    st.success(f"✅ Saved: {jd_file.name}")
                    st.caption(f"Location: {saved_path}")
            else:
                st.error("❌ Only PDF files are supported. Please upload a PDF file.")
        else:
            st.info(f"ℹ️ {jd_file.name} was already uploaded in this session")
    
    st.markdown("---")
    
    # Step 2: Resume Upload
    st.subheader("Step 2: Upload Candidate Resumes")
    st.markdown("Upload PDF resumes of candidates you want to screen. You can upload multiple files at once.")
    
    resumes = st.file_uploader(
        "📄 Resume PDFs (Multiple)",
        type=["pdf"],
        accept_multiple_files=True,
        key="resume_uploader",
        help="Select one or more resume PDF files"
    )
    
    if resumes:
        progress_container = st.container()
        
        with progress_container:
            progress_bar = st.progress(0)
            status_text = st.empty()
        
        for idx, resume in enumerate(resumes, start=1):
            if not validate_file_type(resume.name):
                st.warning(f"⚠️ Skipping {resume.name}: not a PDF")
                continue
            
            # Create unique file identifier
            file_id = f"{resume.name}_{resume.size}"
            
            # Only save if not already processed
            if file_id not in st.session_state.processed_resume_files:
                with st.spinner(f"Saving {resume.name}..."):
                    saved_path = save_uploaded_file(resume, RESUMES_DIR)
                    time.sleep(0.2)
                
                if saved_path:
                    st.session_state.processed_resume_files.add(file_id)
                    st.success(f"✅ Saved: {resume.name}")
            else:
                st.info(f"ℹ️ {resume.name} was already uploaded in this session")
            
            progress = min(idx / len(resumes), 1.0)
            progress_bar.progress(progress)
            status_text.text(f"Processed {idx}/{len(resumes)} resume(s)")
        
        progress_bar.empty()
        status_text.empty()
    
    st.markdown("---")
    
    # Step 3: Analysis
    st.subheader("Step 3: Analyze Candidates")
    st.markdown("Click the button below to trigger the AI backend pipeline.")
    
    # Validation check
    upload_status = utils.get_upload_status()
    
    if upload_status["jd_count"] == 0 or upload_status["resume_count"] == 0:
        st.warning("⚠️ Please upload both a JD and at least one resume before analyzing.")
        st.button("🔎 Analyze Candidates", disabled=True, use_container_width=True)
    
    else:
        # Ready to analyze
        st.info(f"✅ Ready to analyze: {upload_status['jd_count']} JD, {upload_status['resume_count']} resume(s)")
        
        analyze_button = st.button("🔎 Analyze Candidates", use_container_width=True, type="primary")
        
        if analyze_button:
            st.markdown("---")
            
            # Create containers for progress and logs
            progress_container = st.container()
            log_container = st.container()
            
            # Run backend
            success, result_data, message = backend_connector.run_backend(
                progress_container,
                log_container
            )
            
            st.markdown("---")
            
            if success:
                # Save to session state
                st.session_state.batch_data = result_data
                st.session_state.candidates_df = utils.extract_candidate_dataframe(result_data)
                st.session_state.current_page = "Dashboard"
                
                st.success("✅ Analysis complete! Switching to Dashboard...")
                st.balloons()
                
                # Rerun to show dashboard
                time.sleep(1)
                st.rerun()
            
            else:
                st.error(f"❌ Analysis failed: {message}")
                st.info("Please check the logs above for details.")
