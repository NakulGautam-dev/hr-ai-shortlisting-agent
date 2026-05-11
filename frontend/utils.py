"""
Frontend Utility Functions

Helper functions for data processing, formatting, and common operations
used across the Streamlit dashboard.
"""

import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime


# Project structure
PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUTS_DIR = PROJECT_ROOT / "outputs"


# ==============================================================================
# JSON LOADING & DATA PROCESSING
# ==============================================================================

def load_latest_results_json() -> Optional[Dict[str, Any]]:
    """
    Load the most recently generated results JSON file.
    
    Returns:
        Parsed JSON dict or None if no file found
    """
    if not OUTPUTS_DIR.exists():
        return None
    
    result_files = sorted(
        OUTPUTS_DIR.glob("*results*.json"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    if not result_files:
        return None
    
    try:
        with open(result_files[0], 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading JSON: {str(e)}")
        return None


def extract_candidate_dataframe(batch_data: Dict) -> Optional[pd.DataFrame]:
    """
    Convert batch results JSON into a pandas DataFrame.
    
    Args:
        batch_data (Dict): Batch results dictionary
    
    Returns:
        pandas DataFrame with candidate information or None
    """
    try:
        if isinstance(batch_data, list):
            df = pd.DataFrame(batch_data)
        elif isinstance(batch_data, dict):
            if "candidates" in batch_data:
                df = pd.DataFrame(batch_data["candidates"])
            elif "results" in batch_data:
                df = pd.DataFrame(batch_data["results"])
            else:
                df = pd.DataFrame([batch_data])
        else:
            return None
        
        # Ensure required columns
        if "final_score" not in df.columns or "candidate_name" not in df.columns:
            return None
        
        # Add rank if missing
        if "rank" not in df.columns:
            df = df.sort_values("final_score", ascending=False).reset_index(drop=True)
            df["rank"] = range(1, len(df) + 1)
        
        return df.sort_values("final_score", ascending=False).reset_index(drop=True)
    
    except Exception as e:
        print(f"Error extracting dataframe: {str(e)}")
        return None


# ==============================================================================
# STATUS CLASSIFICATION
# ==============================================================================

def get_candidate_status(score: float) -> Tuple[str, str, str]:
    """
    Classify candidate status based on score.
    
    Args:
        score (float): Final score (0-100)
    
    Returns:
        Tuple of (status_label, emoji, color_hex)
    """
    if score >= 75:
        return "Shortlisted", "🟢", "#10b981"
    elif score >= 50:
        return "Consider", "🟡", "#f59e0b"
    else:
        return "Rejected", "🔴", "#ef4444"


def get_score_color(score: float) -> str:
    """
    Get color for score visualization.
    
    Args:
        score (float): Score (0-100)
    
    Returns:
        Color hex code
    """
    if score >= 85:
        return "#10b981"  # Green
    elif score >= 70:
        return "#3b82f6"  # Blue
    elif score >= 50:
        return "#f59e0b"  # Orange
    else:
        return "#ef4444"  # Red


def get_score_class(score: float) -> str:
    """
    Get CSS-style class name for score.
    """
    if score >= 85:
        return "excellent"
    elif score >= 70:
        return "good"
    elif score >= 50:
        return "fair"
    else:
        return "poor"


# ==============================================================================
# FORMATTING & DISPLAY
# ==============================================================================

def format_score(score: float, decimals: int = 1) -> str:
    """Format score for display."""
    return f"{score:.{decimals}f}"


def format_percentage(value: float, decimals: int = 1) -> str:
    """Format percentage."""
    return f"{value:.{decimals}f}%"


def get_recommendation_text(score: float) -> str:
    """
    Generate hiring recommendation based on score.
    
    Args:
        score (float): Candidate final score
    
    Returns:
        Recommendation text
    """
    if score >= 85:
        return "🌟 Exceptional match. High priority for interview."
    elif score >= 75:
        return "✅ Strong candidate. Recommended for interview."
    elif score >= 65:
        return "👍 Good candidate. Consider for further evaluation."
    elif score >= 50:
        return "⚠️ Moderate candidate. Further evaluation recommended."
    elif score >= 30:
        return "📋 Weak match. Review if quota allows."
    else:
        return "❌ Does not meet minimum requirements."


def get_component_status(component_name: str, score: float) -> str:
    """
    Get formatted status for a component score.
    
    Args:
        component_name (str): Component name (Skills, Experience, etc.)
        score (float): Score (0-10)
    
    Returns:
        Formatted status string
    """
    if score >= 8:
        return f"✅ {component_name}: Excellent ({score:.0f}/10)"
    elif score >= 6:
        return f"👍 {component_name}: Good ({score:.0f}/10)"
    elif score >= 4:
        return f"⚠️ {component_name}: Fair ({score:.0f}/10)"
    else:
        return f"❌ {component_name}: Weak ({score:.0f}/10)"


# ==============================================================================
# DATA AGGREGATION
# ==============================================================================

def calculate_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate summary statistics from candidate dataframe.
    
    Args:
        df (pd.DataFrame): Candidate dataframe
    
    Returns:
        Dictionary with statistics
    """
    if df is None or len(df) == 0:
        return {}
    
    scores = df["final_score"]
    
    return {
        "total_candidates": len(df),
        "average_score": float(scores.mean()),
        "median_score": float(scores.median()),
        "std_dev": float(scores.std()),
        "min_score": float(scores.min()),
        "max_score": float(scores.max()),
        "shortlisted_count": len(df[df["final_score"] >= 75]),
        "consider_count": len(df[(df["final_score"] >= 50) & (df["final_score"] < 75)]),
        "rejected_count": len(df[df["final_score"] < 50]),
    }


def get_top_candidates(df: pd.DataFrame, n: int = 5) -> List[Dict[str, Any]]:
    """
    Get top N candidates by score.
    
    Args:
        df (pd.DataFrame): Candidate dataframe
        n (int): Number of top candidates
    
    Returns:
        List of top candidate dictionaries
    """
    if df is None or len(df) == 0:
        return []
    
    top = df.nlargest(n, "final_score")
    return top.to_dict("records")


# ==============================================================================
# SKILL EXTRACTION
# ==============================================================================

def extract_matched_missing_skills(candidate_data: Dict) -> Tuple[List[str], List[str]]:
    """
    Extract matched and missing skills from candidate analysis.
    
    Args:
        candidate_data (Dict): Candidate record with analysis
    
    Returns:
        Tuple of (matched_skills, missing_skills)
    """
    matched_skills = []
    missing_skills = []
    
    try:
        analysis = candidate_data.get("analysis", {})
        if not isinstance(analysis, dict):
            return matched_skills, missing_skills
        
        # Try different field names for matched skills
        for key in ["matching_skills", "matched_skills", "matched"]:
            if key in analysis:
                matched = analysis[key]
                if isinstance(matched, list):
                    for item in matched:
                        if isinstance(item, dict):
                            skill = item.get("jd_skill") or item.get("skill") or item.get("name")
                            if skill:
                                matched_skills.append(str(skill))
                        else:
                            matched_skills.append(str(item))
                break
        
        # Missing skills
        if "missing_skills" in analysis:
            missing = analysis["missing_skills"]
            if isinstance(missing, list):
                missing_skills = [str(s) for s in missing]
    
    except Exception as e:
        print(f"Error extracting skills: {str(e)}")
    
    return matched_skills, missing_skills


def extract_strengths_weaknesses(candidate_data: Dict) -> Tuple[List[str], List[str]]:
    """
    Extract strengths and weaknesses from candidate analysis.
    
    Args:
        candidate_data (Dict): Candidate record
    
    Returns:
        Tuple of (strengths, weaknesses)
    """
    strengths = []
    weaknesses = []
    
    try:
        analysis = candidate_data.get("analysis", {})
        if not isinstance(analysis, dict):
            return strengths, weaknesses
        
        if "strengths" in analysis:
            s = analysis["strengths"]
            strengths = s if isinstance(s, list) else []
        
        if "weaknesses" in analysis:
            w = analysis["weaknesses"]
            weaknesses = w if isinstance(w, list) else []
    
    except Exception:
        pass
    
    return strengths, weaknesses


# ==============================================================================
# COMPONENT SCORES
# ==============================================================================

def extract_component_scores(candidate_data: Dict) -> Dict[str, float]:
    """
    Extract individual component scores from candidate data.
    
    Args:
        candidate_data (Dict): Candidate record
    
    Returns:
        Dictionary of component scores
    """
    components = candidate_data.get("components", {})
    
    if isinstance(components, dict):
        return {
            "skills": components.get("skills", 0),
            "experience": components.get("experience", 0),
            "education": components.get("education", 0),
            "projects": components.get("projects", 0),
            "communication": components.get("communication", 0),
        }
    
    return {
        "skills": 0,
        "experience": 0,
        "education": 0,
        "projects": 0,
        "communication": 0,
    }


# ==============================================================================
# FILE OPERATIONS
# ==============================================================================

def get_upload_status() -> Dict[str, int]:
    """
    Get count of uploaded files.
    
    Returns:
        Dictionary with JD and resume counts
    """
    jd_dir = PROJECT_ROOT / "uploads" / "jd"
    resumes_dir = PROJECT_ROOT / "uploads" / "resumes"
    
    jd_count = len(list(jd_dir.glob("*.pdf"))) if jd_dir.exists() else 0
    resume_count = len(list(resumes_dir.glob("*.pdf"))) if resumes_dir.exists() else 0
    
    return {
        "jd_count": jd_count,
        "resume_count": resume_count,
    }


def clear_uploads():
    """
    Clear uploaded files (for reset/new analysis).
    """
    jd_dir = PROJECT_ROOT / "uploads" / "jd"
    resumes_dir = PROJECT_ROOT / "uploads" / "resumes"
    
    for file in jd_dir.glob("*.pdf"):
        file.unlink()
    
    for file in resumes_dir.glob("*.pdf"):
        file.unlink()


# ==============================================================================
# DATETIME UTILITIES
# ==============================================================================

def get_timestamp() -> str:
    """Get current timestamp formatted for display."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_file_timestamp(file_path: Path) -> str:
    """Get file modification timestamp."""
    mtime = file_path.stat().st_mtime
    return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")


def format_duration(seconds: float) -> str:
    """Format duration in seconds to readable string."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m {int(seconds % 60)}s"
    else:
        return f"{int(seconds / 3600)}h {int((seconds % 3600) / 60)}m"


def get_recommendation_text(score: float) -> str:
    """
    Generate recommendation text based on score.
    
    Args:
        score (float): Candidate final score
    
    Returns:
        Recommendation text
    """
    if score >= 85:
        return "✅ Exceptional match. High priority for interview."
    elif score >= 75:
        return "✅ Strong candidate. Recommended for interview."
    elif score >= 65:
        return "ℹ️ Good candidate. Consider for further evaluation."
    elif score >= 50:
        return "⚠️ Moderate candidate. Further evaluation recommended."
    else:
        return "❌ Does not meet minimum requirements."


def get_matched_skills(candidate_data: Dict) -> Tuple[List[str], List[str]]:
    """
    Extract matched and missing skills from candidate analysis.
    
    Args:
        candidate_data (Dict): Candidate record with analysis
    
    Returns:
        Tuple of (matched_skills, missing_skills)
    """
    matched_skills = []
    missing_skills = []
    
    try:
        if "analysis" in candidate_data and isinstance(candidate_data["analysis"], dict):
            analysis = candidate_data["analysis"]
            
            # Try both possible keys for matched skills
            matched = analysis.get("matching_skills") or analysis.get("matched_skills", [])
            if isinstance(matched, list):
                matched_skills = [
                    s.get("jd_skill", str(s)) if isinstance(s, dict) else str(s)
                    for s in matched
                ]
            
            # Get missing skills
            missing = analysis.get("missing_skills", [])
            if isinstance(missing, list):
                missing_skills = [str(s) for s in missing]
    
    except Exception as e:
        print(f"Error extracting skills: {str(e)}")
    
    return matched_skills, missing_skills
