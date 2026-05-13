"""
Enhanced Dashboard with AI vs HR Override Transparency

This module provides an enterprise-grade dashboard that:
- Shows AI scores and HR override scores separately
- Displays final scores with clear precedence logic
- Highlights HR-modified candidates
- Provides transparent scoring explanations
- Supports enterprise ATS-style workflows
- Includes comprehensive filtering and sorting

Features:
- Real-time AI vs HR comparison
- Interactive candidate cards with override details
- Advanced filtering (override status, decision, score range, priority)
- Professional visualizations
- Audit trail integration
- Export functionality
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Import transparency system
try:
    import transparency
except ImportError:
    st.error("Transparency module not found")
    transparency = None


# ==============================================================================
# COLOR SCHEMES AND STYLING
# ==============================================================================

COLORS = {
    "hr_modified": "#3B82F6",      # Blue
    "ai_only": "#9CA3AF",           # Gray
    "approved": "#10B981",          # Green
    "rejected": "#EF4444",          # Red
    "under_review": "#F59E0B",      # Orange
    "interview": "#8B5CF6",         # Purple
    "high_priority": "#EF4444",     # Red
    "medium_priority": "#F59E0B",   # Orange
    "low_priority": "#10B981"       # Green
}


# ==============================================================================
# DASHBOARD HEADER AND METRICS
# ==============================================================================

def render_dashboard_header(metrics: Dict[str, Any]) -> None:
    """
    Render dashboard header with summary metrics.
    
    Args:
        metrics: Dictionary of metric values from transparency system
    """
    st.markdown("# 📊 AI Resume Shortlisting Dashboard")
    st.markdown("### AI vs HR Override Transparency System")
    st.divider()
    
    # Summary metrics - Top row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "👥 Total Candidates",
            metrics.get("total_candidates", 0),
            help="Total number of candidates analyzed"
        )
    
    with col2:
        st.metric(
            "👤 HR Modified",
            f"{metrics.get('hr_modified_count', 0)} ({metrics.get('override_percentage', 0):.1f}%)",
            help="Candidates reviewed and scored by Human Resources"
        )
    
    with col3:
        st.metric(
            "✅ Final Approved",
            metrics.get("final_approved_count", 0),
            help="Candidates approved for next stage"
        )
    
    with col4:
        st.metric(
            "❌ Rejected",
            metrics.get("final_rejected_count", 0),
            help="Candidates rejected by HR decision"
        )
    
    st.markdown("")
    
    # Score metrics - Second row
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            "🤖 Average AI Score",
            f"{metrics.get('average_ai_score', 0):.1f}/100",
            help="Average score before human review"
        )
    
    with col2:
        st.metric(
            "👤 Average Final Score",
            f"{metrics.get('average_final_score', 0):.1f}/100",
            help="Average score after HR review and overrides"
        )
    
    with col3:
        score_change = metrics.get('average_final_score', 0) - metrics.get('average_ai_score', 0)
        st.metric(
            "📈 Score Adjustment",
            f"{score_change:+.1f}",
            help="Average change from AI to Final score",
            delta=score_change if score_change != 0 else None
        )
    
    st.divider()


# ==============================================================================
# FILTER PANEL
# ==============================================================================

def render_filter_panel() -> Dict[str, Any]:
    """
    Render sidebar filters for candidate search and filtering.
    
    Returns:
        Dictionary of selected filter values
    """
    st.sidebar.markdown("## 🔍 Filters")
    
    filters = {}
    
    # Override status filter
    st.sidebar.markdown("### Override Status")
    filters["override_filter"] = st.sidebar.radio(
        "Show:",
        ["All Candidates", "HR Modified Only", "AI Only"],
        help="Filter by override status"
    )
    
    # Decision status filter
    st.sidebar.markdown("### HR Decision")
    decision_options = [
        "Final Approved",
        "Rejected",
        "Interview Scheduled",
        "Under Review",
        "Not Reviewed",
        "On Hold"
    ]
    filters["decision_filter"] = st.sidebar.multiselect(
        "Status:",
        decision_options,
        default=decision_options,
        help="Filter by HR decision status"
    )
    
    # Score range filter
    st.sidebar.markdown("### Score Range")
    filters["score_range"] = st.sidebar.slider(
        "Final Score:",
        0, 100, (0, 100),
        step=5,
        help="Filter by final score (after HR review)"
    )
    
    # Priority filter
    st.sidebar.markdown("### Priority Level")
    priority_options = ["High", "Medium", "Low"]
    filters["priority_filter"] = st.sidebar.multiselect(
        "Priority:",
        priority_options,
        default=priority_options,
        help="Filter by HR-assigned priority"
    )
    
    return filters


# ==============================================================================
# PROFESSIONAL RANKING TABLE
# ==============================================================================

def render_ranking_table(candidates: List[Dict[str, Any]]) -> None:
    """
    Render professional ATS-style ranking table.
    
    Args:
        candidates: List of merged candidate records
    """
    st.markdown("## 📋 Candidate Rankings")
    
    # Sorting options
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        sort_by = st.selectbox(
            "Sort by:",
            ["Final Score", "AI Score", "HR Score", "Override Delta", "Priority", "Final Decision"],
            key="sort_selector"
        )
    
    with col2:
        show_count = st.number_input(
            "Show:",
            min_value=5,
            max_value=len(candidates),
            value=min(10, len(candidates)),
            step=5,
            help="Number of candidates to display"
        )
    
    with col3:
        show_modified_only = st.checkbox(
            "HR Modified Only",
            help="Show only candidates reviewed by HR"
        )
    
    # Sort candidates
    sorted_candidates = transparency.sort_candidates(candidates, sort_by)
    
    # Filter if needed
    if show_modified_only:
        sorted_candidates = [c for c in sorted_candidates if c.get("was_modified", False)]
    
    # Limit display
    sorted_candidates = sorted_candidates[:show_count]
    
    # Create table data
    table_data = []
    
    for idx, candidate in enumerate(sorted_candidates, 1):
        ai_score = candidate.get("ai_score", 0)
        hr_score = candidate.get("hr_override_score")
        final_score = candidate.get("final_score", 0)
        delta = candidate.get("score_delta", 0)
        was_modified = candidate.get("was_modified", False)
        hr_status = candidate.get("hr_status", "Not Reviewed")
        priority = candidate.get("priority", "Medium")
        risk_flags = candidate.get("risk_flags", [])
        
        # Get status badge
        status_text, status_color, status_emoji = transparency.get_override_status_badge(was_modified, hr_status)
        
        # Get priority badge
        priority_text, priority_color = transparency.get_priority_badge(priority)
        
        table_data.append({
            "Rank": f"#{idx}",
            "Candidate": candidate.get("candidate_name", "Unknown"),
            "AI Score": f"{ai_score:.1f}",
            "HR Score": f"{hr_score:.1f}" if was_modified else "—",
            "Final Score": f"**{final_score:.1f}**",
            "Delta": f"{delta:+.1f}" if was_modified else "—",
            "Status": f"{status_emoji} {status_text}",
            "Priority": priority_text,
            "Modified": "✓" if was_modified else "—",
            "Risks": ", ".join(risk_flags[:2]) if risk_flags else "—"
        })
    
    df = pd.DataFrame(table_data)
    
    # Display as dataframe
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.TextColumn("Rank", width="small"),
            "Candidate": st.column_config.TextColumn("Candidate", width="medium"),
            "AI Score": st.column_config.TextColumn("AI Score", width="small"),
            "HR Score": st.column_config.TextColumn("HR Score", width="small"),
            "Final Score": st.column_config.TextColumn("Final Score", width="small"),
            "Delta": st.column_config.TextColumn("Delta", width="small"),
            "Status": st.column_config.TextColumn("Status", width="medium"),
            "Priority": st.column_config.TextColumn("Priority", width="small"),
            "Modified": st.column_config.TextColumn("Modified", width="small"),
            "Risks": st.column_config.TextColumn("Risks", width="medium")
        }
    )


# ==============================================================================
# CANDIDATE CARD DISPLAY
# ==============================================================================

def render_candidate_cards(candidates: List[Dict[str, Any]], columns: int = 2) -> None:
    """
    Render professional candidate cards with override details.
    
    Args:
        candidates: List of merged candidate records
        columns: Number of columns for card layout
    """
    st.markdown("## 🎯 Candidate Details")
    
    # Create columns
    cols = st.columns(columns)
    col_idx = 0
    
    for candidate in candidates:
        col = cols[col_idx % columns]
        col_idx += 1
        
        with col:
            render_single_candidate_card(candidate)


def render_single_candidate_card(candidate: Dict[str, Any]) -> None:
    """
    Render a single professional candidate card.
    
    Args:
        candidate: Merged candidate record
    """
    candidate_name = candidate.get("candidate_name", "Unknown")
    final_score = candidate.get("final_score", 0)
    ai_score = candidate.get("ai_score", 0)
    hr_score = candidate.get("hr_override_score")
    delta = candidate.get("score_delta", 0)
    was_modified = candidate.get("was_modified", False)
    hr_status = candidate.get("hr_status", "Not Reviewed")
    priority = candidate.get("priority", "Medium")
    risk_flags = candidate.get("risk_flags", [])
    
    # Get status badge
    status_text, status_color, status_emoji = transparency.get_override_status_badge(was_modified, hr_status)
    priority_text, priority_color = transparency.get_priority_badge(priority)
    
    # Card styling
    border_color = COLORS["hr_modified"] if was_modified else COLORS["ai_only"]
    
    with st.container():
        # Top section: Name and Status
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"### {candidate_name}")
        with col2:
            st.markdown(f"<span style='color:{status_color};'>{status_emoji} {status_text}</span>", unsafe_allow_html=True)
        
        st.divider()
        
        # Score section
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "🤖 AI Score",
                f"{ai_score:.1f}",
                help="Original AI assessment"
            )
        
        with col2:
            if was_modified and hr_score:
                st.metric(
                    "👤 HR Score",
                    f"{hr_score:.1f}",
                    delta=f"{delta:+.1f}",
                    delta_color="off"
                )
            else:
                st.metric("👤 HR Score", "—")
        
        with col3:
            st.metric(
                "✅ Final Score",
                f"{final_score:.1f}",
                help="Score used for ranking"
            )
        
        st.divider()
        
        # Details section
        col1, col2 = st.columns(2)
        
        with col1:
            st.write(f"**Priority:** {priority_text}")
        
        with col2:
            reviewer = candidate.get("reviewer_name", "—")
            st.write(f"**Reviewer:** {reviewer}")
        
        # Risk flags
        if risk_flags:
            risk_html = " ".join([f"<span style='background:#FEE2E2;color:#991B1B;padding:2px 6px;border-radius:3px;font-size:12px;margin-right:4px;'>{flag}</span>" for flag in risk_flags[:3]])
            st.markdown(f"**Risks:** {risk_html}", unsafe_allow_html=True)
        
        # HR Notes
        if was_modified:
            notes = candidate.get("override_notes", "")
            if notes:
                with st.expander("📝 HR Notes"):
                    st.write(notes)
        
        st.divider()


# ==============================================================================
# TRANSPARENCY EXPLANATIONS
# ==============================================================================

def render_transparency_section(candidates: List[Dict[str, Any]]) -> None:
    """
    Render transparency explanations for score changes.
    
    Args:
        candidates: List of merged candidate records
    """
    st.markdown("## 🔍 Scoring Transparency")
    
    # Count modified candidates
    modified = [c for c in candidates if c.get("was_modified", False)]
    
    if not modified:
        st.info("No candidates have been reviewed by HR yet. All scores are AI-generated.")
        return
    
    st.markdown(f"**{len(modified)} candidate(s)** have been reviewed and scored by HR.\n")
    
    # Create tabs for each modified candidate
    candidate_names = [c.get("candidate_name", "Unknown") for c in modified]
    tabs = st.tabs(candidate_names)
    
    for tab, candidate in zip(tabs, modified):
        with tab:
            render_candidate_explanation(candidate)


def render_candidate_explanation(candidate: Dict[str, Any]) -> None:
    """
    Render detailed explanation for a single candidate's score.
    
    Args:
        candidate: Merged candidate record
    """
    ai_score = candidate.get("ai_score", 0)
    hr_score = candidate.get("hr_override_score", 0)
    delta = candidate.get("score_delta", 0)
    reviewer = candidate.get("reviewer_name", "Unknown")
    timestamp = transparency.format_timestamp(candidate.get("override_timestamp"))
    notes = candidate.get("override_notes", "No notes provided")
    reason = candidate.get("override_reason", "General HR review")
    
    # Main explanation
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("🤖 AI Score", f"{ai_score:.1f}/100")
    
    with col2:
        st.markdown(f"<div style='text-align:center; padding:20px;'><span style='font-size:24px;'>{delta:+.1f}</span><br/><span style='color:#666;'>Change</span></div>", unsafe_allow_html=True)
    
    with col3:
        st.metric("👤 HR Score", f"{hr_score:.1f}/100")
    
    st.divider()
    
    # Review details
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Reviewer:** {reviewer}")
        st.write(f"**Date:** {timestamp}")
    
    with col2:
        st.write(f"**Reason:** {reason}")
        st.write(f"**Status:** {candidate.get('hr_status', 'Under Review')}")
    
    # Notes
    st.markdown("**HR Notes:**")
    st.info(notes)
    
    # AI vs HR comparison
    st.markdown("**AI Analysis Summary:**")
    breakdown = candidate.get("breakdown", {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        skills_score = breakdown.get("skills", {}).get("score", 0)
        st.metric("Skills", f"{skills_score}/10")
    
    with col2:
        exp_score = breakdown.get("experience", {}).get("score", 0)
        st.metric("Experience", f"{exp_score}/10")
    
    with col3:
        edu_score = breakdown.get("education", {}).get("score", 0)
        st.metric("Education", f"{edu_score}/10")


# ==============================================================================
# VISUALIZATION SECTION
# ==============================================================================

def render_visualizations(candidates: List[Dict[str, Any]]) -> None:
    """
    Render chart visualizations.
    
    Args:
        candidates: List of merged candidate records
    """
    st.markdown("## 📈 Analytics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### AI vs Final Score")
        fig = transparency.create_ai_vs_final_score_chart(candidates)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Override Distribution")
        fig = transparency.create_override_distribution_chart(candidates)
        st.plotly_chart(fig, use_container_width=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### HR Decision Distribution")
        fig = transparency.create_decision_distribution_chart(candidates)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.markdown("### Score Change Distribution")
        fig = transparency.create_delta_histogram(candidates)
        st.plotly_chart(fig, use_container_width=True)


# ==============================================================================
# AUDIT TRAIL SECTION
# ==============================================================================

def render_audit_trail(candidates: List[Dict[str, Any]]) -> None:
    """
    Render audit trail of all modifications.
    
    Args:
        candidates: List of merged candidate records
    """
    st.markdown("## 🔐 Audit Trail")
    
    # Get audit log
    audit_log = transparency.load_audit_log()
    
    if not audit_log:
        st.info("No audit log entries yet.")
        return
    
    # Create audit table
    audit_data = []
    for entry in audit_log[-20:]:  # Show last 20 entries
        audit_data.append({
            "Timestamp": transparency.format_timestamp(entry.get("timestamp")),
            "Candidate": entry.get("candidate_name", "Unknown"),
            "Action": entry.get("action", "Unknown"),
            "Reviewer": entry.get("reviewer_name", "Unknown"),
            "Details": entry.get("details", "")
        })
    
    if audit_data:
        df = pd.DataFrame(audit_data)
        st.dataframe(df, use_container_width=True, hide_index=True)


# ==============================================================================
# EXPORT SECTION
# ==============================================================================

def render_export_section(candidates: List[Dict[str, Any]]) -> None:
    """
    Render export options.
    
    Args:
        candidates: List of merged candidate records
    """
    st.markdown("## 📥 Export")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv_data = transparency.export_transparency_report(candidates)
        st.download_button(
            label="📊 Download Transparency Report",
            data=csv_data,
            file_name="transparency_report.csv",
            mime="text/csv"
        )
    
    with col2:
        # JSON export
        import json
        json_data = json.dumps(candidates, indent=2, default=str).encode()
        st.download_button(
            label="📄 Download Full JSON",
            data=json_data,
            file_name="candidates_full_data.json",
            mime="application/json"
        )
    
    with col3:
        # Summary stats
        stats = transparency.calculate_dashboard_metrics(candidates)
        stats_json = json.dumps(stats, indent=2).encode()
        st.download_button(
            label="📈 Download Summary Stats",
            data=stats_json,
            file_name="summary_statistics.json",
            mime="application/json"
        )


# ==============================================================================
# MAIN DASHBOARD RENDERING FUNCTION
# ==============================================================================

def render_dashboard(batch_data: Optional[Any] = None) -> None:
    """
    Main function to render the complete dashboard with transparency system.
    
    Args:
        batch_data: Candidate results from session state (optional)
    """
    # Handle case where batch_data is a string
    if isinstance(batch_data, str):
        try:
            import json
            batch_data = json.loads(batch_data)
        except:
            st.error("Could not parse candidate data")
            return
    
    # Load AI candidates
    ai_candidates = batch_data if batch_data else transparency.load_candidate_results()
    
    if not ai_candidates:
        st.info("📁 No candidate data available. Please run the backend pipeline first.")
        return
    
    # Load HR overrides
    hr_overrides = transparency.load_hr_overrides()
    
    # Merge datasets
    merged_candidates = transparency.merge_ai_and_hr_data(ai_candidates, hr_overrides)
    
    # Calculate metrics
    metrics = transparency.calculate_dashboard_metrics(merged_candidates)
    
    # Render header
    render_dashboard_header(metrics)
    
    # Render filter panel
    filters = render_filter_panel()
    
    # Apply filters
    filtered_candidates = transparency.apply_filters(
        merged_candidates,
        override_filter=filters["override_filter"],
        decision_filter=filters["decision_filter"],
        score_range=filters["score_range"],
        priority_filter=filters["priority_filter"]
    )
    
    if not filtered_candidates:
        st.warning("No candidates match the selected filters.")
        return
    
    # Render ranking table
    render_ranking_table(filtered_candidates)
    
    st.markdown("")
    
    # Render candidate cards (top 6)
    top_candidates = filtered_candidates[:6]
    if top_candidates:
        render_candidate_cards(top_candidates, columns=2)
    
    st.markdown("")
    
    # Render visualizations
    render_visualizations(filtered_candidates)
    
    st.markdown("")
    
    # Render transparency section
    render_transparency_section(filtered_candidates)
    
    st.markdown("")
    
    # Render audit trail
    render_audit_trail(filtered_candidates)
    
    st.markdown("")
    
    # Render export section
    render_export_section(filtered_candidates)
