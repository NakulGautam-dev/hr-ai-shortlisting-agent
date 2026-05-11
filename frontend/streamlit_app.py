"""
AI HR Resume Shortlisting System - Frontend Dashboard

A professional Streamlit application for visualizing and analyzing
AI-powered candidate screening results.

This frontend:
- Loads JSON results from the backend pipeline
- Displays candidate rankings and scores
- Provides detailed candidate analysis
- Generates visual analytics and insights
- Exports reports and data

Works WITHOUT Gemini API (uses pre-generated JSON files)
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
import warnings

warnings.filterwarnings("ignore")

# Import frontend modules
import upload_section
import backend_connector
import utils
import dashboard
import charts

# ==============================================================================
# PAGE CONFIGURATION
# ==============================================================================

st.set_page_config(
    page_title="AI HR Shortlisting Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# CUSTOM STYLING
# ==============================================================================

def apply_custom_styling():
    """Apply custom CSS styling for professional appearance."""
    custom_css = """
    <style>
    /* Main container styling */
    .main {
        padding: 2rem;
    }
    
    /* Headers */
    h1, h2, h3 {
        color: #1f77b4;
        font-weight: 600;
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    /* Status badges */
    .status-shortlisted {
        background-color: #10b981;
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-consider {
        background-color: #f59e0b;
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    .status-rejected {
        background-color: #ef4444;
        color: white;
        padding: 5px 12px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
    }
    
    /* Score highlights */
    .score-excellent {
        color: #10b981;
        font-weight: bold;
        font-size: 1.3rem;
    }
    
    .score-good {
        color: #3b82f6;
        font-weight: bold;
        font-size: 1.3rem;
    }
    
    .score-fair {
        color: #f59e0b;
        font-weight: bold;
        font-size: 1.3rem;
    }
    
    .score-poor {
        color: #ef4444;
        font-weight: bold;
        font-size: 1.3rem;
    }
    
    /* Skill tags */
    .skill-tag-matched {
        background-color: #d1fae5;
        color: #065f46;
        padding: 5px 12px;
        border-radius: 15px;
        margin: 5px;
        display: inline-block;
        font-size: 0.9rem;
    }
    
    .skill-tag-missing {
        background-color: #fee2e2;
        color: #7f1d1d;
        padding: 5px 12px;
        border-radius: 15px;
        margin: 5px;
        display: inline-block;
        font-size: 0.9rem;
    }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


apply_custom_styling()

# ==============================================================================
# CONSTANTS & PATHS
# ==============================================================================

# Get the parent directory (project root)
FRONTEND_DIR = Path(__file__).parent
PROJECT_ROOT = FRONTEND_DIR.parent
OUTPUTS_DIR = PROJECT_ROOT / "outputs"

# Create outputs directory if it doesn't exist
OUTPUTS_DIR.mkdir(exist_ok=True)

# ==============================================================================
# SESSION STATE INITIALIZATION
# ==============================================================================

def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "Dashboard"
    
    if "selected_batch" not in st.session_state:
        st.session_state.selected_batch = None
    
    if "batch_data" not in st.session_state:
        st.session_state.batch_data = None
    
    if "candidates_df" not in st.session_state:
        st.session_state.candidates_df = None
    
    if "selected_candidate" not in st.session_state:
        st.session_state.selected_candidate = None


initialize_session_state()

# ==============================================================================
# FILE LOADING FUNCTIONS
# ==============================================================================

def get_batch_files() -> List[str]:
    """
    Get list of available batch result JSON files.
    
    Returns:
        List of file names sorted by modification time (newest first)
    """
    if not OUTPUTS_DIR.exists():
        return []
    
    batch_files = sorted(
        OUTPUTS_DIR.glob("*results*.json"),
        key=lambda x: x.stat().st_mtime,
        reverse=True
    )
    
    return [f.name for f in batch_files]


def load_batch_results(filename: str) -> Optional[Dict[str, Any]]:
    """
    Load batch results from JSON file.
    
    Args:
        filename (str): Name of the JSON file to load
    
    Returns:
        Dict with batch results or None if load fails
    """
    try:
        file_path = OUTPUTS_DIR / filename
        if not file_path.exists():
            st.error(f"File not found: {filename}")
            return None
        
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return data
    
    except json.JSONDecodeError:
        st.error(f"Invalid JSON format in {filename}")
        return None
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None


def extract_candidate_dataframe(batch_data: Dict) -> Optional[pd.DataFrame]:
    """
    Extract candidate dataframe from batch results.
    
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
        
        # Ensure required columns exist
        required_cols = ["final_score", "candidate_name"]
        if not all(col in df.columns for col in required_cols):
            st.warning("Dataset missing required columns")
            return None
        
        # Add rank column if not present
        if "rank" not in df.columns:
            df = df.sort_values("final_score", ascending=False).reset_index(drop=True)
            df["rank"] = range(1, len(df) + 1)
        
        return df
    
    except Exception as e:
        st.error(f"Error processing candidate data: {str(e)}")
        return None


def get_candidate_status(score: float) -> Tuple[str, str]:
    """
    Determine candidate status based on score.
    
    Args:
        score (float): Candidate's final score (0-100)
    
    Returns:
        Tuple of (status_label, status_color)
    """
    if score >= 75:
        return "🟢 Shortlisted", "#10b981"
    elif score >= 50:
        return "🟡 Consider", "#f59e0b"
    else:
        return "🔴 Rejected", "#ef4444"


def get_score_color(score: float) -> str:
    """
    Get color code for score visualization.
    
    Args:
        score (float): Score value (0-100)
    
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


# ==============================================================================
# UI COMPONENT FUNCTIONS
# ==============================================================================

def render_metric_card(label: str, value: str, color: str = "#667eea", icon: str = "📊"):
    """
    Render a professional metric card.
    
    Args:
        label (str): Metric label
        value (str): Metric value
        color (str): Card background color (hex)
        icon (str): Emoji icon for the card
    """
    col1, col2 = st.columns([0.2, 0.8])
    with col1:
        st.markdown(f"<p style='font-size: 2rem'>{icon}</p>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<p style='color: gray; font-size: 0.9rem'>{label}</p>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 1.8rem; font-weight: bold; color: {color}'>{value}</p>", unsafe_allow_html=True)


def render_score_badge(score: float) -> str:
    """
    Create HTML for score badge.
    
    Args:
        score (float): Score value (0-100)
    
    Returns:
        HTML string for badge
    """
    color = get_score_color(score)
    return f'<span style="background-color: {color}; color: white; padding: 8px 16px; border-radius: 20px; font-weight: bold; font-size: 1.1rem">{score:.1f}/100</span>'


def render_status_badge(status: str) -> str:
    """
    Create HTML for status badge.
    
    Args:
        status (str): Status label with emoji
    
    Returns:
        HTML string for badge
    """
    color_map = {
        "🟢 Shortlisted": "#10b981",
        "🟡 Consider": "#f59e0b",
        "🔴 Rejected": "#ef4444"
    }
    color = color_map.get(status, "#6b7280")
    return f'<span style="background-color: {color}; color: white; padding: 6px 14px; border-radius: 20px; font-weight: 600; font-size: 0.9rem">{status}</span>'


def render_skill_tags(matched_skills: List[str], missing_skills: List[str]):
    """
    Render matched and missing skills as tags.
    
    Args:
        matched_skills (List[str]): List of matched skills
        missing_skills (List[str]): List of missing skills
    """
    if matched_skills:
        st.markdown("**✅ Matched Skills:**")
        skill_html = "".join([
            f'<span class="skill-tag-matched">{skill}</span>'
            for skill in matched_skills[:10]  # Show top 10
        ])
        st.markdown(skill_html, unsafe_allow_html=True)
    
    if missing_skills:
        st.markdown("**❌ Missing Skills:**")
        skill_html = "".join([
            f'<span class="skill-tag-missing">{skill}</span>'
            for skill in missing_skills[:10]  # Show top 10
        ])
        st.markdown(skill_html, unsafe_allow_html=True)


# ==============================================================================
# PAGE FUNCTIONS
# ==============================================================================

def page_dashboard():
    """Render the main dashboard page with key metrics and overview."""
    st.title("📊 Dashboard")
    st.markdown("---")
    
    if st.session_state.candidates_df is None or len(st.session_state.candidates_df) == 0:
        st.info("📁 Select a batch file from the sidebar to view dashboard")
        return
    
    df = st.session_state.candidates_df
    
    # Calculate metrics
    total_candidates = len(df)
    avg_score = df["final_score"].mean()
    highest_score = df["final_score"].max()
    shortlisted = len(df[df["final_score"] >= 75])
    rejected = len(df[df["final_score"] < 50])
    
    # Display metric cards in columns
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric("Total Candidates", total_candidates, delta=None)
    with col2:
        st.metric("Average Score", f"{avg_score:.1f}", delta=None)
    with col3:
        st.metric("Highest Score", f"{highest_score:.1f}", delta=None)
    with col4:
        st.metric("Shortlisted", shortlisted, delta=f"{(shortlisted/total_candidates*100):.0f}%")
    with col5:
        st.metric("Rejected", rejected, delta=f"{(rejected/total_candidates*100):.0f}%")
    
    st.markdown("---")
    
    # Top candidate section
    st.subheader("🏆 Top Candidate")
    top_candidate = df.iloc[0]
    
    col1, col2 = st.columns([0.7, 0.3])
    with col1:
        st.markdown(f"### {top_candidate['candidate_name']}")
        if "overall_recommendation" in top_candidate or "analysis" in top_candidate:
            analysis = top_candidate.get("overall_recommendation") or top_candidate.get("analysis", {}).get("overall_recommendation", "Excellent candidate")
            st.markdown(f"*{analysis}*")
    with col2:
        st.markdown(render_score_badge(top_candidate["final_score"]), unsafe_allow_html=True)
    
    # Top candidate score breakdown
    col1, col2, col3, col4, col5 = st.columns(5)
    
    component_scores = {
        "Skills": top_candidate.get("components", {}).get("skills", 0),
        "Experience": top_candidate.get("components", {}).get("experience", 0),
        "Education": top_candidate.get("components", {}).get("education", 0),
        "Projects": top_candidate.get("components", {}).get("projects", 0),
        "Communication": top_candidate.get("components", {}).get("communication", 0)
    }
    
    for (label, score), col in zip(component_scores.items(), [col1, col2, col3, col4, col5]):
        with col:
            color = get_score_color(score)
            st.markdown(f"<p style='text-align: center; color: {color}; font-weight: bold'>{label}</p>", unsafe_allow_html=True)
            st.markdown(f"<p style='text-align: center; font-size: 1.5rem; color: {color}; font-weight: bold'>{score:.0f}</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Score distribution
    st.subheader("📈 Score Distribution")
    fig = px.histogram(
        df,
        x="final_score",
        nbins=15,
        title="Distribution of Candidate Scores",
        labels={"final_score": "Final Score", "count": "Number of Candidates"},
        color_discrete_sequence=["#667eea"]
    )
    fig.update_layout(
        showlegend=False,
        hovermode="x unified",
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Status breakdown pie chart
    col1, col2 = st.columns(2)
    with col1:
        status_counts = pd.cut(df["final_score"], bins=[0, 50, 75, 100], labels=["Rejected", "Consider", "Shortlisted"]).value_counts()
        fig_pie = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Candidate Status Breakdown",
            color_discrete_map={"Rejected": "#ef4444", "Consider": "#f59e0b", "Shortlisted": "#10b981"}
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Component averages
        if all(key in df.columns or f"components.{key.lower()}" in str(df.columns) for key in ["skills", "experience", "education"]):
            components_df = pd.DataFrame({
                "Component": ["Skills", "Experience", "Education", "Projects", "Communication"],
                "Average Score": [
                    df["components"].apply(lambda x: x.get("skills", 0) if isinstance(x, dict) else 0).mean() if "components" in df.columns else df.get("components", [{}])[0].get("skills", 5),
                    df["components"].apply(lambda x: x.get("experience", 0) if isinstance(x, dict) else 0).mean() if "components" in df.columns else 5,
                    df["components"].apply(lambda x: x.get("education", 0) if isinstance(x, dict) else 0).mean() if "components" in df.columns else 5,
                    df["components"].apply(lambda x: x.get("projects", 0) if isinstance(x, dict) else 0).mean() if "components" in df.columns else 5,
                    df["components"].apply(lambda x: x.get("communication", 0) if isinstance(x, dict) else 0).mean() if "components" in df.columns else 5,
                ]
            })
            
            fig_components = px.bar(
                components_df,
                x="Component",
                y="Average Score",
                title="Average Component Scores",
                color="Average Score",
                color_continuous_scale="Viridis"
            )
            fig_components.update_layout(template="plotly_white", showlegend=False)
            st.plotly_chart(fig_components, use_container_width=True)


def page_rankings():
    """Render the rankings page with sortable, filterable candidate table."""
    st.title("🏅 Rankings")
    st.markdown("---")
    
    if st.session_state.candidates_df is None or len(st.session_state.candidates_df) == 0:
        st.info("📁 Select a batch file from the sidebar to view rankings")
        return
    
    df = st.session_state.candidates_df.copy()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        score_min = st.slider("Minimum Score", 0, 100, 0)
    with col2:
        score_max = st.slider("Maximum Score", 0, 100, 100)
    with col3:
        status_filter = st.multiselect(
            "Filter by Status",
            ["Shortlisted", "Consider", "Rejected"],
            default=["Shortlisted", "Consider", "Rejected"]
        )
    
    # Apply filters
    df = df[(df["final_score"] >= score_min) & (df["final_score"] <= score_max)]
    
    # Map scores to status
    df["status"] = df["final_score"].apply(lambda x: "Shortlisted" if x >= 75 else ("Consider" if x >= 50 else "Rejected"))
    df = df[df["status"].isin(status_filter)]
    
    # Display table
    st.subheader(f"Showing {len(df)} Candidates")
    
    # Create display dataframe
    display_df = df[["rank", "candidate_name", "final_score"]].copy()
    
    # Add component scores if available
    if "components" in df.columns:
        try:
            components = df["components"].apply(pd.Series)
            for col in ["skills", "experience", "education", "projects", "communication"]:
                if col in components.columns:
                    display_df[col.capitalize()] = components[col].round(0).astype(int)
        except:
            pass
    
    display_df["Status"] = df["final_score"].apply(lambda x: "🟢 Shortlisted" if x >= 75 else ("🟡 Consider" if x >= 50 else "🔴 Rejected"))
    display_df.columns = ["Rank", "Candidate Name", "Final Score", "Status"]
    
    # Display as table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Final Score": st.column_config.ProgressColumn(
                "Final Score",
                min_value=0,
                max_value=100,
            ),
        }
    )
    
    # Export button
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Rankings (CSV)",
        data=csv,
        file_name=f"rankings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


def page_candidate_analysis():
    """Render detailed analysis for a selected candidate."""
    st.title("🔍 Candidate Analysis")
    st.markdown("---")
    
    if st.session_state.candidates_df is None or len(st.session_state.candidates_df) == 0:
        st.info("📁 Select a batch file from the sidebar to view candidate analysis")
        return
    
    df = st.session_state.candidates_df
    
    # Candidate selector
    candidate_names = df["candidate_name"].unique()
    selected_candidate_name = st.selectbox("Select Candidate", candidate_names, key="candidate_selector")
    
    # Get candidate data
    candidate_data = df[df["candidate_name"] == selected_candidate_name].iloc[0]
    
    # Candidate header
    col1, col2, col3 = st.columns([0.6, 0.2, 0.2])
    
    with col1:
        st.markdown(f"## {candidate_data['candidate_name']}")
    
    with col2:
        status, _ = get_candidate_status(candidate_data["final_score"])
        st.markdown(render_status_badge(status), unsafe_allow_html=True)
    
    with col3:
        st.markdown(render_score_badge(candidate_data["final_score"]), unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Rank and recommendation
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Rank", f"#{candidate_data.get('rank', 'N/A')}")
    
    with col2:
        if candidate_data["final_score"] >= 75:
            rec_text = "✅ Strong candidate. Recommended for interview."
            rec_color = "#10b981"
        elif candidate_data["final_score"] >= 50:
            rec_text = "⚠️ Moderate candidate. Further evaluation recommended."
            rec_color = "#f59e0b"
        else:
            rec_text = "❌ Candidate does not meet requirements."
            rec_color = "#ef4444"
        
        st.markdown(f"<p style='color: {rec_color}; font-weight: bold; font-size: 1.1rem'>{rec_text}</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Score breakdown - Radar chart
    st.subheader("📊 Score Breakdown")
    
    if "components" in candidate_data and isinstance(candidate_data["components"], dict):
        components = candidate_data["components"]
    else:
        components = {
            "skills": candidate_data.get("skills_score", 5),
            "experience": candidate_data.get("experience_score", 5),
            "education": candidate_data.get("education_score", 5),
            "projects": candidate_data.get("projects_score", 5),
            "communication": candidate_data.get("communication_score", 5)
        }
    
    # Radar chart
    fig = go.Figure(data=go.Scatterpolar(
        r=[components.get(key, 0) for key in ["skills", "experience", "education", "projects", "communication"]],
        theta=["Skills", "Experience", "Education", "Projects", "Communication"],
        fill="toself",
        name="Score",
        line_color="rgba(102, 126, 234, 1)",
        fillcolor="rgba(102, 126, 234, 0.3)"
    ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 10])),
        showlegend=False,
        template="plotly_white",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Component details
    st.subheader("📋 Component Details")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    component_details = {
        "Skills": ("skills", col1),
        "Experience": ("experience", col2),
        "Education": ("education", col3),
        "Projects": ("projects", col4),
        "Communication": ("communication", col5)
    }
    
    for comp_name, (comp_key, comp_col) in component_details.items():
        score = components.get(comp_key, 0)
        with comp_col:
            color = get_score_color(score)
            st.markdown(f"**{comp_name}**")
            st.markdown(f"<p style='font-size: 2rem; color: {color}; font-weight: bold; text-align: center'>{score:.0f}/10</p>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Analysis details
    st.subheader("📝 Detailed Analysis")
    
    if "analysis" in candidate_data and isinstance(candidate_data["analysis"], dict):
        analysis = candidate_data["analysis"]
        
        # Strengths
        if "strengths" in analysis and analysis["strengths"]:
            st.markdown("**✅ Strengths:**")
            for strength in analysis["strengths"]:
                st.markdown(f"• {strength}")
            st.markdown("")
        
        # Weaknesses
        if "weaknesses" in analysis and analysis["weaknesses"]:
            st.markdown("**⚠️ Weaknesses:**")
            for weakness in analysis["weaknesses"]:
                st.markdown(f"• {weakness}")
            st.markdown("")
        
        # Skills analysis
        if "matching_skills" in analysis or "matched_skills" in analysis:
            matched = analysis.get("matching_skills") or analysis.get("matched_skills", [])
            missing = analysis.get("missing_skills", [])
            
            st.markdown("**🎯 Skills Analysis:**")
            col1, col2 = st.columns(2)
            
            with col1:
                if matched:
                    st.markdown("**Matched Skills:**")
                    for skill in matched[:5]:
                        if isinstance(skill, dict):
                            st.markdown(f"✅ {skill.get('jd_skill', skill)}")
                        else:
                            st.markdown(f"✅ {skill}")
            
            with col2:
                if missing:
                    st.markdown("**Missing Skills:**")
                    for skill in missing[:5]:
                        st.markdown(f"❌ {skill}")
        
        # Overall summary
        if "overall_summary" in analysis:
            st.markdown("**📌 Summary:**")
            st.markdown(analysis["overall_summary"])
    else:
        st.info("Detailed analysis not available for this candidate")
    
    st.markdown("---")
    
    # Export candidate report
    st.subheader("📄 Export Options")
    
    json_report = json.dumps(candidate_data.to_dict(), indent=2, default=str)
    st.download_button(
        label="📥 Download Candidate Report (JSON)",
        data=json_report,
        file_name=f"candidate_{selected_candidate_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
        mime="application/json"
    )


def page_analytics():
    """Render advanced analytics and visualizations."""
    st.title("📊 Analytics")
    st.markdown("---")
    
    if st.session_state.candidates_df is None or len(st.session_state.candidates_df) == 0:
        st.info("📁 Select a batch file from the sidebar to view analytics")
        return
    
    df = st.session_state.candidates_df
    
    # Score distribution histogram
    st.subheader("📈 Score Distribution")
    fig = px.histogram(
        df,
        x="final_score",
        nbins=20,
        title="Candidate Score Distribution",
        labels={"final_score": "Final Score", "count": "Number of Candidates"},
        color_discrete_sequence=["#667eea"]
    )
    fig.update_layout(template="plotly_white", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)
    
    # Component comparison
    st.subheader("🎯 Component Comparison")
    
    if "components" in df.columns:
        try:
            components_avg = []
            for comp in ["skills", "experience", "education", "projects", "communication"]:
                avg = df["components"].apply(lambda x: x.get(comp, 5) if isinstance(x, dict) else 5).mean()
                components_avg.append({"Component": comp.capitalize(), "Average Score": avg})
            
            components_df = pd.DataFrame(components_avg)
            fig = px.bar(
                components_df,
                x="Component",
                y="Average Score",
                title="Average Component Scores Across All Candidates",
                color="Average Score",
                color_continuous_scale="Viridis"
            )
            fig.update_layout(template="plotly_white", yaxis_range=[0, 10])
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not display component comparison: {str(e)}")
    
    # Top performers
    st.subheader("🏆 Top 10 Performers")
    top_10 = df.nlargest(10, "final_score")[["rank", "candidate_name", "final_score"]].copy()
    top_10["Status"] = top_10["final_score"].apply(lambda x: "🟢 Shortlisted" if x >= 75 else "🟡 Consider")
    
    fig = px.bar(
        top_10,
        x="candidate_name",
        y="final_score",
        color="final_score",
        title="Top 10 Candidates by Score",
        labels={"candidate_name": "Candidate", "final_score": "Final Score"},
        color_continuous_scale="Greens"
    )
    fig.update_layout(
        template="plotly_white",
        yaxis_range=[0, 100],
        xaxis_tickangle=-45,
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Status breakdown
    st.subheader("📊 Candidate Status Breakdown")
    
    col1, col2 = st.columns(2)
    
    with col1:
        status_counts = pd.cut(df["final_score"], bins=[0, 50, 75, 100], labels=["Rejected", "Consider", "Shortlisted"]).value_counts()
        fig = px.pie(
            values=status_counts.values,
            names=status_counts.index,
            title="Status Distribution",
            color_discrete_map={"Rejected": "#ef4444", "Consider": "#f59e0b", "Shortlisted": "#10b981"}
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        stats_text = f"""
        **Statistics Summary:**
        
        - Total Candidates: {len(df)}
        - Average Score: {df['final_score'].mean():.2f}
        - Median Score: {df['final_score'].median():.2f}
        - Std Dev: {df['final_score'].std():.2f}
        - Min Score: {df['final_score'].min():.2f}
        - Max Score: {df['final_score'].max():.2f}
        
        **Status Breakdown:**
        - Shortlisted (≥75): {len(df[df['final_score'] >= 75])} ({len(df[df['final_score'] >= 75])/len(df)*100:.1f}%)
        - Consider (50-74): {len(df[(df['final_score'] >= 50) & (df['final_score'] < 75)])} ({len(df[(df['final_score'] >= 50) & (df['final_score'] < 75)])/len(df)*100:.1f}%)
        - Rejected (<50): {len(df[df['final_score'] < 50])} ({len(df[df['final_score'] < 50])/len(df)*100:.1f}%)
        """
        st.markdown(stats_text)


def page_system_info():
    """Render system information and configuration."""
    st.title("ℹ️ System Information")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔧 System Status")
        st.markdown(f"""
        **Frontend Status:** ✅ Running
        
        **Framework:** Streamlit
        
        **Version:** {st.__version__}
        
        **Backend Pipeline:** Available (JSON outputs found)
        
        **Embedding Model:** sentence-transformers (all-MiniLM-L6-v2)
        
        **Semantic Matching Threshold:** 0.72
        """)
    
    with col2:
        st.subheader("📁 File Information")
        
        batch_files = get_batch_files()
        st.markdown(f"""
        **Output Directory:** {OUTPUTS_DIR}
        
        **Directory Exists:** ✅ Yes
        
        **Available Batch Files:** {len(batch_files)}
        
        **Last Updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """)
    
    st.markdown("---")
    
    st.subheader("📊 Available Batch Files")
    
    if batch_files:
        for i, filename in enumerate(batch_files[:5], 1):
            file_path = OUTPUTS_DIR / filename
            file_size = file_path.stat().st_size / 1024  # KB
            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
            st.markdown(f"{i}. **{filename}** ({file_size:.1f} KB) - {file_time.strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.info("No batch files found. Run the backend pipeline to generate results.")
    
    st.markdown("---")
    
    st.subheader("🔗 Module Information")
    st.markdown("""
    **Backend Modules:**
    - `llm.py` - Gemini API integration for semantic analysis
    - `parser.py` - PDF text extraction and processing
    - `prompts.py` - LLM prompt templates
    - `scoring.py` - Candidate scoring and ranking engine
    - `utils.py` - Utility functions for data handling
    - `app.py` - Main pipeline orchestrator
    
    **Frontend Components:**
    - `streamlit_app.py` - Main dashboard and UI
    - `dashboard.py` - Dashboard components (modular)
    - `charts.py` - Chart and visualization utilities (modular)
    - `candidate_view.py` - Candidate analysis components (modular)
    - `utils.py` - Frontend utilities (modular)
    """)
    
    st.markdown("---")
    
    st.subheader("📝 Data Structure Sample")
    
    if st.session_state.batch_data:
        st.json(st.session_state.batch_data if isinstance(st.session_state.batch_data, dict) else {"sample": "data"})
    else:
        st.info("Select a batch file to view data structure sample.")


# ==============================================================================
# SIDEBAR
# ==============================================================================

def render_sidebar():
    """Render the sidebar with navigation and file controls."""
    with st.sidebar:
        # Header
        st.markdown("## 🤖 AI HR Shortlisting")
        st.markdown("**Professional Resume Screening Dashboard**")
        st.markdown("---")
        
        # Navigation
        st.markdown("### 📍 Navigation")
        current_page = st.radio(
            "Select Page",
            ["Upload", "Dashboard", "Rankings", "Candidate Analysis", "Analytics", "System Info"],
            label_visibility="collapsed"
        )
        st.session_state.current_page = current_page
        
        st.markdown("---")
        
        # File selector
        st.markdown("### 📂 Batch Results")
        batch_files = get_batch_files()
        
        if batch_files:
            selected_file = st.selectbox(
                "Select Batch File",
                batch_files,
                label_visibility="collapsed"
            )
            
            if selected_file != st.session_state.selected_batch:
                st.session_state.selected_batch = selected_file
                batch_data = load_batch_results(selected_file)
                
                if batch_data:
                    st.session_state.batch_data = batch_data
                    st.session_state.candidates_df = extract_candidate_dataframe(batch_data)
                    st.success("✅ Batch loaded successfully!")
            
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()
        
        else:
            st.info("📁 No batch files found. Run the backend pipeline to generate results.")
        
        st.markdown("---")
        
        # Info section
        st.markdown("### ℹ️ About")
        st.markdown("""
        This dashboard visualizes AI-powered resume screening results.
        
        **Key Features:**
        - Real-time candidate rankings
        - Detailed skill analysis
        - Visual performance analytics
        - Export capabilities
        
        **Data Source:** Backend JSON outputs
        
        **Last Refresh:** {0}
        """.format(datetime.now().strftime("%H:%M:%S")))


# ==============================================================================
# MAIN APPLICATION
# ==============================================================================

def main():
    """Main application entry point."""
    # Render sidebar
    render_sidebar()
    
    # If batch_data exists in session_state but candidates_df is empty, try to extract
    if st.session_state.batch_data and (st.session_state.candidates_df is None):
        try:
            st.session_state.candidates_df = extract_candidate_dataframe(st.session_state.batch_data)
        except Exception:
            st.warning("Could not build candidate dataframe from batch data.")

    # Route to selected page
    if st.session_state.current_page == "Upload":
        # Render upload UI - connects frontend to backend
        upload_section.render_upload_page()
    elif st.session_state.current_page == "Dashboard":
        # Render dashboard with candidate results
        dashboard.render_dashboard(st.session_state.candidates_df)
    elif st.session_state.current_page == "Rankings":
        page_rankings()
    elif st.session_state.current_page == "Candidate Analysis":
        page_candidate_analysis()
    elif st.session_state.current_page == "Analytics":
        # Render charts and visualizations
        charts.render_charts(st.session_state.candidates_df)
    elif st.session_state.current_page == "System Info":
        page_system_info()


if __name__ == "__main__":
    main()
