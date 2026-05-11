"""
Dashboard Module

Displays AI-powered resume screening results and analytics.

This module is ONLY responsible for:
- Displaying dashboard UI and metrics
- Showing candidate rankings and analysis
- Generating insights from results

It does NOT handle:
- File uploads (that's upload_section.py)
- Backend processing (that's backend_connector.py)
- Session state management (that's streamlit_app.py)

The dashboard receives processed candidate results from session state.
"""

import streamlit as st
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional


# ==============================================================================
# UTILITY FUNCTIONS FOR SCORING AND STATUS
# ==============================================================================

def get_score_color(score: float) -> str:
    """
    Get hex color code based on score.
    
    Args:
        score: Candidate score (0-100)
    
    Returns:
        Hex color code
    """
    if score >= 85:
        return "#10b981"  # Green - Excellent
    elif score >= 70:
        return "#3b82f6"  # Blue - Good
    elif score >= 50:
        return "#f59e0b"  # Orange - Average
    else:
        return "#ef4444"  # Red - Poor


def get_score_label(score: float) -> str:
    """
    Get strength label based on score.
    
    Args:
        score: Candidate score (0-100)
    
    Returns:
        Label string
    """
    if score >= 85:
        return "Excellent Match"
    elif score >= 70:
        return "Good Match"
    elif score >= 50:
        return "Average Match"
    else:
        return "Poor Match"


def get_status_badge(score: float) -> str:
    """
    Get status badge text based on score.
    
    Args:
        score: Candidate score (0-100)
    
    Returns:
        Status badge text
    """
    if score >= 70:
        return "✅ Shortlisted"
    elif score >= 50:
        return "⚠️ Review"
    else:
        return "❌ Rejected"


def get_recommendation(top_score: Optional[float]) -> str:
    """
    Get final hiring recommendation based on top candidate score.
    
    Args:
        top_score: Highest candidate score
    
    Returns:
        Recommendation text
    """
    if top_score is None or top_score == 0:
        return "🤔 No candidates analyzed yet. Upload and analyze resumes to get recommendations."
    elif top_score >= 85:
        return "🚀 Hire Immediately - Excellent candidate match found!"
    elif top_score >= 70:
        return "👥 Consider for Interview - Good candidate available"
    elif top_score >= 50:
        return "📋 Needs Review - Candidates need further evaluation"
    else:
        return "❌ No Strong Matches - Consider expanding candidate pool"


# ==============================================================================
# METRIC CARDS - Display key statistics
# ==============================================================================

def show_metric_cards(df: pd.DataFrame) -> None:
    """
    Display responsive metric cards showing key statistics.
    
    Args:
        df: Candidate results dataframe
    """
    # Calculate metrics - handle missing columns
    total_candidates = len(df)
    avg_score = df["final_score"].mean() if "final_score" in df.columns and len(df) > 0 else 0
    highest_score = df["final_score"].max() if "final_score" in df.columns and len(df) > 0 else 0
    shortlisted_count = len(df[df["final_score"] >= 70]) if "final_score" in df.columns and len(df) > 0 else 0
    
    # Create 4 columns for metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Metric 1: Total Candidates
    with col1:
        st.metric(
            label="📊 Total Candidates",
            value=f"{total_candidates}",
            delta=None
        )
    
    # Metric 2: Average Score
    with col2:
        st.metric(
            label="📈 Average Score",
            value=f"{avg_score:.1f}",
            delta=None
        )
    
    # Metric 3: Highest Score
    with col3:
        st.metric(
            label="⭐ Highest Score",
            value=f"{highest_score:.1f}",
            delta=None
        )
    
    # Metric 4: Shortlisted Count
    with col4:
        st.metric(
            label="✅ Shortlisted",
            value=f"{shortlisted_count}",
            delta=f"{(shortlisted_count/total_candidates*100):.0f}%" if total_candidates > 0 else "0%"
        )


# ==============================================================================
# TOP CANDIDATE SECTION - Highlight the best candidate
# ==============================================================================

def show_top_candidate(df: pd.DataFrame) -> None:
    """
    Display a highlighted section showing the top ranked candidate.
    
    Args:
        df: Candidate results dataframe
    """
    if len(df) == 0:
        return
    
    # Get top candidate (rank 1)
    top = df.iloc[0]
    
    score = top.get("final_score", 0)
    color = get_score_color(score)
    label = get_score_label(score)
    
    # Create highlighted container
    st.markdown("---")
    st.subheader("🏆 Top Candidate Match")
    
    # Use columns for visual layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown(f"### {top.get('candidate_name', 'Unknown')}")
        st.markdown(f"**Status:** {label}")
        st.markdown(f"**Match Strength:** {score:.1f}/100")
    
    with col2:
        # Display score as large colored number
        st.markdown(
            f"""
            <div style="
                background-color: {color};
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
            ">
                <h1 style="margin: 0;">{score:.1f}</h1>
                <p style="margin: 0; font-size: 12px;">Match Score</p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Show component breakdown if available
    breakdown = top.get("breakdown", {})
    if breakdown:
        st.markdown("**Component Scores:**")
        
        breakdown_cols = st.columns(5)
        
        components = {
            "skills": "💼 Skills",
            "experience": "📚 Experience",
            "education": "🎓 Education",
            "projects": "🚀 Projects",
            "communication": "💬 Communication"
        }
        
        for idx, (key, label) in enumerate(components.items()):
            with breakdown_cols[idx]:
                comp_data = breakdown.get(key, {})
                comp_score = comp_data.get("score", 0) if isinstance(comp_data, dict) else 0
                st.metric(label, f"{comp_score}/10")


# ==============================================================================
# SHORTLIST TABLE - Display ranked candidates
# ==============================================================================

def show_shortlist_table(df: pd.DataFrame) -> None:
    """
    Display a clean ranked candidates table with status badges.
    
    Args:
        df: Candidate results dataframe
    """
    if len(df) == 0:
        return
    
    st.markdown("---")
    st.subheader("📋 Candidate Rankings")
    
    # Prepare display dataframe - handle missing columns gracefully
    display_data = {
        "Rank": df["rank"].tolist() if "rank" in df.columns else list(range(1, len(df) + 1)),
        "Candidate Name": df["candidate_name"].tolist() if "candidate_name" in df.columns else ["Unknown"] * len(df),
        "Final Score": df["final_score"].apply(lambda x: f"{x:.1f}").tolist() if "final_score" in df.columns else ["N/A"] * len(df),
        "Skills": df["skills_score"].apply(lambda x: f"{x:.0f}/10").tolist() if "skills_score" in df.columns else ["N/A"] * len(df),
        "Experience": df["experience_score"].apply(lambda x: f"{x:.0f}/10").tolist() if "experience_score" in df.columns else ["N/A"] * len(df),
        "Projects": df["projects_score"].apply(lambda x: f"{x:.0f}/10").tolist() if "projects_score" in df.columns else ["N/A"] * len(df),
        "Communication": df["communication_score"].apply(lambda x: f"{x:.0f}/10").tolist() if "communication_score" in df.columns else ["N/A"] * len(df),
        "Status": df["final_score"].apply(get_status_badge).tolist() if "final_score" in df.columns else ["N/A"] * len(df),
    }
    
    display_df = pd.DataFrame(display_data)
    
    # Display as dataframe with styling
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
    
    # Show individual candidate details in expanders
    st.markdown("**Detailed Breakdown:**")
    
    for idx, row in df.iterrows():
        with st.expander(f"🔍 {row.get('candidate_name', 'Unknown')} - Score: {row.get('final_score', 0):.1f}"):
            # Left column: Basic info
            col1, col2 = st.columns([1, 1])
            
            with col1:
                st.markdown(f"**Rank:** #{row.get('rank', 'N/A')}")
                st.markdown(f"**Final Score:** {row.get('final_score', 0):.1f}/100")
                st.markdown(f"**Status:** {get_status_badge(row.get('final_score', 0))}")
            
            with col2:
                st.markdown(f"**Match Level:** {get_score_label(row.get('final_score', 0))}")
            
            # Show component scores as mini bar chart
            st.markdown("**Component Scores:**")
            components = {
                "Skills": row.get("skills_score", 0),
                "Experience": row.get("experience_score", 0),
                "Education": row.get("education_score", 0),
                "Projects": row.get("projects_score", 0),
                "Communication": row.get("communication_score", 0)
            }
            
            for comp_name, comp_score in components.items():
                st.write(f"{comp_name}: {comp_score:.0f}/10")
                st.progress(min(comp_score / 10, 1.0))


# ==============================================================================
# INSIGHTS SECTION - Generate automatic recruiter insights
# ==============================================================================

def generate_insights(df: pd.DataFrame) -> List[str]:
    """
    Generate dynamic recruiter insights from candidate scores.
    
    Args:
        df: Candidate results dataframe
    
    Returns:
        List of insight strings
    """
    insights = []
    
    if len(df) == 0:
        return ["📊 No candidates to analyze yet. Upload resumes to generate insights."]
    
    # Insight 1: Overall quality
    avg_score = df["final_score"].mean() if "final_score" in df.columns else 0
    if avg_score >= 75:
        insights.append("✅ Strong candidate pool with competitive average scores.")
    elif avg_score >= 60:
        insights.append("📈 Good candidate pool. Average scores indicate reasonable matches.")
    else:
        insights.append("⚠️ Candidate pool needs review. Average scores are below threshold.")
    
    # Insight 2: Shortlist availability
    shortlisted = len(df[df["final_score"] >= 70]) if "final_score" in df.columns else 0
    if shortlisted == 0:
        insights.append("❌ No candidates meet the shortlist threshold (70+).")
    elif shortlisted == 1:
        insights.append(f"✅ {shortlisted} candidate meets shortlist criteria. Consider expanding pool.")
    else:
        insights.append(f"✅ {shortlisted} candidates are shortlisted. Good selection to choose from.")
    
    # Insight 3: Component analysis - Skills
    avg_skills = df["skills_score"].mean() if "skills_score" in df.columns else 0
    if avg_skills < 6:
        insights.append("📌 Skills matching is weak across pool. Consider upskilling or broader search.")
    elif avg_skills > 8:
        insights.append("🎯 Excellent skills match across candidates.")
    
    # Insight 4: Component analysis - Projects
    avg_projects = df["projects_score"].mean() if "projects_score" in df.columns else 0
    if avg_projects > 8:
        insights.append("🚀 Project portfolio quality is strong.")
    
    # Insight 5: Top performer
    top_score = df["final_score"].max() if "final_score" in df.columns else 0
    if top_score >= 85:
        insights.append("⭐ Top candidate is an excellent match. Highly recommended for immediate interview.")
    
    # Insight 6: Diversity of scores
    score_std = df["final_score"].std()
    if score_std > 15:
        insights.append("📊 Wide variance in candidate quality. Clear differentiation in rankings.")
    
    return insights


def show_insights(df: pd.DataFrame) -> None:
    """
    Display automatic insights in a clean box.
    
    Args:
        df: Candidate results dataframe
    """
    insights = generate_insights(df)
    
    st.markdown("---")
    st.subheader("💡 Recruiter Insights")
    
    for insight in insights:
        st.info(insight)


# ==============================================================================
# RECOMMENDATION BOX - Final hiring recommendation
# ==============================================================================

def show_recommendation(df: pd.DataFrame) -> None:
    """
    Display final hiring recommendation based on top candidate score.
    
    Args:
        df: Candidate results dataframe
    """
    top_score = df["final_score"].max() if len(df) > 0 else 0
    recommendation = get_recommendation(top_score)
    
    st.markdown("---")
    st.subheader("📢 Final Recommendation")
    
    # Style the recommendation box
    if top_score >= 85:
        st.success(recommendation, icon="🚀")
    elif top_score >= 70:
        st.info(recommendation, icon="👥")
    elif top_score >= 50:
        st.warning(recommendation, icon="📋")
    else:
        st.error(recommendation, icon="❌")


# ==============================================================================
# EMPTY STATE - When no results are available
# ==============================================================================

def show_empty_state() -> None:
    """Display beautiful empty state when no candidate results available."""
    st.markdown("---")
    
    # Create centered empty state
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div style="text-align: center; padding: 40px;">
                <h1 style="font-size: 48px; margin: 0;">📂</h1>
                <h2>No Candidate Results Yet</h2>
                <p style="font-size: 16px; color: #666;">
                    Upload your job description and candidate resumes to analyze and view dashboard insights.
                </p>
                <p style="font-size: 14px; color: #999;">
                    Click "Upload" in the sidebar to get started.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )


# ==============================================================================
# MAIN DASHBOARD FUNCTION
# ==============================================================================

def render_dashboard(candidates_df: Optional[pd.DataFrame]) -> None:
    """
    Main dashboard rendering function.
    
    This function orchestrates all dashboard components and is called from streamlit_app.py.
    
    Args:
        candidates_df: DataFrame with candidate results or None if no data available
    """
    # ========== DASHBOARD HEADER ==========
    st.title("🤖 AI HR Resume Shortlisting Dashboard")
    st.markdown(
        "**Semantic candidate analysis powered by Gemini + Sentence Transformers**"
    )
    
    # ========== EMPTY STATE CHECK ==========
    if candidates_df is None or len(candidates_df) == 0:
        show_empty_state()
        return
    
    # ========== METRIC CARDS ==========
    show_metric_cards(candidates_df)
    
    # ========== TOP CANDIDATE SECTION ==========
    show_top_candidate(candidates_df)
    
    # ========== SHORTLIST TABLE ==========
    show_shortlist_table(candidates_df)
    
    # ========== INSIGHTS SECTION ==========
    show_insights(candidates_df)
    
    # ========== RECOMMENDATION BOX ==========
    show_recommendation(candidates_df)
    
    # ========== FOOTER ==========
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #999; font-size: 12px; padding: 20px;">
            <p>AI HR Shortlisting System | Powered by Gemini AI</p>
        </div>
        """,
        unsafe_allow_html=True
    )
