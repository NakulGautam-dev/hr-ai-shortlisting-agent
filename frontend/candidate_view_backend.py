"""
Candidate Detailed View Module for AI HR Resume Shortlisting System.

This module provides a production-quality recruiter-facing interface for viewing
detailed candidate analysis, skills matching, and hiring recommendations.

Features:
- Detailed candidate analysis with score breakdown
- Skills matching visualization
- Recruiter insights generation
- Hiring recommendations
- Candidate comparison (side-by-side)
- JSON export functionality

Author: HR AI System
Date: 2026
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Any, Optional, Tuple
import json


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_status_label(score: float) -> str:
    """
    Get human-readable status label based on score.
    
    Args:
        score (float): Candidate's final score (0-100)
    
    Returns:
        str: Status label
    """
    if score >= 85:
        return "Excellent Match"
    elif score >= 70:
        return "Strong Match"
    elif score >= 50:
        return "Moderate Match"
    else:
        return "Weak Match"


def get_status_color(score: float) -> str:
    """
    Get color code based on score for consistent coloring.
    
    Args:
        score (float): Candidate's final score (0-100)
    
    Returns:
        str: Streamlit color code
    """
    if score >= 85:
        return "🟢"  # Green
    elif score >= 70:
        return "🔵"  # Blue
    elif score >= 50:
        return "🟠"  # Orange
    else:
        return "🔴"  # Red


def get_hex_color(score: float) -> str:
    """
    Get hex color code based on score.
    
    Args:
        score (float): Candidate's final score (0-100)
    
    Returns:
        str: Hex color code
    """
    if score >= 85:
        return "#10B981"  # Green
    elif score >= 70:
        return "#3B82F6"  # Blue
    elif score >= 50:
        return "#F59E0B"  # Orange
    else:
        return "#EF4444"  # Red


def get_recommendation(score: float) -> Tuple[str, str, str]:
    """
    Get hiring recommendation based on score.
    
    Args:
        score (float): Candidate's final score (0-100)
    
    Returns:
        Tuple[str, str, str]: (recommendation, color, explanation)
    """
    if score >= 85:
        return (
            "✅ Hire Immediately",
            "#10B981",
            "Excellent match across all criteria. Recommend immediate interview."
        )
    elif score >= 70:
        return (
            "👥 Strong Interview Candidate",
            "#3B82F6",
            "Strong fit with good alignment. Recommend for next interview round."
        )
    elif score >= 50:
        return (
            "📋 Consider for Screening",
            "#F59E0B",
            "Moderate fit. Recommend for initial screening to explore further."
        )
    else:
        return (
            "❌ Not Recommended",
            "#EF4444",
            "Low fit with current requirements. Consider for future opportunities."
        )


def extract_skills_data(candidate: Dict[str, Any]) -> Tuple[List[str], List[str], int, int]:
    """
    Extract skills matching data from candidate result.
    
    Args:
        candidate (Dict): Candidate result dictionary
    
    Returns:
        Tuple[List, List, int, int]: (matched_pairs, unmatched, total_matched, total_missing)
    """
    matched_pairs = []
    unmatched_skills = []
    
    breakdown = candidate.get("breakdown", {})
    skills_data = breakdown.get("skills", {})
    details = skills_data.get("details", {})
    
    # Extract matched skill pairs
    matched_pairs = details.get("matched_skill_pairs", [])
    unmatched_skills = details.get("unmatched_skills", [])
    
    total_matched = len(matched_pairs)
    total_missing = len(unmatched_skills)
    
    return matched_pairs, unmatched_skills, total_matched, total_missing


def generate_candidate_insights(candidate: Dict[str, Any]) -> List[str]:
    """
    Generate recruiter-focused insights based on candidate profile.
    
    Args:
        candidate (Dict): Candidate result dictionary
    
    Returns:
        List[str]: List of insight statements
    """
    insights = []
    breakdown = candidate.get("breakdown", {})
    final_score = candidate.get("final_score", 0)
    
    # Extract scores
    scores = {
        category: data.get("score", 0)
        for category, data in breakdown.items()
    }
    
    # Extract skills data
    matched_pairs, unmatched_skills, total_matched, total_missing = extract_skills_data(candidate)
    
    # Generate insights based on score breakdown
    if scores.get("skills", 0) >= 8:
        insights.append("✓ Excellent technical skills alignment")
    elif scores.get("skills", 0) >= 6:
        insights.append("✓ Good technical skills match")
    elif scores.get("skills", 0) < 5:
        insights.append("⚠ Limited technical skills alignment")
    
    if scores.get("projects", 0) >= 8:
        insights.append("✓ Strong portfolio of relevant projects")
    elif scores.get("projects", 0) >= 5:
        insights.append("✓ Some relevant project experience")
    else:
        insights.append("⚠ Limited portfolio demonstration")
    
    if scores.get("experience", 0) >= 7:
        insights.append("✓ Solid domain experience")
    elif scores.get("experience", 0) >= 5:
        insights.append("✓ Adjacent experience that transfers well")
    else:
        insights.append("⚠ Limited relevant experience")
    
    if scores.get("education", 0) >= 7:
        insights.append("✓ Strong educational background")
    else:
        insights.append("✓ Adequate educational qualifications")
    
    if scores.get("communication", 0) >= 7:
        insights.append("✓ Demonstrates strong communication")
    else:
        insights.append("⚠ Communication could be stronger")
    
    # Skill-specific insights
    if total_missing > 0:
        insights.append(f"• Missing {total_missing} key skill(s): {', '.join(unmatched_skills[:3])}")
    
    if total_matched > 5:
        insights.append(f"• Excellent match on {total_matched} technical skills")
    
    # Overall recommendation insight
    if final_score >= 80:
        insights.append("→ High priority candidate for further evaluation")
    elif final_score >= 60:
        insights.append("→ Strong candidate worth interviewing")
    else:
        insights.append("→ Consider for junior/entry-level positions or future opportunities")
    
    return insights


def create_score_gauge(score: float) -> go.Figure:
    """
    Create a gauge chart for final score visualization.
    
    Args:
        score (float): Final score (0-100)
    
    Returns:
        go.Figure: Plotly gauge chart
    """
    color = get_hex_color(score)
    
    fig = go.Figure(data=[
        go.Indicator(
            mode="gauge+number+delta",
            value=score,
            domain={"x": [0, 1], "y": [0, 1]},
            title={"text": "Final Score"},
            delta={"reference": 70, "increasing": {"color": "#10B981"}},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": color},
                "steps": [
                    {"range": [0, 50], "color": "#FEE2E2"},
                    {"range": [50, 70], "color": "#FEF3C7"},
                    {"range": [70, 85], "color": "#DBEAFE"},
                    {"range": [85, 100], "color": "#DCFCE7"}
                ],
                "threshold": {
                    "line": {"color": "red", "width": 2},
                    "thickness": 0.75,
                    "value": 50
                }
            }
        )
    ])
    
    fig.update_layout(
        height=300,
        margin={"l": 20, "r": 20, "t": 40, "b": 20},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#374151", "size": 12}
    )
    
    return fig


def create_category_breakdown_chart(breakdown: Dict[str, Dict[str, Any]]) -> go.Figure:
    """
    Create a horizontal bar chart showing category breakdowns.
    
    Args:
        breakdown (Dict): Category breakdown data
    
    Returns:
        go.Figure: Plotly bar chart
    """
    categories = []
    scores = []
    colors = []
    
    category_order = ["skills", "experience", "education", "projects", "communication"]
    
    for category in category_order:
        if category in breakdown:
            data = breakdown[category]
            score = data.get("score", 0)
            categories.append(category.capitalize())
            scores.append(score * 10)  # Convert to 0-100 scale
            
            if score >= 8:
                colors.append("#10B981")  # Green
            elif score >= 6:
                colors.append("#3B82F6")  # Blue
            elif score >= 4:
                colors.append("#F59E0B")  # Orange
            else:
                colors.append("#EF4444")  # Red
    
    fig = go.Figure(data=[
        go.Bar(
            y=categories,
            x=scores,
            orientation="h",
            marker={"color": colors},
            text=[f"{s:.0f}" for s in scores],
            textposition="auto",
            hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}/100<extra></extra>"
        )
    ])
    
    fig.update_layout(
        title="Category Breakdown",
        xaxis_title="Score",
        yaxis_title="",
        height=250,
        margin={"l": 150, "r": 20, "t": 40, "b": 20},
        xaxis={"range": [0, 100]},
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": "#374151", "size": 11},
        showlegend=False
    )
    
    return fig


# ==============================================================================
# RENDERING FUNCTIONS
# ==============================================================================

def render_candidate_header(candidate: Dict[str, Any]) -> None:
    """
    Render the candidate header section with name, score, rank, and status.
    
    Args:
        candidate (Dict): Candidate result dictionary
    """
    col1, col2, col3, col4 = st.columns([3, 1, 1, 1.5])
    
    with col1:
        name = candidate.get("candidate_name", "Unknown")
        st.markdown(f"## {name}")
    
    with col2:
        score = candidate.get("final_score", 0)
        st.metric("Score", f"{score:.1f}/100")
    
    with col3:
        rank = candidate.get("rank", "N/A")
        st.metric("Rank", f"#{rank}")
    
    with col4:
        score = candidate.get("final_score", 0)
        status = get_status_label(score)
        color_emoji = get_status_color(score)
        st.markdown(f"### {color_emoji} {status}")
    
    st.divider()


def render_score_cards(breakdown: Dict[str, Dict[str, Any]]) -> None:
    """
    Render category score cards with justifications and progress bars.
    
    Args:
        breakdown (Dict): Category breakdown data
    """
    st.subheader("📊 Category Breakdown")
    
    # Define category display order and icons
    categories_display = [
        ("skills", "🔧 Technical Skills"),
        ("experience", "💼 Experience"),
        ("education", "🎓 Education"),
        ("projects", "📁 Projects"),
        ("communication", "💬 Communication")
    ]
    
    # Create 2x3 grid
    cols = st.columns(2)
    col_idx = 0
    
    for category_key, category_label in categories_display:
        if category_key not in breakdown:
            continue
        
        col = cols[col_idx % 2]
        col_idx += 1
        
        with col:
            data = breakdown[category_key]
            score = data.get("score", 0)
            justification = data.get("justification", "")
            
            # Determine color
            if score >= 8:
                color = "#10B981"
            elif score >= 6:
                color = "#3B82F6"
            elif score >= 4:
                color = "#F59E0B"
            else:
                color = "#EF4444"
            
            # Create card with HTML/Markdown
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {color}15 0%, {color}05 100%);
                border-left: 4px solid {color};
                padding: 16px;
                border-radius: 8px;
                margin-bottom: 12px;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 600; color: #1F2937;">{category_label}</span>
                    <span style="font-size: 18px; font-weight: 700; color: {color};">{score}/10</span>
                </div>
                <div style="background: #E5E7EB; height: 6px; border-radius: 3px; overflow: hidden; margin-bottom: 8px;">
                    <div style="background: {color}; height: 100%; width: {score*10}%;"></div>
                </div>
                <div style="font-size: 13px; color: #6B7280; line-height: 1.4;">
                    {justification}
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()


def render_skills_analysis(candidate: Dict[str, Any]) -> None:
    """
    Render detailed skills matching analysis.
    
    Args:
        candidate (Dict): Candidate result dictionary
    """
    st.subheader("🎯 Skills Match Analysis")
    
    matched_pairs, unmatched_skills, total_matched, total_missing = extract_skills_data(candidate)
    
    # Summary metrics
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.metric("Matched Skills", total_matched, delta="+")
    
    with summary_col2:
        st.metric("Missing Skills", total_missing, delta="-")
    
    with summary_col3:
        if total_matched + total_missing > 0:
            match_pct = (total_matched / (total_matched + total_missing)) * 100
            st.metric("Match Rate", f"{match_pct:.0f}%")
        else:
            st.metric("Match Rate", "N/A")
    
    # Matched skills
    if matched_pairs:
        st.markdown("#### ✅ Matched Skills")
        
        skills_cols = st.columns(2)
        for idx, pair in enumerate(matched_pairs):
            col = skills_cols[idx % 2]
            with col:
                st.markdown(f"""
                <div style="
                    background: #F0FDF4;
                    border-left: 3px solid #10B981;
                    padding: 12px;
                    border-radius: 6px;
                    margin-bottom: 8px;
                ">
                    <span style="font-size: 13px; color: #065F46;">✓ {pair}</span>
                </div>
                """, unsafe_allow_html=True)
    
    # Missing skills
    if unmatched_skills:
        st.markdown("#### ⚠️ Missing Skills")
        
        missing_cols = st.columns(2)
        for idx, skill in enumerate(unmatched_skills):
            col = missing_cols[idx % 2]
            with col:
                st.markdown(f"""
                <div style="
                    background: #FEF3C7;
                    border-left: 3px solid #F59E0B;
                    padding: 12px;
                    border-radius: 6px;
                    margin-bottom: 8px;
                ">
                    <span style="font-size: 13px; color: #92400E;">✗ {skill}</span>
                </div>
                """, unsafe_allow_html=True)
    
    st.divider()


def render_recruiter_insights(insights: List[str]) -> None:
    """
    Render recruiter insights section.
    
    Args:
        insights (List[str]): List of insight strings
    """
    st.subheader("💡 Recruiter Insights")
    
    for insight in insights:
        st.markdown(f"- {insight}")
    
    st.divider()


def render_hiring_recommendation(score: float) -> None:
    """
    Render hiring recommendation box.
    
    Args:
        score (float): Final score (0-100)
    """
    recommendation, color, explanation = get_recommendation(score)
    
    st.markdown(f"""
    <div style="
        background: {color}15;
        border-left: 4px solid {color};
        border-radius: 8px;
        padding: 20px;
        margin: 20px 0;
    ">
        <div style="font-size: 18px; font-weight: 700; color: {color}; margin-bottom: 8px;">
            {recommendation}
        </div>
        <div style="font-size: 14px; color: #374151; line-height: 1.6;">
            {explanation}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()


def render_comparison_section(candidates: List[Dict[str, Any]]) -> None:
    """
    Render candidate comparison section (bonus feature).
    
    Args:
        candidates (List[Dict]): List of all candidate results
    """
    if len(candidates) < 2:
        return
    
    st.subheader("🔄 Compare Candidates")
    
    enable_comparison = st.checkbox("Enable side-by-side comparison")
    
    if enable_comparison:
        # Create sorted list for selection
        sorted_candidates = sorted(
            candidates,
            key=lambda x: x.get("final_score", 0),
            reverse=True
        )
        
        candidate_labels = [
            f"{c.get('candidate_name', 'Unknown')} — {c.get('final_score', 0):.1f}/100"
            for c in sorted_candidates
        ]
        
        col1, col2 = st.columns(2)
        
        with col1:
            candidate1_idx = st.selectbox(
                "Select first candidate",
                range(len(sorted_candidates)),
                format_func=lambda i: candidate_labels[i],
                key="comparison_1"
            )
            candidate1 = sorted_candidates[candidate1_idx]
        
        with col2:
            candidate2_idx = st.selectbox(
                "Select second candidate",
                range(len(sorted_candidates)),
                format_func=lambda i: candidate_labels[i],
                key="comparison_2"
            )
            candidate2 = sorted_candidates[candidate2_idx]
        
        # Render comparison
        if candidate1_idx != candidate2_idx:
            st.markdown("---")
            
            comp_col1, comp_col2 = st.columns(2)
            
            with comp_col1:
                st.markdown(f"### {candidate1.get('candidate_name', 'Candidate 1')}")
                st.metric("Score", f"{candidate1.get('final_score', 0):.1f}/100")
                st.metric("Rank", f"#{candidate1.get('rank', 'N/A')}")
            
            with comp_col2:
                st.markdown(f"### {candidate2.get('candidate_name', 'Candidate 2')}")
                st.metric("Score", f"{candidate2.get('final_score', 0):.1f}/100")
                st.metric("Rank", f"#{candidate2.get('rank', 'N/A')}")
            
            # Category comparison
            st.markdown("#### Category Comparison")
            
            breakdown1 = candidate1.get("breakdown", {})
            breakdown2 = candidate2.get("breakdown", {})
            
            comparison_data = []
            for category in ["skills", "experience", "education", "projects", "communication"]:
                score1 = breakdown1.get(category, {}).get("score", 0)
                score2 = breakdown2.get(category, {}).get("score", 0)
                
                comparison_data.append({
                    "Category": category.capitalize(),
                    candidate1.get('candidate_name', 'Candidate 1'): score1,
                    candidate2.get('candidate_name', 'Candidate 2'): score2
                })
            
            df_comparison = pd.DataFrame(comparison_data)
            
            # Create comparison chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                y=df_comparison["Category"],
                x=df_comparison[candidate1.get('candidate_name', 'Candidate 1')],
                name=candidate1.get('candidate_name', 'Candidate 1'),
                orientation="h",
                marker_color="#3B82F6"
            ))
            
            fig.add_trace(go.Bar(
                y=df_comparison["Category"],
                x=df_comparison[candidate2.get('candidate_name', 'Candidate 2')],
                name=candidate2.get('candidate_name', 'Candidate 2'),
                orientation="h",
                marker_color="#10B981"
            ))
            
            fig.update_layout(
                barmode="group",
                height=300,
                margin={"l": 150, "r": 20, "t": 20, "b": 20},
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font={"color": "#374151"}
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    st.divider()


def render_export_section(candidate: Dict[str, Any]) -> None:
    """
    Render export/download section.
    
    Args:
        candidate (Dict): Candidate result dictionary
    """
    st.subheader("📥 Export Candidate Data")
    
    col1, col2 = st.columns(2)
    
    with col1:
        json_str = json.dumps(candidate, indent=2)
        st.download_button(
            label="📄 Download Full JSON",
            data=json_str,
            file_name=f"{candidate.get('candidate_name', 'candidate').replace(' ', '_')}_analysis.json",
            mime="application/json"
        )
    
    with col2:
        # Create CSV export of breakdown
        breakdown = candidate.get("breakdown", {})
        csv_data = []
        
        for category, data in breakdown.items():
            csv_data.append({
                "Category": category.capitalize(),
                "Score": f"{data.get('score', 0)}/10",
                "Justification": data.get("justification", "")
            })
        
        df_export = pd.DataFrame(csv_data)
        csv_str = df_export.to_csv(index=False)
        
        st.download_button(
            label="📊 Download Breakdown CSV",
            data=csv_str,
            file_name=f"{candidate.get('candidate_name', 'candidate').replace(' ', '_')}_breakdown.csv",
            mime="text/csv"
        )
    
    st.divider()


# ==============================================================================
# MAIN RENDERING FUNCTION
# ==============================================================================

def render_candidate_view(candidate_results: Optional[List[Dict[str, Any]]] = None) -> None:
    """
    Main function to render the complete candidate detail interface.
    
    Args:
        candidate_results (Optional[List[Dict]]): List of candidate results from backend
    """
    # Handle empty state
    if not candidate_results or len(candidate_results) == 0:
        st.info("📋 Analyze resumes to view detailed candidate insights.")
        return
    
    # Sort candidates by score (highest first)
    sorted_candidates = sorted(
        candidate_results,
        key=lambda x: x.get("final_score", 0),
        reverse=True
    )
    
    # Candidate selector
    st.subheader("👤 Select Candidate")
    
    candidate_labels = [
        f"{c.get('candidate_name', 'Unknown')} — {c.get('final_score', 0):.1f}/100 — Rank #{c.get('rank', 'N/A')}"
        for c in sorted_candidates
    ]
    
    selected_idx = st.selectbox(
        "Choose a candidate to view detailed analysis:",
        range(len(sorted_candidates)),
        format_func=lambda i: candidate_labels[i],
        key="candidate_selector"
    )
    
    selected_candidate = sorted_candidates[selected_idx]
    
    st.markdown("---")
    
    # Render candidate header
    render_candidate_header(selected_candidate)
    
    # Main content area
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        # Score visualization
        st.subheader("📈 Final Score")
        fig_gauge = create_score_gauge(selected_candidate.get("final_score", 0))
        st.plotly_chart(fig_gauge, use_container_width=True)
        
        # Category breakdown chart
        breakdown = selected_candidate.get("breakdown", {})
        fig_breakdown = create_category_breakdown_chart(breakdown)
        st.plotly_chart(fig_breakdown, use_container_width=True)
    
    with col_side:
        # Category scores as metrics
        st.markdown("#### Category Scores")
        
        category_order = ["skills", "experience", "education", "projects", "communication"]
        
        for category in category_order:
            if category in breakdown:
                score = breakdown[category].get("score", 0)
                st.metric(
                    category.capitalize(),
                    f"{score}/10"
                )
    
    st.markdown("---")
    
    # Category breakdown cards
    render_score_cards(breakdown)
    
    # Skills analysis
    render_skills_analysis(selected_candidate)
    
    # Recruiter insights
    insights = generate_candidate_insights(selected_candidate)
    render_recruiter_insights(insights)
    
    # Hiring recommendation
    render_hiring_recommendation(selected_candidate.get("final_score", 0))
    
    # Comparison section (bonus feature)
    render_comparison_section(sorted_candidates)
    
    # Export section
    render_export_section(selected_candidate)


# ==============================================================================
# DEBUG/TESTING FUNCTION
# ==============================================================================

def test_render() -> None:
    """
    Test function to render candidate view with mock data.
    Used for development and testing purposes.
    """
    mock_data = [
        {
            "candidate_name": "Nakul Gautam",
            "final_score": 87.5,
            "rank": 1,
            "breakdown": {
                "skills": {
                    "score": 9,
                    "justification": "Excellent technical skills match with Python, REST APIs, and cloud experience",
                    "details": {
                        "matched_skill_pairs": [
                            "Python ← Python (0.98)",
                            "REST API ← REST APIs (0.91)",
                            "Cloud ← AWS (0.88)"
                        ],
                        "unmatched_skills": ["Kubernetes"]
                    }
                },
                "experience": {
                    "score": 8,
                    "justification": "Strong backend development experience with relevant technologies"
                },
                "education": {
                    "score": 8,
                    "justification": "Strong educational background in Computer Science"
                },
                "projects": {
                    "score": 9,
                    "justification": "Highly relevant projects including ML and full-stack development"
                },
                "communication": {
                    "score": 8,
                    "justification": "Clear documentation and technical writing in portfolio"
                }
            }
        },
        {
            "candidate_name": "Ayush Sharma",
            "final_score": 72.0,
            "rank": 2,
            "breakdown": {
                "skills": {
                    "score": 7,
                    "justification": "Good technical skills match with some gaps",
                    "details": {
                        "matched_skill_pairs": [
                            "Python ← Python (0.95)",
                            "APIs ← REST APIs (0.85)"
                        ],
                        "unmatched_skills": ["Kubernetes", "Docker"]
                    }
                },
                "experience": {
                    "score": 6,
                    "justification": "Adjacent domain experience with some backend exposure"
                },
                "education": {
                    "score": 7,
                    "justification": "Good educational background"
                },
                "projects": {
                    "score": 7,
                    "justification": "Some relevant projects but limited complexity"
                },
                "communication": {
                    "score": 7,
                    "justification": "Adequate communication in portfolio"
                }
            }
        }
    ]
    
    render_candidate_view(mock_data)


if __name__ == "__main__":
    # For testing: use mock data
    test_render()
