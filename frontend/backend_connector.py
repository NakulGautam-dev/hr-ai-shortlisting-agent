"""
Backend Connector Module

Handles execution of the backend AI HR Resume Shortlisting pipeline.

Responsibilities:
- Execute the backend app.py using subprocess
- Capture and stream logs
- Monitor processing completion
- Handle errors gracefully
- Detect result file generation
- Return success/failure status

This module bridges the frontend UI with the backend scoring engine.
"""

import subprocess
import sys
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import json
import time
import streamlit as st

# Project structure
PROJECT_ROOT = Path(__file__).resolve().parents[1]
BACKEND_APP = PROJECT_ROOT / "app.py"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


def get_latest_result_file() -> Optional[Path]:
    """
    Get the most recently modified result JSON file from outputs/.
    
    Returns:
        Path to latest result file or None if no results exist
    """
    if not OUTPUTS_DIR.exists():
        return None
    
    result_files = sorted(
        OUTPUTS_DIR.glob("*results*.json"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    return result_files[0] if result_files else None


def get_result_file_before(timestamp: float) -> Optional[Path]:
    """
    Get result file that was created after a certain timestamp.
    Used to detect newly generated files after backend execution.
    
    Args:
        timestamp (float): Reference time in seconds since epoch
    
    Returns:
        Path to new result file or None if no new file exists
    """
    if not OUTPUTS_DIR.exists():
        return None
    
    new_files = [
        f for f in OUTPUTS_DIR.glob("*results*.json")
        if f.stat().st_mtime > timestamp
    ]
    
    if new_files:
        return sorted(new_files, key=lambda x: x.stat().st_mtime, reverse=True)[0]
    
    return None


def load_result_json(file_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load and parse result JSON file.
    
    Args:
        file_path (Path): Path to JSON file
    
    Returns:
        Parsed JSON dict or None if load fails
    """
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Error loading result file: {str(e)}")
        return None


def run_backend(
    progress_placeholder,
    log_placeholder,
    timeout: int = 300
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Execute the backend pipeline and monitor completion.
    
    Args:
        progress_placeholder: Streamlit container for progress updates
        log_placeholder: Streamlit container for log output
        timeout (int): Maximum seconds to wait for backend completion
    
    Returns:
        Tuple of (success: bool, result_data: dict or None, message: str)
    """
    
    # Verify backend app exists
    if not BACKEND_APP.exists():
        error_msg = f"Backend app not found at: {BACKEND_APP}"
        st.error(error_msg)
        return False, None, error_msg
    
    # Record timestamp before execution to detect new result files
    start_time = time.time()
    pre_execution_time = start_time - 1  # Small buffer
    
    try:
        # Show status
        with progress_placeholder.container():
            st.info("🚀 Starting backend pipeline...")
        
        # Build command
        python_exe = sys.executable
        cmd = [python_exe, str(BACKEND_APP)]
        
        # Execute backend process
        with progress_placeholder.container():
            st.info("⏳ Processing... This may take a minute depending on file sizes and API response times.")
        
        # Run process and capture output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=str(PROJECT_ROOT)
        )
        
        # Stream output in real-time
        accumulated_output = []
        log_lines = []
        progress_steps = [
            "Extracting Job Description",
            "Processing Resumes",
            "Performing Semantic Analysis",
            "Calculating Candidate Scores",
            "Ranking Candidates",
            "Generating Results"
        ]
        step_idx = 0
        
        # Read stdout while process runs
        try:
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                
                accumulated_output.append(line)
                log_lines.append(line.strip())
                
                # Update progress based on keywords in output
                if any(keyword in line.lower() for keyword in ["extracting", "parsing", "jd"]):
                    step_idx = max(step_idx, 1)
                elif any(keyword in line.lower() for keyword in ["resume", "processing"]):
                    step_idx = max(step_idx, 2)
                elif any(keyword in line.lower() for keyword in ["semantic", "analysis", "embedding"]):
                    step_idx = max(step_idx, 3)
                elif any(keyword in line.lower() for keyword in ["scoring", "score", "calculate"]):
                    step_idx = max(step_idx, 4)
                elif any(keyword in line.lower() for keyword in ["ranking", "rank"]):
                    step_idx = max(step_idx, 5)
                elif any(keyword in line.lower() for keyword in ["saving", "save", "output", "json"]):
                    step_idx = max(step_idx, 6)
                
                # Update UI every 5 lines
                if len(log_lines) % 5 == 0:
                    with progress_placeholder.container():
                        col1, col2 = st.columns([0.3, 0.7])
                        with col1:
                            st.metric("Step", f"{step_idx + 1}/6")
                        with col2:
                            for i, step in enumerate(progress_steps):
                                status = "✅" if i < step_idx else ("⏳" if i == step_idx else "⭕")
                                st.write(f"{status} {step}")
                    
                    # Show last 10 log lines
                    with log_placeholder.container():
                        st.caption("Processing Logs:")
                        log_text = "\n".join(log_lines[-10:])
                        st.code(log_text, language="text")
        
        except Exception as e:
            st.warning(f"Error reading process output: {str(e)}")
        
        # Wait for process to complete
        stdout, stderr = process.communicate(timeout=timeout)
        accumulated_output.append(stdout)
        
        if stderr:
            log_lines.extend(stderr.split("\n"))
        
        # Check return code
        if process.returncode != 0:
            error_msg = f"Backend execution failed with exit code {process.returncode}"
            with log_placeholder.container():
                st.error(error_msg)
                if stderr:
                    st.code(stderr, language="text")
            return False, None, error_msg
        
        # Wait a moment for file system to catch up
        time.sleep(1)
        
        # Detect newly generated result file
        result_file = get_result_file_before(pre_execution_time)
        
        if not result_file:
            # Fallback: get latest file
            result_file = get_latest_result_file()
        
        if not result_file:
            error_msg = "No result files generated by backend"
            with log_placeholder.container():
                st.error(error_msg)
            return False, None, error_msg
        
        # Load result JSON
        result_data = load_result_json(result_file)
        
        if result_data is None:
            return False, None, "Failed to parse result JSON"
        
        # Success
        success_msg = f"✅ Backend processing complete! Results saved to: {result_file.name}"
        with progress_placeholder.container():
            st.success(success_msg)
        
        with log_placeholder.container():
            st.success("All steps completed successfully!")
        
        return True, result_data, success_msg
    
    except subprocess.TimeoutExpired:
        error_msg = f"Backend execution timed out after {timeout} seconds"
        st.error(error_msg)
        process.kill()
        return False, None, error_msg
    
    except Exception as e:
        error_msg = f"Backend execution error: {str(e)}"
        st.error(error_msg)
        return False, None, error_msg


def validate_uploads() -> Tuple[bool, str]:
    """
    Validate that uploaded files exist and are ready for processing.
    
    Returns:
        Tuple of (valid: bool, message: str)
    """
    jd_dir = PROJECT_ROOT / "uploads" / "jd"
    resumes_dir = PROJECT_ROOT / "uploads" / "resumes"
    
    # Check JD
    if not jd_dir.exists() or not list(jd_dir.glob("*.pdf")):
        return False, "❌ No Job Description PDF found in uploads/jd/"
    
    # Check resumes
    if not resumes_dir.exists() or not list(resumes_dir.glob("*.pdf")):
        return False, "❌ No Resume PDFs found in uploads/resumes/"
    
    jd_count = len(list(jd_dir.glob("*.pdf")))
    resume_count = len(list(resumes_dir.glob("*.pdf")))
    
    return True, f"✅ Ready to analyze: {jd_count} JD, {resume_count} resume(s)"
