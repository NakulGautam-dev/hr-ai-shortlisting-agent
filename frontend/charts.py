"""
Charts and Visualizations Module

Professional analytics visualizations for HR Resume Shortlisting Dashboard.

This module is ONLY responsible for:
- Creating Plotly visualizations
- Rendering interactive charts
- Generating chart-based insights

It does NOT handle:
- File uploads
- Backend processing
- Data loading
- Session state management

All data is received from streamlit_app.py as processed dataframes.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import List, Dict, Any, Optional, Tuple


# ==============================================================================
# HELPER FUNCTIONS - Color coding and data formatting
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
        return "#10b981"  # Green
    elif score >= 70:
        return "#3b82f6"  # Blue
    elif score >= 50:
        return "#f59e0b"  # Orange
    else:
        return "#ef4444"  # Red


def get_status_category(score: float) -> str:
    """Get status category from score."""
    if score >= 70:
        return "Shortlisted"
    elif score >= 50:
        return "Review"
    else:
        return "Rejected"


# ==============================================================================
# CHART 1: SCORE DISTRIBUTION HISTOGRAM
# ==============================================================================

def create_score_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create histogram showing distribution of candidate final scores.
    
    Args:
        df: Candidate dataframe with final_score column
    
    Returns:
        Plotly Figure object
    """
    if "final_score" not in df.columns or len(df) == 0:
        return None
    
    scores = df["final_score"].dropna()
    
    fig = go.Figure()
    
    # Add histogram
    fig.add_trace(go.Histogram(
        x=scores,
        nbinsx=max(10, len(df) // 2),
        name="Score Distribution",
        marker=dict(
            color="#3b82f6",
            line=dict(color="#1e40af", width=1)
        ),
        hovertemplate="<b>Score Range:</b> %{x:.0f}<br><b>Candidates:</b> %{y}<extra></extra>"
    ))
    
    # Update layout
    fig.update_layout(
        title="📊 Score Distribution Analysis",
        xaxis_title="Final Score",
        yaxis_title="Number of Candidates",
        template="plotly_white",
        showlegend=False,
        height=400,
        hovermode="x unified",
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


def show_score_distribution_insight(df: pd.DataFrame) -> str:
    """Generate insight text for score distribution."""
    if "final_score" not in df.columns:
        return None
    
    scores = df["final_score"]
    mean = scores.mean()
    median = scores.median()
    
    # Generate insight
    if mean > 75:
        return "✅ Strong pool with most candidates scoring 75+."
    elif mean > 60:
        return "📈 Good distribution. Most candidates meet basic threshold."
    else:
        return "⚠️ Scores spread across lower range. Consider broader search."


# ==============================================================================
# CHART 2: SKILL BREAKDOWN BAR CHART
# ==============================================================================

def create_breakdown_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create grouped bar chart comparing candidates across skill categories.
    
    Args:
        df: Candidate dataframe
    
    Returns:
        Plotly Figure object
    """
    # Extract component scores
    components = ["skills_score", "experience_score", "education_score", "projects_score", "communication_score"]
    available_components = [c for c in components if c in df.columns]
    
    if len(available_components) == 0 or "candidate_name" not in df.columns:
        return None
    
    # Prepare data - limit to top 10 candidates
    display_df = df.head(10).copy()
    
    # Map component names
    component_labels = {
        "skills_score": "Skills",
        "experience_score": "Experience",
        "education_score": "Education",
        "projects_score": "Projects",
        "communication_score": "Communication"
    }
    
    # Create figure
    fig = go.Figure()
    
    # Add trace for each component
    colors = ["#3b82f6", "#8b5cf6", "#ec4899", "#f59e0b", "#10b981"]
    
    for idx, component in enumerate(available_components):
        fig.add_trace(go.Bar(
            x=display_df["candidate_name"],
            y=display_df[component],
            name=component_labels.get(component, component),
            marker=dict(color=colors[idx % len(colors)]),
            hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y:.1f}<extra></extra>"
        ))
    
    # Update layout
    fig.update_layout(
        title="💼 Candidate Component Scores (Top 10)",
        xaxis_title="Candidate Name",
        yaxis_title="Score (0-10)",
        template="plotly_white",
        barmode="group",
        height=450,
        hovermode="x unified",
        xaxis_tickangle=-45,
        margin=dict(l=50, r=50, t=50, b=100)
    )
    
    return fig


# ==============================================================================
# CHART 3: LEADERBOARD - TOP CANDIDATES BAR CHART
# ==============================================================================

def create_leaderboard_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create horizontal bar chart showing top candidates ranked by score.
    
    Args:
        df: Candidate dataframe sorted by final_score
    
    Returns:
        Plotly Figure object
    """
    if "final_score" not in df.columns or "candidate_name" not in df.columns:
        return None
    
    # Get top 15 candidates
    top_df = df.head(15).copy()
    top_df = top_df.sort_values("final_score", ascending=True)
    
    # Create color list based on scores
    bar_colors = [get_score_color(score) for score in top_df["final_score"]]
    
    # Create figure
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=top_df["candidate_name"],
        x=top_df["final_score"],
        orientation="h",
        marker=dict(
            color=bar_colors,
            line=dict(color="white", width=2)
        ),
        text=top_df["final_score"].apply(lambda x: f"{x:.1f}"),
        textposition="auto",
        hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}<extra></extra>"
    ))
    
    # Update layout
    fig.update_layout(
        title="🏆 Candidate Leaderboard (Top 15)",
        xaxis_title="Final Score",
        yaxis_title="Candidate Name",
        template="plotly_white",
        showlegend=False,
        height=500,
        hovermode="y unified",
        margin=dict(l=200, r=50, t=50, b=50)
    )
    
    return fig


# ==============================================================================
# CHART 4: RADAR CHART FOR TOP CANDIDATE
# ==============================================================================

def create_radar_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create radar/spider chart for top candidate showing component breakdown.
    
    Args:
        df: Candidate dataframe
    
    Returns:
        Plotly Figure object
    """
    if len(df) == 0:
        return None
    
    # Get top candidate
    top = df.iloc[0]
    candidate_name = top.get("candidate_name", "Top Candidate")
    
    # Extract component scores
    components = {
        "Skills": top.get("skills_score", 0),
        "Experience": top.get("experience_score", 0),
        "Education": top.get("education_score", 0),
        "Projects": top.get("projects_score", 0),
        "Communication": top.get("communication_score", 0)
    }
    
    # Remove components with zero scores if all are missing
    components = {k: v for k, v in components.items() if v > 0 or any(components.values())}
    
    if len(components) == 0:
        return None
    
    # Create figure
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=list(components.values()),
        theta=list(components.keys()),
        fill="toself",
        name=candidate_name,
        marker=dict(color="#3b82f6"),
        fillcolor="rgba(59, 130, 246, 0.3)",
        line=dict(color="#1e40af", width=2),
        hovertemplate="<b>%{theta}</b><br>Score: %{r:.1f}/10<extra></extra>"
    ))
    
    # Update layout
    fig.update_layout(
        title=f"🎯 Component Breakdown - {candidate_name}",
        template="plotly_white",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 10],
                tickfont=dict(size=10)
            )
        ),
        height=450,
        showlegend=False,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


# ==============================================================================
# CHART 5: STATUS DISTRIBUTION PIE CHART
# ==============================================================================

def create_status_pie_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create donut chart showing distribution of candidates by status.
    
    Args:
        df: Candidate dataframe with final_score column
    
    Returns:
        Plotly Figure object
    """
    if "final_score" not in df.columns or len(df) == 0:
        return None
    
    # Calculate status counts
    shortlisted = len(df[df["final_score"] >= 70])
    review = len(df[(df["final_score"] >= 50) & (df["final_score"] < 70)])
    rejected = len(df[df["final_score"] < 50])
    
    # Create data
    labels = ["Shortlisted", "Review", "Rejected"]
    values = [shortlisted, review, rejected]
    colors = ["#10b981", "#f59e0b", "#ef4444"]
    
    # Filter out zero values
    labels = [l for l, v in zip(labels, values) if v > 0]
    values = [v for v in values if v > 0]
    colors = colors[:len(values)]
    
    if len(values) == 0:
        return None
    
    # Create figure
    fig = go.Figure()
    
    fig.add_trace(go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        hole=0.4,
        textposition="inside",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>"
    ))
    
    # Update layout
    fig.update_layout(
        title="📊 Candidate Status Distribution",
        template="plotly_white",
        height=400,
        showlegend=True,
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


# ==============================================================================
# CHART 6: AVERAGE CATEGORY PERFORMANCE
# ==============================================================================

def create_category_performance_chart(df: pd.DataFrame) -> go.Figure:
    """
    Create bar chart showing average score across all skill categories.
    
    Args:
        df: Candidate dataframe
    
    Returns:
        Plotly Figure object
    """
    components = ["skills_score", "experience_score", "education_score", "projects_score", "communication_score"]
    available_components = [c for c in components if c in df.columns]
    
    if len(available_components) == 0:
        return None
    
    # Calculate averages
    component_labels = {
        "skills_score": "Skills",
        "experience_score": "Experience",
        "education_score": "Education",
        "projects_score": "Projects",
        "communication_score": "Communication"
    }
    
    averages = []
    labels = []
    
    for component in available_components:
        avg = df[component].mean()
        averages.append(avg)
        labels.append(component_labels.get(component, component))
    
    # Create figure
    fig = go.Figure()
    
    # Determine colors based on performance
    colors = []
    for avg in averages:
        if avg >= 8:
            colors.append("#10b981")  # Green - Excellent
        elif avg >= 6:
            colors.append("#3b82f6")  # Blue - Good
        elif avg >= 4:
            colors.append("#f59e0b")  # Orange - Fair
        else:
            colors.append("#ef4444")  # Red - Weak
    
    fig.add_trace(go.Bar(
        x=labels,
        y=averages,
        marker=dict(color=colors, line=dict(color="white", width=1)),
        text=[f"{v:.1f}" for v in averages],
        textposition="auto",
        hovertemplate="<b>%{x}</b><br>Average: %{y:.2f}/10<extra></extra>"
    ))
    
    # Update layout
    fig.update_layout(
        title="📊 Average Category Performance",
        yaxis_title="Average Score (0-10)",
        template="plotly_white",
        showlegend=False,
        height=400,
        hovermode="x unified",
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    return fig


# ==============================================================================
# INSIGHTS GENERATION
# ==============================================================================

def generate_chart_insights(df: pd.DataFrame) -> List[str]:
    """
    Generate insights from candidate data for chart interpretation.
    
    Args:
        df: Candidate dataframe
    
    Returns:
        List of insight strings
    """
    insights = []
    
    if len(df) == 0:
        return ["📊 No data available for analysis."]
    
    # Insight 1: Score distribution
    if "final_score" in df.columns:
        scores = df["final_score"]
        avg_score = scores.mean()
        min_score = scores.min()
        max_score = scores.max()
        
        if max_score - min_score > 30:
            insights.append(f"📊 Wide score variance detected ({min_score:.0f}-{max_score:.0f}). Clear candidate differentiation.")
        
        if avg_score > 75:
            insights.append("✅ Strong average score indicates competitive candidate pool.")
        elif avg_score < 55:
            insights.append("⚠️ Low average score. Consider expanding candidate search parameters.")
    
    # Insight 2: Component strengths
    components = ["skills_score", "experience_score", "education_score", "projects_score", "communication_score"]
    available_components = [c for c in components if c in df.columns]
    
    if len(available_components) > 0:
        component_labels = {
            "skills_score": "Skills",
            "experience_score": "Experience",
            "education_score": "Education",
            "projects_score": "Projects",
            "communication_score": "Communication"
        }
        
        averages = {component_labels[c]: df[c].mean() for c in available_components}
        
        # Find strongest component
        strongest = max(averages.items(), key=lambda x: x[1])
        if strongest[1] >= 8:
            insights.append(f"🌟 {strongest[0]} is a strong point (avg: {strongest[1]:.1f}/10) across candidates.")
        
        # Find weakest component
        weakest = min(averages.items(), key=lambda x: x[1])
        if weakest[1] <= 6:
            insights.append(f"📌 {weakest[0]} is the weakest component (avg: {weakest[1]:.1f}/10). Consider coaching or hiring for this skill.")
    
    # Insight 3: Status distribution
    if "final_score" in df.columns:
        shortlisted = len(df[df["final_score"] >= 70])
        total = len(df)
        
        pct = (shortlisted / total * 100) if total > 0 else 0
        
        if pct == 0:
            insights.append("❌ No candidates meet shortlist criteria (70+). Recommend expanding pool.")
        elif pct < 20:
            insights.append(f"⚠️ Only {pct:.0f}% of candidates are shortlisted. Limited selection available.")
        elif pct > 50:
            insights.append(f"✅ {pct:.0f}% shortlist rate indicates strong candidate pool.")
    
    # Insight 4: Top performer
    if len(df) > 0 and "final_score" in df.columns and "candidate_name" in df.columns:
        top = df.iloc[0]
        top_score = top.get("final_score", 0)
        top_name = top.get("candidate_name", "Top Candidate")
        
        if top_score >= 85:
            insights.append(f"⭐ {top_name} is exceptional (score: {top_score:.1f}). Highly recommended for immediate interview.")
    
    return insights


# ==============================================================================
# EMPTY STATE
# ==============================================================================

def show_empty_state() -> None:
    """Display empty state when no chart data available."""
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(
            """
            <div style="text-align: center; padding: 40px;">
                <h1 style="font-size: 48px; margin: 0;">📈</h1>
                <h2>No Analytics Data Yet</h2>
                <p style="font-size: 16px; color: #666;">
                    Run candidate analysis to view visual insights and analytics charts.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )


# ==============================================================================
# MAIN RENDERING FUNCTION
# ==============================================================================

def render_charts(candidates_df: Optional[pd.DataFrame]) -> None:
    """
    Main charts rendering function.
    
    Orchestrates all chart visualizations and insights.
    Called from streamlit_app.py.
    
    Args:
        candidates_df: DataFrame with candidate results or None if no data
    """
    # ========== HEADER ==========
    st.title("📊 Analytics & Insights")
    st.markdown("**Interactive visualizations of candidate analysis results**")
    
    # ========== EMPTY STATE CHECK ==========
    if candidates_df is None or len(candidates_df) == 0:
        show_empty_state()
        return
    
    # ========== CHART 1: SCORE DISTRIBUTION ==========
    st.markdown("---")
    st.subheader("Distribution Analysis")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        score_chart = create_score_distribution_chart(candidates_df)
        if score_chart:
            st.plotly_chart(score_chart, use_container_width=True)
    
    with col2:
        insight = show_score_distribution_insight(candidates_df)
        if insight:
            st.info(insight)
    
    # ========== CHART 2: LEADERBOARD ==========
    st.markdown("---")
    st.subheader("Candidate Rankings")
    
    leaderboard_chart = create_leaderboard_chart(candidates_df)
    if leaderboard_chart:
        st.plotly_chart(leaderboard_chart, use_container_width=True)
    
    # ========== CHART 3: COMPONENT BREAKDOWN & STATUS PIE ==========
    st.markdown("---")
    st.subheader("Candidate Comparison & Status")
    
    col1, col2 = st.columns(2)
    
    with col1:
        breakdown_chart = create_breakdown_chart(candidates_df)
        if breakdown_chart:
            st.plotly_chart(breakdown_chart, use_container_width=True)
    
    with col2:
        status_chart = create_status_pie_chart(candidates_df)
        if status_chart:
            st.plotly_chart(status_chart, use_container_width=True)
    
    # ========== CHART 4: TOP CANDIDATE RADAR ==========
    st.markdown("---")
    st.subheader("Top Candidate Profile")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        category_chart = create_category_performance_chart(candidates_df)
        if category_chart:
            st.plotly_chart(category_chart, use_container_width=True)
    
    with col2:
        radar_chart = create_radar_chart(candidates_df)
        if radar_chart:
            st.plotly_chart(radar_chart, use_container_width=True)
    
    # ========== INSIGHTS SECTION ==========
    st.markdown("---")
    st.subheader("💡 Visual Insights & Recommendations")
    
    insights = generate_chart_insights(candidates_df)
    for insight in insights:
        st.info(insight)
    
    # ========== FOOTER ==========
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #999; font-size: 12px; padding: 20px;">
            <p>Analytics Dashboard | AI HR Shortlisting System</p>
        </div>
        """,
        unsafe_allow_html=True
    )
