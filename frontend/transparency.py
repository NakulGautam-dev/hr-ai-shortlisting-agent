"""
AI vs HR Override Transparency System

This module implements enterprise-grade transparency for the AI HR Shortlisting System.

Features:
- Load and merge AI scores with HR overrides
- Calculate final display scores with human judgment
- Track override deltas and changes
- Generate audit trails
- Provide explainability for all score changes
- Support enterprise ATS-style workflows

The system ensures all scoring decisions are:
1. Transparent - show AI and HR scores separately
2. Auditable - track all changes with timestamps
3. Explainable - provide reasoning for overrides
4. Professional - enterprise-ready UI/UX
"""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

# ==============================================================================
# CONFIGURATION
# ==============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
HR_OVERRIDES_DIR = OUTPUTS_DIR / "hr_overrides"
AUDIT_LOG_FILE = OUTPUTS_DIR / "audit_log.json"


# ==============================================================================
# DATA LOADING FUNCTIONS
# ==============================================================================

@st.cache_data(ttl=60)
def load_candidate_results() -> Optional[List[Dict[str, Any]]]:
    """
    Load AI-generated candidate results from outputs directory.
    
    Returns:
        List of candidate dictionaries or None if not found
    """
    try:
        # Find latest results file
        results_files = sorted(OUTPUTS_DIR.glob("shortlisting_results_*.json"), reverse=True)
        
        if not results_files:
            return None
        
        with open(results_files[0], 'r') as f:
            data = json.load(f)
        
        # Ensure data is a list
        if isinstance(data, dict):
            if "candidates" in data:
                return data["candidates"]
            elif "results" in data:
                return data["results"]
            else:
                return [data]
        
        return data if isinstance(data, list) else None
    
    except Exception as e:
        st.error(f"Error loading candidate results: {str(e)}")
        return None


@st.cache_data(ttl=60)
def load_hr_overrides() -> Dict[str, Dict[str, Any]]:
    """
    Load all HR override records from hr_overrides directory.
    
    Returns:
        Dictionary mapping candidate names to their latest override data
    """
    overrides = {}
    
    try:
        if not HR_OVERRIDES_DIR.exists():
            return overrides
        
        for override_file in HR_OVERRIDES_DIR.glob("*_overrides.json"):
            try:
                with open(override_file, 'r') as f:
                    data = json.load(f)
                
                # Handle different file formats
                if isinstance(data, list) and len(data) > 0:
                    # Latest override is last in list (append-only)
                    latest = data[-1]
                    candidate_name = latest.get("candidate_name", "Unknown")
                    overrides[candidate_name] = latest
                elif isinstance(data, dict):
                    candidate_name = data.get("candidate_name", "Unknown")
                    overrides[candidate_name] = data
            
            except Exception as e:
                st.warning(f"Error loading override file {override_file.name}: {str(e)}")
                continue
    
    except Exception as e:
        st.warning(f"Error loading HR overrides: {str(e)}")
    
    return overrides


def load_audit_log() -> List[Dict[str, Any]]:
    """
    Load audit trail of all override actions.
    
    Returns:
        List of audit log entries
    """
    try:
        if AUDIT_LOG_FILE.exists():
            with open(AUDIT_LOG_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        st.warning(f"Error loading audit log: {str(e)}")
    
    return []


# ==============================================================================
# DATA MERGING AND TRANSFORMATION
# ==============================================================================

def calculate_final_display_score(
    ai_score: float,
    hr_override_score: Optional[float] = None,
    was_modified: bool = False
) -> float:
    """
    Calculate the final display score using the scoring precedence logic.
    
    Args:
        ai_score: Original AI-generated score
        hr_override_score: HR-adjusted score (if modified)
        was_modified: Whether candidate was modified by HR
    
    Returns:
        Final score to display in rankings
    """
    if was_modified and hr_override_score is not None:
        return hr_override_score
    return ai_score


def calculate_override_delta(ai_score: float, hr_score: Optional[float] = None) -> float:
    """
    Calculate the delta (change) between AI and HR scores.
    
    Args:
        ai_score: Original AI score
        hr_score: HR-adjusted score
    
    Returns:
        Delta as float (positive = increase, negative = decrease, 0 = no change)
    """
    if hr_score is None:
        return 0.0
    return round(hr_score - ai_score, 1)


def get_override_status_badge(was_modified: bool, hr_status: Optional[str] = None) -> Tuple[str, str, str]:
    """
    Get badge info for override status.
    
    Args:
        was_modified: Whether candidate was modified by HR
        hr_status: HR decision status
    
    Returns:
        Tuple of (badge_text, color_code, badge_emoji)
    """
    if hr_status == "Final Approved":
        return ("Final Approved", "#10B981", "✅")
    elif hr_status == "Rejected":
        return ("Rejected", "#EF4444", "❌")
    elif hr_status == "Interview Scheduled":
        return ("Interview Scheduled", "#F59E0B", "📅")
    elif was_modified:
        return ("HR Modified", "#3B82F6", "👤")
    elif hr_status == "Under Review":
        return ("Under Review", "#F59E0B", "👀")
    else:
        return ("AI Only", "#9CA3AF", "🤖")


def get_priority_badge(priority: Optional[str] = None) -> Tuple[str, str]:
    """
    Get badge info for priority level.
    
    Args:
        priority: Priority level (High, Medium, Low)
    
    Returns:
        Tuple of (badge_text, color_code)
    """
    if priority == "High":
        return ("🔴 High", "#EF4444")
    elif priority == "Medium":
        return ("🟠 Medium", "#F59E0B")
    else:
        return ("🟢 Low", "#10B981")


def merge_ai_and_hr_data(
    ai_candidates: List[Dict[str, Any]],
    hr_overrides: Dict[str, Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Merge AI candidate results with HR override data.
    
    Creates unified candidate records with:
    - Original AI scores and analysis
    - HR override scores and decisions (if modified)
    - Final display scores
    - Delta calculations
    - Override metadata (reviewer, timestamp, notes)
    
    Args:
        ai_candidates: List of AI-generated candidate results
        hr_overrides: Dictionary of HR override records
    
    Returns:
        List of merged candidate dictionaries with all transparency data
    """
    merged = []
    
    for candidate in ai_candidates:
        candidate_name = candidate.get("candidate_name", "Unknown")
        
        # Create merged record starting with AI data
        merged_record = {
            "candidate_name": candidate_name,
            "rank": candidate.get("rank", 0),
            "ai_score": candidate.get("final_score", 0),
            "breakdown": candidate.get("breakdown", {}),
            "recommendation": candidate.get("recommendation", ""),
            "was_modified": False,
            "hr_override_score": None,
            "hr_status": "Not Reviewed",
            "hr_recommendation": None,
            "reviewer_name": None,
            "override_timestamp": None,
            "override_notes": None,
            "override_reason": None,
            "risk_flags": [],
            "priority": "Medium"
        }
        
        # Merge with HR override if exists
        if candidate_name in hr_overrides:
            override = hr_overrides[candidate_name]
            merged_record.update({
                "was_modified": True,
                "hr_override_score": override.get("hr_override_score"),
                "hr_status": override.get("hr_status", "Under Review"),
                "hr_recommendation": override.get("hr_recommendation"),
                "reviewer_name": override.get("reviewer_name"),
                "override_timestamp": override.get("timestamp"),
                "override_notes": override.get("notes"),
                "override_reason": override.get("override_reason"),
                "risk_flags": override.get("risk_flags", []),
                "priority": override.get("priority", "Medium")
            })
        
        # Calculate final display score
        final_score = calculate_final_display_score(
            merged_record["ai_score"],
            merged_record["hr_override_score"],
            merged_record["was_modified"]
        )
        merged_record["final_score"] = final_score
        
        # Calculate delta
        merged_record["score_delta"] = calculate_override_delta(
            merged_record["ai_score"],
            merged_record["hr_override_score"]
        )
        
        merged.append(merged_record)
    
    return merged


def apply_filters(
    candidates: List[Dict[str, Any]],
    override_filter: str = "All Candidates",
    decision_filter: Optional[List[str]] = None,
    score_range: Tuple[int, int] = (0, 100),
    priority_filter: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Apply filters to candidate list.
    
    Args:
        candidates: List of merged candidate records
        override_filter: "All Candidates", "HR Modified Only", or "AI Only"
        decision_filter: List of statuses to include
        score_range: (min_score, max_score) tuple
        priority_filter: List of priority levels
    
    Returns:
        Filtered candidate list
    """
    filtered = candidates
    
    # Override filter
    if override_filter == "HR Modified Only":
        filtered = [c for c in filtered if c.get("was_modified", False)]
    elif override_filter == "AI Only":
        filtered = [c for c in filtered if not c.get("was_modified", False)]
    
    # Decision filter
    if decision_filter:
        filtered = [c for c in filtered if c.get("hr_status") in decision_filter]
    
    # Score range filter
    filtered = [
        c for c in filtered
        if score_range[0] <= c.get("final_score", 0) <= score_range[1]
    ]
    
    # Priority filter
    if priority_filter:
        filtered = [c for c in filtered if c.get("priority") in priority_filter]
    
    return filtered


def sort_candidates(
    candidates: List[Dict[str, Any]],
    sort_by: str = "Final Score"
) -> List[Dict[str, Any]]:
    """
    Sort candidates by specified column.
    
    Args:
        candidates: List of merged candidate records
        sort_by: Column to sort by (Final Score, AI Score, HR Score, etc.)
    
    Returns:
        Sorted candidate list
    """
    sort_map = {
        "Final Score": ("final_score", True),
        "AI Score": ("ai_score", True),
        "HR Score": ("hr_override_score", True),
        "Override Delta": ("score_delta", False),
        "Priority": ("priority", True),
        "Final Decision": ("hr_status", False)
    }
    
    if sort_by not in sort_map:
        sort_by = "Final Score"
    
    column, descending = sort_map[sort_by]
    
    return sorted(
        candidates,
        key=lambda x: x.get(column, 0) if column != "priority" else priority_order(x.get(column, "Medium")),
        reverse=descending
    )


def priority_order(priority: str) -> int:
    """Convert priority to sortable integer."""
    order = {"High": 0, "Medium": 1, "Low": 2}
    return order.get(priority, 1)


# ==============================================================================
# SUMMARY METRICS
# ==============================================================================

def calculate_dashboard_metrics(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate key metrics for dashboard summary cards.
    
    Args:
        candidates: List of merged candidate records
    
    Returns:
        Dictionary of metric values
    """
    total = len(candidates)
    modified = sum(1 for c in candidates if c.get("was_modified", False))
    approved = sum(1 for c in candidates if c.get("hr_status") == "Final Approved")
    rejected = sum(1 for c in candidates if c.get("hr_status") == "Rejected")
    
    ai_scores = [c.get("ai_score", 0) for c in candidates]
    final_scores = [c.get("final_score", 0) for c in candidates]
    
    avg_ai = sum(ai_scores) / len(ai_scores) if ai_scores else 0
    avg_final = sum(final_scores) / len(final_scores) if final_scores else 0
    
    override_pct = (modified / total * 100) if total > 0 else 0
    
    return {
        "total_candidates": total,
        "hr_modified_count": modified,
        "final_approved_count": approved,
        "final_rejected_count": rejected,
        "average_ai_score": round(avg_ai, 1),
        "average_final_score": round(avg_final, 1),
        "override_percentage": round(override_pct, 1)
    }


# ==============================================================================
# VISUALIZATION HELPERS
# ==============================================================================

def create_ai_vs_final_score_chart(candidates: List[Dict[str, Any]]) -> go.Figure:
    """
    Create scatter plot comparing AI scores vs final scores.
    
    Args:
        candidates: List of merged candidate records
    
    Returns:
        Plotly figure
    """
    modified = [c for c in candidates if c.get("was_modified", False)]
    unmodified = [c for c in candidates if not c.get("was_modified", False)]
    
    fig = go.Figure()
    
    # Modified candidates (HR changed)
    if modified:
        fig.add_trace(go.Scatter(
            x=[c.get("ai_score", 0) for c in modified],
            y=[c.get("final_score", 0) for c in modified],
            mode="markers",
            name="HR Modified",
            marker=dict(
                size=10,
                color="#3B82F6",
                opacity=0.7,
                line=dict(color="white", width=2)
            ),
            text=[c.get("candidate_name", "") for c in modified],
            hovertemplate="<b>%{text}</b><br>AI: %{x:.1f}<br>Final: %{y:.1f}<extra></extra>"
        ))
    
    # Unmodified candidates (AI only)
    if unmodified:
        fig.add_trace(go.Scatter(
            x=[c.get("ai_score", 0) for c in unmodified],
            y=[c.get("final_score", 0) for c in unmodified],
            mode="markers",
            name="AI Only",
            marker=dict(
                size=8,
                color="#9CA3AF",
                opacity=0.5
            ),
            text=[c.get("candidate_name", "") for c in unmodified],
            hovertemplate="<b>%{text}</b><br>Score: %{x:.1f}<extra></extra>"
        ))
    
    # Diagonal line (where AI = Final)
    max_score = 100
    fig.add_trace(go.Scatter(
        x=[0, max_score],
        y=[0, max_score],
        mode="lines",
        name="No Change Line",
        line=dict(dash="dash", color="rgba(200,200,200,0.5)"),
        showlegend=True,
        hoverinfo="skip"
    ))
    
    fig.update_layout(
        title="AI Score vs Final Score (Post-HR Review)",
        xaxis_title="AI Score",
        yaxis_title="Final Score (After HR Override)",
        height=400,
        hovermode="closest",
        template="plotly_white",
        xaxis=dict(range=[0, 100]),
        yaxis=dict(range=[0, 100])
    )
    
    return fig


def create_override_distribution_chart(candidates: List[Dict[str, Any]]) -> go.Figure:
    """
    Create pie chart showing override distribution.
    
    Args:
        candidates: List of merged candidate records
    
    Returns:
        Plotly figure
    """
    modified_count = sum(1 for c in candidates if c.get("was_modified", False))
    unmodified_count = len(candidates) - modified_count
    
    fig = go.Figure(data=[go.Pie(
        labels=["HR Modified", "AI Only"],
        values=[modified_count, unmodified_count],
        marker=dict(colors=["#3B82F6", "#9CA3AF"]),
        textposition="inside",
        textinfo="label+percent"
    )])
    
    fig.update_layout(
        title="HR Override Distribution",
        height=350,
        showlegend=True
    )
    
    return fig


def create_delta_histogram(candidates: List[Dict[str, Any]]) -> go.Figure:
    """
    Create histogram showing score change distribution.
    
    Args:
        candidates: List of merged candidate records
    
    Returns:
        Plotly figure
    """
    modified = [c for c in candidates if c.get("was_modified", False)]
    deltas = [c.get("score_delta", 0) for c in modified]
    
    if not deltas:
        # Empty chart
        fig = go.Figure()
        fig.add_annotation(text="No HR modifications yet")
        return fig
    
    fig = go.Figure(data=[
        go.Histogram(
            x=deltas,
            nbinsx=15,
            marker_color="#F59E0B",
            name="Score Delta"
        )
    ])
    
    fig.update_layout(
        title="Score Change Distribution (HR Overrides)",
        xaxis_title="Score Delta (HR - AI)",
        yaxis_title="Frequency",
        height=350,
        template="plotly_white"
    )
    
    return fig


def create_decision_distribution_chart(candidates: List[Dict[str, Any]]) -> go.Figure:
    """
    Create bar chart showing HR decision distribution.
    
    Args:
        candidates: List of merged candidate records
    
    Returns:
        Plotly figure
    """
    decisions = {}
    for c in candidates:
        status = c.get("hr_status", "Not Reviewed")
        decisions[status] = decisions.get(status, 0) + 1
    
    status_colors = {
        "Final Approved": "#10B981",
        "Rejected": "#EF4444",
        "Interview Scheduled": "#F59E0B",
        "Under Review": "#3B82F6",
        "Not Reviewed": "#9CA3AF",
        "On Hold": "#8B5CF6"
    }
    
    colors = [status_colors.get(status, "#6B7280") for status in decisions.keys()]
    
    fig = go.Figure(data=[
        go.Bar(
            x=list(decisions.keys()),
            y=list(decisions.values()),
            marker_color=colors,
            text=list(decisions.values()),
            textposition="auto"
        )
    ])
    
    fig.update_layout(
        title="HR Decision Distribution",
        xaxis_title="Status",
        yaxis_title="Count",
        height=350,
        template="plotly_white",
        showlegend=False
    )
    
    return fig


# ==============================================================================
# EXPORT FUNCTIONS
# ==============================================================================

def export_transparency_report(candidates: List[Dict[str, Any]]) -> bytes:
    """
    Export comprehensive transparency report as CSV.
    
    Args:
        candidates: List of merged candidate records
    
    Returns:
        CSV data as bytes
    """
    export_data = []
    
    for c in candidates:
        export_data.append({
            "Rank": c.get("rank", ""),
            "Candidate Name": c.get("candidate_name", ""),
            "AI Score": f"{c.get('ai_score', 0):.1f}",
            "HR Score": f"{c.get('hr_override_score', 'N/A')}",
            "Final Score": f"{c.get('final_score', 0):.1f}",
            "Delta": f"{c.get('score_delta', 0):+.1f}",
            "Modified": "Yes" if c.get("was_modified", False) else "No",
            "HR Status": c.get("hr_status", ""),
            "Reviewer": c.get("reviewer_name", ""),
            "Notes": c.get("override_notes", ""),
            "Timestamp": c.get("override_timestamp", "")
        })
    
    df = pd.DataFrame(export_data)
    return df.to_csv(index=False).encode()


# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

def get_transparency_explanation(candidate: Dict[str, Any]) -> str:
    """
    Generate human-readable explanation for score changes.
    
    Args:
        candidate: Merged candidate record
    
    Returns:
        Explanation string
    """
    if not candidate.get("was_modified", False):
        return "This candidate was evaluated by AI only. No human review has been conducted yet."
    
    ai_score = candidate.get("ai_score", 0)
    hr_score = candidate.get("hr_override_score", 0)
    delta = candidate.get("score_delta", 0)
    
    explanation = f"""
    **Original AI Assessment**: {ai_score}/100
    
    **HR Final Decision**: {hr_score}/100
    
    **Change**: {'+' if delta > 0 else ''}{delta}
    
    **Reviewer**: {candidate.get('reviewer_name', 'Unknown')}
    
    **Review Date**: {candidate.get('override_timestamp', 'N/A')}
    
    **HR Notes**: {candidate.get('override_notes', 'No notes provided')}
    
    **Decision**: {candidate.get('hr_status', 'Under Review')}
    """
    
    return explanation.strip()


def format_timestamp(timestamp_str: Optional[str]) -> str:
    """Format timestamp for display."""
    if not timestamp_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(timestamp_str)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return timestamp_str
