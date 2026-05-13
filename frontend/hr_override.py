"""
Human-in-the-Loop Override System for AI HR Resume Shortlisting System.

This module provides a professional recruiter interface for:
- Reviewing AI-generated candidate scores
- Overriding scores and recommendations
- Adding HR notes and risk flags
- Maintaining override history and audit trails
- Exporting decisions and reports

Features:
- Side-by-side AI vs HR score comparison
- Risk flag management
- Override history tracking
- Audit logging
- CSV export functionality
- Real-time metrics dashboard

Author: HR AI System
Date: 2026
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
import uuid


# ==============================================================================
# CONFIGURATION & PATHS
# ==============================================================================

OUTPUTS_DIR = Path("../outputs")
OVERRIDES_DIR = OUTPUTS_DIR / "hr_overrides"
AUDIT_LOG_PATH = OUTPUTS_DIR / "audit_log.json"

# Ensure directories exist
OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
OVERRIDES_DIR.mkdir(parents=True, exist_ok=True)


# ==============================================================================
# HELPER FUNCTIONS - FILE OPERATIONS
# ==============================================================================

def load_candidate_results() -> List[Dict[str, Any]]:
    """
    Load all candidate results from outputs directory.
    
    Returns:
        List[Dict]: List of candidate result dictionaries
    """
    candidates = []
    
    if not OUTPUTS_DIR.exists():
        return candidates
    
    for json_file in OUTPUTS_DIR.glob("*.json"):
        if json_file.name == "audit_log.json":
            continue
        
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
                
                # Handle batch results (list of candidates)
                if isinstance(data, list):
                    candidates.extend(data)
                # Handle single candidate result
                elif isinstance(data, dict) and "candidate_name" in data:
                    candidates.append(data)
        except Exception as e:
            st.warning(f"Could not load {json_file.name}: {str(e)}")
    
    return candidates


def load_override_history(candidate_name: str) -> List[Dict[str, Any]]:
    """
    Load override history for a specific candidate.
    
    Args:
        candidate_name (str): Name of the candidate
    
    Returns:
        List[Dict]: List of override records
    """
    override_file = OVERRIDES_DIR / f"{candidate_name.replace(' ', '_')}_overrides.json"
    
    if not override_file.exists():
        return []
    
    try:
        with open(override_file, "r") as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]
    except Exception as e:
        st.warning(f"Could not load override history: {str(e)}")
        return []


def save_override(candidate_name: str, override_data: Dict[str, Any]) -> bool:
    """
    Save HR override for a candidate.
    Appends to existing history if it exists.
    
    Args:
        candidate_name (str): Name of the candidate
        override_data (Dict): Override data to save
    
    Returns:
        bool: True if successful
    """
    try:
        override_file = OVERRIDES_DIR / f"{candidate_name.replace(' ', '_')}_overrides.json"
        
        # Load existing history
        history = load_override_history(candidate_name)
        
        # Append new override
        history.append(override_data)
        
        # Save updated history
        with open(override_file, "w") as f:
            json.dump(history, f, indent=2, default=str)
        
        return True
    except Exception as e:
        st.error(f"Failed to save override: {str(e)}")
        return False


def append_audit_log(action: str, candidate_name: str, details: Dict[str, Any]) -> bool:
    """
    Append entry to audit log.
    
    Args:
        action (str): Action type (e.g., "OVERRIDE", "EXPORT")
        candidate_name (str): Name of candidate
        details (Dict): Action details
    
    Returns:
        bool: True if successful
    """
    try:
        # Load existing audit log
        audit_log = []
        if AUDIT_LOG_PATH.exists():
            with open(AUDIT_LOG_PATH, "r") as f:
                audit_log = json.load(f)
        
        # Create new entry
        entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "candidate_name": candidate_name,
            "details": details
        }
        
        audit_log.append(entry)
        
        # Save updated log
        with open(AUDIT_LOG_PATH, "w") as f:
            json.dump(audit_log, f, indent=2, default=str)
        
        return True
    except Exception as e:
        st.warning(f"Could not append to audit log: {str(e)}")
        return False


def export_overrides_csv() -> Optional[str]:
    """
    Export all overrides as CSV.
    
    Returns:
        Optional[str]: CSV string or None
    """
    try:
        all_overrides = []
        
        for override_file in OVERRIDES_DIR.glob("*_overrides.json"):
            with open(override_file, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_overrides.extend(data)
                else:
                    all_overrides.append(data)
        
        if not all_overrides:
            st.warning("No override records found")
            return None
        
        df = pd.DataFrame(all_overrides)
        return df.to_csv(index=False)
    except Exception as e:
        st.error(f"Failed to export overrides: {str(e)}")
        return None


# ==============================================================================
# HELPER FUNCTIONS - DISPLAY & ANALYSIS
# ==============================================================================

def get_score_color(score: float) -> str:
    """Get color code based on score."""
    if score >= 85:
        return "#10B981"  # Green
    elif score >= 70:
        return "#3B82F6"  # Blue
    elif score >= 50:
        return "#F59E0B"  # Orange
    else:
        return "#EF4444"  # Red


def get_recommendation_color(recommendation: str) -> str:
    """Get color code based on recommendation."""
    if "hire" in recommendation.lower():
        return "#10B981"
    elif "maybe" in recommendation.lower() or "consider" in recommendation.lower():
        return "#F59E0B"
    else:
        return "#EF4444"


def get_hr_status_emoji(status: str) -> str:
    """Get emoji for HR status."""
    emojis = {
        "Shortlisted": "✅",
        "Rejected": "❌",
        "Interview Scheduled": "📅",
        "Under Review": "⏳",
        "Final Approved": "🎯",
        "On Hold": "⏸️"
    }
    return emojis.get(status, "•")


def extract_score_components(candidate: Dict[str, Any]) -> Dict[str, float]:
    """Extract individual score components from candidate data."""
    breakdown = candidate.get("breakdown", {})
    
    components = {}
    for category in ["skills", "experience", "education", "projects", "communication"]:
        if category in breakdown:
            score = breakdown[category].get("score", 0)
            components[category.capitalize()] = (score / 10) * 100  # Convert to 0-100
        else:
            components[category.capitalize()] = 0
    
    return components


def get_override_summary(candidate_name: str) -> Optional[Dict[str, Any]]:
    """Get the most recent override for a candidate."""
    history = load_override_history(candidate_name)
    return history[-1] if history else None


def calculate_metrics(candidates: List[Dict[str, Any]]) -> Dict[str, int]:
    """Calculate dashboard metrics."""
    total = len(candidates)
    
    ai_shortlisted = sum(
        1 for c in candidates
        if c.get("final_score", 0) >= 75
    )
    
    hr_modified = sum(
        1 for c in candidates
        if get_override_summary(c.get("candidate_name", "")) is not None
    )
    
    final_approved = sum(
        1 for c in candidates
        if get_override_summary(c.get("candidate_name", "")) 
        and get_override_summary(c.get("candidate_name", "")).get("hr_status") == "Final Approved"
    )
    
    return {
        "total": total,
        "ai_shortlisted": ai_shortlisted,
        "hr_modified": hr_modified,
        "final_approved": final_approved
    }


# ==============================================================================
# RENDERING FUNCTIONS - HEADER & METRICS
# ==============================================================================

def render_header(metrics: Dict[str, int]) -> None:
    """Render dashboard header with metrics."""
    st.markdown("# 👥 Human Review & Override System")
    st.markdown("**AI-assisted screening with recruiter decision control**")
    st.markdown("---")
    
    # Metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Candidates", metrics["total"])
    
    with col2:
        st.metric("AI Shortlisted", metrics["ai_shortlisted"])
    
    with col3:
        st.metric("HR Modified", metrics["hr_modified"])
    
    with col4:
        st.metric("Final Approved", metrics["final_approved"])
    
    st.markdown("---")


def render_candidate_selector(candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Render candidate selection panel in sidebar.
    
    Returns:
        Optional[Dict]: Selected candidate data or None
    """
    st.sidebar.markdown("## 👤 Select Candidate")
    
    if not candidates:
        st.sidebar.warning("⚠️ No candidates found")
        return None
    
    # Debug info
    st.sidebar.write(f"📊 Available: {len(candidates)} candidates")
    
    # Sort by score
    sorted_candidates = sorted(
        candidates,
        key=lambda x: x.get("final_score", 0),
        reverse=True
    )
    
    # Simple selector - just show all candidates sorted by score
    candidate_labels = []
    for c in sorted_candidates:
        name = c.get("candidate_name", "Unknown")
        score = c.get("final_score", 0)
        rank = c.get("rank", "?")
        label = f"{name} — {score:.1f}/100"
        candidate_labels.append(label)
    
    # Default to first candidate
    selected_idx = st.sidebar.selectbox(
        "Choose a candidate:",
        range(len(sorted_candidates)),
        format_func=lambda i: candidate_labels[i],
        index=0,
        key="candidate_selector_main"
    )
    
    return sorted_candidates[selected_idx]


# ==============================================================================
# RENDERING FUNCTIONS - AI ANALYSIS DISPLAY
# ==============================================================================

def render_ai_analysis(candidate: Dict[str, Any]) -> None:
    """Render AI analysis section - simplified version."""
    st.subheader("🤖 AI Analysis")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score = candidate.get("final_score", 0)
        color = get_score_color(score)
        st.markdown(f"""
        <div style="
            background: {color}15;
            border-left: 4px solid {color};
            padding: 16px;
            border-radius: 8px;
            text-align: center;
        ">
            <div style="font-size: 12px; color: #6B7280; margin-bottom: 8px;">AI Final Score</div>
            <div style="font-size: 32px; font-weight: 700; color: {color};">{score:.1f}</div>
            <div style="font-size: 11px; color: #9CA3AF; margin-top: 4px;">/100</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        rank = candidate.get("rank", "N/A")
        st.markdown(f"""
        <div style="
            background: #3B82F615;
            border-left: 4px solid #3B82F6;
            padding: 16px;
            border-radius: 8px;
            text-align: center;
        ">
            <div style="font-size: 12px; color: #6B7280; margin-bottom: 8px;">Rank</div>
            <div style="font-size: 32px; font-weight: 700; color: #3B82F6;">#{rank}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        rec = candidate.get("recommendation", "Not Rated")
        color = get_recommendation_color(rec)
        st.markdown(f"""
        <div style="
            background: {color}15;
            border-left: 4px solid {color};
            padding: 16px;
            border-radius: 8px;
            text-align: center;
        ">
            <div style="font-size: 12px; color: #6B7280; margin-bottom: 8px;">Recommendation</div>
            <div style="font-size: 14px; font-weight: 600; color: {color}; text-align: center;">{rec}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Brief justification from breakdown
    breakdown = candidate.get("breakdown", {})
    if breakdown and breakdown.get("skills", {}).get("justification"):
        st.markdown("**AI Justification:**")
        st.write(breakdown["skills"].get("justification", "No details available"))
        missing_skills = candidate.get("missing_skills", [])
        if missing_skills:
            st.markdown("**Missing Skills:**")
            for skill in missing_skills[:5]:
                st.markdown(f"• {skill}")


# ==============================================================================
# RENDERING FUNCTIONS - HR OVERRIDE PANEL
# ==============================================================================

def render_hr_override_panel(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """
    Render HR override control panel.
    
    Returns:
        Dict: Override data from HR input
    """
    st.subheader("👨‍💼 HR Override & Decision Panel")
    
    override_data = {
        "candidate_name": candidate.get("candidate_name", "Unknown"),
        "original_ai_score": candidate.get("final_score", 0),
        "original_recommendation": candidate.get("recommendation", "Unknown"),
    }
    
    # Get existing override if any
    existing_override = get_override_summary(candidate.get("candidate_name", ""))
    
    # Initialize session state for override form
    if "override_score_input" not in st.session_state:
        st.session_state.override_score_input = (
            existing_override.get("hr_override_score", override_data["original_ai_score"])
            if existing_override else override_data["original_ai_score"]
        )
    
    if "override_notes_input" not in st.session_state:
        st.session_state.override_notes_input = (
            existing_override.get("reviewer_notes", "")
            if existing_override else ""
        )
    
    # A. Manual Score Override
    st.markdown("#### 📊 A. Manual Score Override")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        override_enabled = st.checkbox(
            "Override AI Score",
            value=existing_override is not None if existing_override else False,
            key="override_enabled"
        )
    
    if override_enabled:
        with col2:
            hr_score = st.number_input(
                "HR Score",
                min_value=0,
                max_value=100,
                value=int(st.session_state.override_score_input),
                key="hr_score_input"
            )
            st.session_state.override_score_input = hr_score
            override_data["hr_override_score"] = hr_score
    else:
        override_data["hr_override_score"] = override_data["original_ai_score"]
    
    st.markdown("---")
    
    # B. Recommendation Override
    st.markdown("#### 🎯 B. Recommendation Override")
    
    rec_options = ["Hire", "Strong Hire", "Maybe", "Reject", "Hold"]
    rec_default = (
        existing_override.get("hr_recommendation", override_data["original_recommendation"])
        if existing_override else override_data["original_recommendation"]
    )
    
    hr_recommendation = st.selectbox(
        "HR Recommendation",
        rec_options,
        index=rec_options.index(rec_default) if rec_default in rec_options else 0,
        key="hr_recommendation"
    )
    override_data["hr_recommendation"] = hr_recommendation
    
    st.markdown("---")
    
    # C. HR Decision Status
    st.markdown("#### 📋 C. HR Decision Status")
    
    status_options = ["Shortlisted", "Rejected", "Interview Scheduled", "Under Review", "Final Approved", "On Hold"]
    status_default = (
        existing_override.get("hr_status", "Under Review")
        if existing_override else "Under Review"
    )
    
    hr_status = st.selectbox(
        "Decision Status",
        status_options,
        index=status_options.index(status_default) if status_default in status_options else 3,
        key="hr_status"
    )
    override_data["hr_status"] = hr_status
    
    st.markdown("---")
    
    # D. HR Notes
    st.markdown("#### 💬 D. HR Notes & Comments")
    
    reviewer_notes = st.text_area(
        "Add your review notes:",
        value=st.session_state.override_notes_input,
        height=120,
        key="reviewer_notes_textarea"
    )
    st.session_state.override_notes_input = reviewer_notes
    override_data["reviewer_notes"] = reviewer_notes
    
    st.markdown("---")
    
    # E. Risk Flags
    st.markdown("#### 🚩 E. Risk Flags")
    
    risk_flags = []
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.checkbox("Skill Gap", key="flag_skill_gap"):
            risk_flags.append("Skill Gap")
        if st.checkbox("Communication Concern", key="flag_communication"):
            risk_flags.append("Communication Concern")
        if st.checkbox("Experience Concern", key="flag_experience"):
            risk_flags.append("Experience Concern")
    
    with col2:
        if st.checkbox("Fake Resume Suspicion", key="flag_fake"):
            risk_flags.append("Fake Resume Suspicion")
        if st.checkbox("Overqualified", key="flag_overqualified"):
            risk_flags.append("Overqualified")
        if st.checkbox("Underqualified", key="flag_underqualified"):
            risk_flags.append("Underqualified")
    
    override_data["risk_flags"] = risk_flags
    
    st.markdown("---")
    
    # F. Priority Level
    st.markdown("#### ⭐ F. Priority Level")
    
    priority_options = ["High", "Medium", "Low"]
    priority_default = (
        existing_override.get("priority", "Medium")
        if existing_override else "Medium"
    )
    
    priority = st.select_slider(
        "Priority",
        options=priority_options,
        value=priority_default,
        key="priority_level"
    )
    override_data["priority"] = priority
    
    st.markdown("---")
    
    # Reviewer info
    st.markdown("#### 👤 Reviewer Information")
    
    reviewer_name = st.text_input(
        "Your Name",
        value=st.session_state.get("reviewer_name", ""),
        key="reviewer_name_input"
    )
    st.session_state.reviewer_name = reviewer_name
    override_data["reviewer_name"] = reviewer_name
    
    # Add metadata
    override_data["override_timestamp"] = datetime.now().isoformat()
    override_data["was_modified"] = (
        override_data["hr_override_score"] != override_data["original_ai_score"] or
        override_data["hr_recommendation"] != override_data["original_recommendation"]
    )
    
    return override_data


# ==============================================================================
# RENDERING FUNCTIONS - COMPARISON & ACTIONS
# ==============================================================================

def render_score_comparison(original_score: float, hr_score: float, original_rec: str, hr_rec: str) -> None:
    """Render side-by-side score comparison."""
    st.subheader("📊 Score Comparison: AI vs HR")
    
    col1, col2, col3 = st.columns([1.5, 0.5, 1.5])
    
    with col1:
        st.markdown("#### 🤖 AI Score")
        color1 = get_score_color(original_score)
        st.markdown(f"""
        <div style="
            background: {color1}15;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        ">
            <div style="font-size: 28px; font-weight: 700; color: {color1};">{original_score:.1f}</div>
            <div style="font-size: 12px; color: #6B7280; margin-top: 8px;">{original_rec}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if hr_score != original_score:
            diff_pct = ((hr_score - original_score) / original_score * 100) if original_score > 0 else 0
            arrow = "📈" if diff_pct > 0 else "📉"
            color = "#10B981" if diff_pct > 0 else "#EF4444"
            
            st.markdown(f"""
            <div style="
                text-align: center;
                padding-top: 40px;
                font-size: 28px;
            ">
            {arrow}
            </div>
            <div style="
                text-align: center;
                color: {color};
                font-weight: 700;
                margin-top: 8px;
            ">
            {diff_pct:+.1f}%
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("<div style='padding-top: 40px; text-align: center; font-size: 20px;'>—</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown("#### 👨‍💼 HR Score")
        color2 = get_score_color(hr_score)
        st.markdown(f"""
        <div style="
            background: {color2}15;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        ">
            <div style="font-size: 28px; font-weight: 700; color: {color2};">{hr_score:.1f}</div>
            <div style="font-size: 12px; color: #6B7280; margin-top: 8px;">{hr_rec}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")


def render_override_history(candidate_name: str) -> None:
    """Render override history for candidate."""
    st.subheader("📜 Override History")
    
    history = load_override_history(candidate_name)
    
    if not history:
        st.info("No override history for this candidate")
        return
    
    # Show most recent first
    for idx, record in enumerate(reversed(history)):
        with st.expander(f"Override #{len(history) - idx} — {record.get('override_timestamp', 'Unknown')[:10]}", expanded=(idx == 0)):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Score Change:**")
                original = record.get("original_ai_score", "N/A")
                modified = record.get("hr_override_score", "N/A")
                st.write(f"AI: **{original}** → HR: **{modified}**")
                
                st.markdown("**Recommendation Change:**")
                st.write(f"{record.get('original_recommendation', 'N/A')} → {record.get('hr_recommendation', 'N/A')}")
            
            with col2:
                st.markdown("**HR Status:**")
                emoji = get_hr_status_emoji(record.get("hr_status", ""))
                st.write(f"{emoji} {record.get('hr_status', 'N/A')}")
                
                st.markdown("**Priority:**")
                st.write(record.get("priority", "N/A"))
            
            if record.get("risk_flags"):
                st.markdown("**Risk Flags:**")
                for flag in record.get("risk_flags", []):
                    st.write(f"🚩 {flag}")
            
            if record.get("reviewer_notes"):
                st.markdown("**Notes:**")
                st.info(record.get("reviewer_notes"))
            
            st.markdown("**Reviewer:** " + record.get("reviewer_name", "Unknown"))


# ==============================================================================
# MAIN RENDERING FUNCTION
# ==============================================================================

def render_hr_override(candidate_results: Optional[List[Dict[str, Any]]] = None) -> None:
    """
    Main function to render HR override system.
    
    Args:
        candidate_results (Optional[List[Dict]]): Candidate results from backend
    """
    # Handle case where batch_data is a JSON string
    if isinstance(candidate_results, str):
        try:
            candidate_results = json.loads(candidate_results)
        except Exception as e:
            st.warning(f"Could not parse candidate results: {str(e)}")
            candidate_results = None
    
    # Handle case where candidate_results is a dict with candidates/results key
    if isinstance(candidate_results, dict):
        if "candidates" in candidate_results:
            candidate_results = candidate_results["candidates"]
        elif "results" in candidate_results:
            candidate_results = candidate_results["results"]
        else:
            # If it's a single candidate dict, wrap it in a list
            candidate_results = [candidate_results]
    
    # Load candidates from outputs if not provided
    if not candidate_results:
        candidate_results = load_candidate_results()
    
    if not candidate_results:
        st.warning("⚠️ No candidate results found. Please run the backend pipeline first.")
        return
    
    # Ensure candidate_results is a list
    if not isinstance(candidate_results, list):
        st.warning("Invalid candidate data format")
        return
    
    # Calculate metrics
    metrics = calculate_metrics(candidate_results)
    
    # Render header
    render_header(metrics)
    
    # Debug: Show candidate count
    st.sidebar.write(f"📊 Total candidates available: {len(candidate_results)}")
    
    # Candidate selection
    selected_candidate = render_candidate_selector(candidate_results)
    
    if not selected_candidate:
        st.warning("Please select a candidate to review")
        return
    
    # Main content area
    st.markdown(f"## {selected_candidate.get('candidate_name', 'Unknown')}")
    st.markdown("---")
    
    # Create tabs for organized display
    tab1, tab2, tab3, tab4 = st.tabs(["AI Analysis", "HR Override", "History", "Export"])
    
    with tab1:
        render_ai_analysis(selected_candidate)
    
    with tab2:
        # HR Override Form
        override_data = render_hr_override_panel(selected_candidate)
        
        st.markdown("---")
        
        # Score comparison
        render_score_comparison(
            override_data["original_ai_score"],
            override_data.get("hr_override_score", override_data["original_ai_score"]),
            override_data["original_recommendation"],
            override_data["hr_recommendation"]
        )
        
        # Save action button
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("💾 Save Override", use_container_width=True, type="primary"):
                # Validate inputs
                if not override_data.get("reviewer_name"):
                    st.error("Please enter your name as reviewer")
                else:
                    # Save override
                    if save_override(override_data["candidate_name"], override_data):
                        # Log to audit trail
                        append_audit_log(
                            "OVERRIDE_CREATED",
                            override_data["candidate_name"],
                            {
                                "original_score": override_data["original_ai_score"],
                                "new_score": override_data.get("hr_override_score", override_data["original_ai_score"]),
                                "reviewer": override_data["reviewer_name"],
                                "status": override_data["hr_status"]
                            }
                        )
                        
                        st.success(f"✅ Override saved for {override_data['candidate_name']}")
                        st.balloons()
        
        with col2:
            if st.button("🔄 Reset Form", use_container_width=True):
                st.session_state.override_score_input = override_data["original_ai_score"]
                st.session_state.override_notes_input = ""
                st.rerun()
    
    with tab3:
        render_override_history(selected_candidate.get("candidate_name", ""))
    
    with tab4:
        st.subheader("📥 Export Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Export single candidate
            candidate_json = json.dumps(selected_candidate, indent=2, default=str)
            st.download_button(
                label="📄 Download Candidate JSON",
                data=candidate_json,
                file_name=f"{selected_candidate.get('candidate_name', 'candidate').replace(' ', '_')}_profile.json",
                mime="application/json"
            )
        
        with col2:
            # Export all overrides
            csv_data = export_overrides_csv()
            if csv_data:
                st.download_button(
                    label="📊 Download All Overrides CSV",
                    data=csv_data,
                    file_name=f"hr_overrides_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
                
                # Log export action
                append_audit_log(
                    "EXPORT_OVERRIDES_CSV",
                    "bulk",
                    {"timestamp": datetime.now().isoformat()}
                )
        
        with col3:
            # Export final approved candidates
            approved = [
                c for c in candidate_results
                if get_override_summary(c.get("candidate_name", ""))
                and get_override_summary(c.get("candidate_name", "")).get("hr_status") == "Final Approved"
            ]
            
            if approved:
                approved_json = json.dumps(approved, indent=2, default=str)
                st.download_button(
                    label="✅ Download Approved Candidates",
                    data=approved_json,
                    file_name=f"final_approved_candidates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
                
                # Log export action
                append_audit_log(
                    "EXPORT_APPROVED",
                    "bulk",
                    {"approved_count": len(approved), "timestamp": datetime.now().isoformat()}
                )


if __name__ == "__main__":
    # For testing purposes
    render_hr_override()
