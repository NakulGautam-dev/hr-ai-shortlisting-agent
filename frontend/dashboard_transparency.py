"""
Dashboard Transparency Module - AI vs HR Override

Simple, clean integration of AI scores and HR overrides in the dashboard.
Shows:
- AI Score
- HR Override Score (if exists)
- Final Score (used for ranking)
- Override status badge

This module is designed to be simple and robust, avoiding complex logic.
"""

import streamlit as st
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from pathlib import Path
import sys

# report generator - use absolute import
try:
    import report_generator
except ImportError:
    # Fallback for when running in different context
    import importlib.util
    spec = importlib.util.spec_from_file_location("report_generator", Path(__file__).parent / "report_generator.py")
    report_generator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(report_generator)

# reportlab colors for batch PDF styling
from reportlab.lib import colors


# ==============================================================================
# DATA LOADING
# ==============================================================================

# ==============================================================================
# DATA LOADING
# ==============================================================================

def load_candidate_results() -> Optional[List[Dict[str, Any]]]:
    """Load latest candidate results from outputs folder."""
    try:
        outputs_dir = Path(__file__).parent.parent / "outputs"
        
        # Find latest shortlisting_results file
        result_files = list(outputs_dir.glob("shortlisting_results_*.json"))
        if not result_files:
            return None
        
        # Get latest file
        latest_file = max(result_files, key=lambda p: p.stat().st_mtime)
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
            return data.get("results", [])
    
    except Exception as e:
        st.error(f"Error loading results: {str(e)}")
        return None


def load_hr_overrides() -> Dict[str, Dict[str, Any]]:
    """Load all HR override files into a dict keyed by candidate name."""
    try:
        overrides = {}
        overrides_dir = Path(__file__).parent.parent / "outputs" / "hr_overrides"
        
        if not overrides_dir.exists():
            return overrides
        
        for override_file in overrides_dir.glob("*_overrides.json"):
            try:
                with open(override_file, 'r') as f:
                    data = json.load(f)
                    # Get candidate name from first item if it's a list
                    if isinstance(data, list) and len(data) > 0:
                        candidate_name = data[0].get("candidate_name")
                        if candidate_name:
                            # Use the most recent override (last in list)
                            overrides[candidate_name] = data[-1]
            except Exception as e:
                continue
        
        return overrides
    
    except Exception as e:
        return {}


# ==============================================================================
# MERGE AND CALCULATE
# ==============================================================================

def merge_ai_and_hr_data(candidates: List[Dict[str, Any]], overrides: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Merge AI results with HR overrides.
    
    For each candidate:
    - If override exists: use HR score for final ranking
    - If no override: use AI score
    """
    merged = []
    
    for candidate in candidates:
        name = candidate.get("candidate_name", "")
        ai_score = candidate.get("final_score", 0)
        
        # Check if override exists
        override = overrides.get(name)
        
        if override:
            # HR has reviewed this candidate
            hr_score = override.get("hr_override_score", ai_score)
            final_score = hr_score
            override_status = override.get("hr_status", "Modified")
            hr_status = override.get("hr_status", "Under Review")  # Final decision status
            hr_notes = override.get("hr_notes", "")
            reviewer = override.get("reviewer_name", "Unknown")
            delta = hr_score - ai_score
            is_overridden = True
        else:
            # No HR override, use AI score and AI recommendation
            hr_score = None
            final_score = ai_score
            override_status = "AI Only"
            hr_status = get_ai_recommendation(ai_score)  # Show AI recommendation instead of "Pending"
            hr_notes = ""
            reviewer = "N/A"
            delta = 0
            is_overridden = False
        
        merged.append({
            "candidate_name": name,
            "ai_score": ai_score,
            "hr_score": hr_score,
            "final_score": final_score,
            "delta": delta,
            "is_overridden": is_overridden,
            "override_status": override_status,
            "hr_status": hr_status,
            "hr_notes": hr_notes,
            "reviewer": reviewer,
            "rank": candidate.get("rank", "N/A"),
            "breakdown": candidate.get("breakdown", {}),
            "original_candidate": candidate
        })
    
    # Re-rank by final score
    merged = sorted(merged, key=lambda x: x["final_score"], reverse=True)
    for idx, candidate in enumerate(merged, 1):
        candidate["rank"] = idx
    
    return merged


# ==============================================================================
# DISPLAY FUNCTIONS
# ==============================================================================

def get_ai_recommendation(score: float) -> str:
    """Get AI recommendation based on score."""
    if score >= 85:
        return "Shortlisted"
    elif score >= 70:
        return "Strong Candidate"
    elif score >= 50:
        return "Review Later"
    else:
        return "Not Recommended"


def get_status_badge_color(override_status: str) -> str:
    """Get color for override status badge."""
    if override_status == "Final Approved":
        return "🟢"
    elif override_status == "Rejected":
        return "🔴"
    elif override_status == "AI Only":
        return "⚪"
    elif override_status == "Under Review":
        return "🟡"
    else:
        return "🔵"


def render_transparency_dashboard(candidates: List[Dict[str, Any]]) -> None:
    """
    Render the main transparency dashboard.
    
    Shows all candidates with AI vs HR scores and override status.
    """
    st.subheader("📊 Candidate Rankings - AI vs HR Override")
    st.markdown("---")
    # Batch export buttons
    st.subheader("📥 Batch Reports & Exports")
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        if st.button("📄 Generate Batch PDF Report"):
            try:
                batch_pdf = report_generator.REPORTS_DIR / "batch_shortlisting_report.pdf"
                # Create a simple batch PDF listing candidates and scores
                from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
                from reportlab.lib.styles import getSampleStyleSheet
                from reportlab.lib.pagesizes import A4
                styles = getSampleStyleSheet()
                doc = SimpleDocTemplate(str(batch_pdf), pagesize=A4)
                story = []
                story.append(Paragraph('Batch Shortlisting Report', styles['Heading1']))
                story.append(Spacer(1,12))
                rows = [['Rank','Candidate','Final Score','Decision Status']]
                for c in candidates:
                    rows.append([str(c.get('rank','')) , c.get('candidate_name',''), f"{c.get('final_score',0):.1f}", c.get('hr_status','')])
                table = Table(rows, colWidths=[40,220,80,120])
                table.setStyle(TableStyle([('GRID',(0,0),(-1,-1),0.5,colors.grey),('BACKGROUND',(0,0),(-1,0),colors.HexColor('#F3F4F6'))]))
                story.append(table)
                doc.build(story)
                with open(batch_pdf,'rb') as f:
                    st.download_button('📥 Download Batch PDF', data=f.read(), file_name=batch_pdf.name, mime='application/pdf')
            except Exception as e:
                st.error(f"Failed to generate batch PDF: {str(e)}")

    with col_b:
        if st.button('🌐 Generate Batch HTML Report'):
            try:
                batch_html = report_generator.REPORTS_DIR / 'batch_shortlisting_report.html'
                html = ['<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Batch Shortlisting Report</title></head><body>']
                html.append('<h1>Batch Shortlisting Report</h1>')
                html.append('<table border="1" cellpadding="6" cellspacing="0"><tr><th>Rank</th><th>Candidate</th><th>Final Score</th><th>Decision Status</th></tr>')
                for c in candidates:
                    html.append(f"<tr><td>{c.get('rank','')}</td><td>{c.get('candidate_name','')}</td><td>{c.get('final_score',0):.1f}</td><td>{c.get('hr_status','')}</td></tr>")
                html.append('</table></body></html>')
                with open(batch_html,'w',encoding='utf-8') as f:
                    f.write(''.join(html))
                with open(batch_html,'r',encoding='utf-8') as f:
                    st.download_button('📥 Download Batch HTML', data=f.read().encode('utf-8'), file_name=batch_html.name, mime='text/html')
            except Exception as e:
                st.error(f"Failed to generate batch HTML: {str(e)}")

    with col_c:
        if st.button('🔁 Export Batch JSON'):
            try:
                batch_json = report_generator.REPORTS_DIR / 'batch_shortlisting_report.json'
                with open(batch_json,'w',encoding='utf-8') as f:
                    json.dump(candidates, f, indent=2, default=str)
                with open(batch_json,'r',encoding='utf-8') as f:
                    st.download_button('📥 Download Batch JSON', data=f.read().encode('utf-8'), file_name=batch_json.name, mime='application/json')
            except Exception as e:
                st.error(f"Failed to export batch json: {str(e)}")

    
    if not candidates:
        st.info("No candidate data available")
        return
    
    # Summary metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    
    total_candidates = len(candidates)
    hr_modified = sum(1 for c in candidates if c["is_overridden"])
    avg_ai_score = sum(c["ai_score"] for c in candidates) / total_candidates if total_candidates > 0 else 0
    avg_final_score = sum(c["final_score"] for c in candidates) / total_candidates if total_candidates > 0 else 0
    override_percentage = (hr_modified / total_candidates * 100) if total_candidates > 0 else 0
    
    with col1:
        st.metric("Total Candidates", total_candidates)
    
    with col2:
        st.metric("HR Modified", hr_modified)
    
    with col3:
        st.metric("Avg AI Score", f"{avg_ai_score:.1f}")
    
    with col4:
        st.metric("Avg Final Score", f"{avg_final_score:.1f}")
    
    with col5:
        st.metric("Override %", f"{override_percentage:.0f}%")
    
    st.markdown("---")
    
    # Prepare data for table
    table_data = []
    for candidate in candidates:
        table_data.append({
            "Rank": f"#{candidate['rank']}",
            "Candidate": candidate["candidate_name"],
            "AI Score": f"{candidate['ai_score']:.1f}",
            "HR Score": f"{candidate['hr_score']:.1f}" if candidate['hr_score'] is not None else "—",
            "Final Score ⭐": f"{candidate['final_score']:.1f}",
            "Delta": f"{candidate['delta']:+.1f}" if candidate['delta'] != 0 else "—",
            "Final Decision": f"{get_status_badge_color(candidate['hr_status'])} {candidate['hr_status']}",
        })
    
    df = pd.DataFrame(table_data)
    
    # Add note explaining final score
    st.info("📌 **Ranking is based on FINAL SCORE** - If HR has reviewed and overridden, Final Score = HR Score. Otherwise, Final Score = AI Score")
    
    # Display table with custom styling
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Rank": st.column_config.TextColumn(width="small"),
            "Candidate": st.column_config.TextColumn(width="medium"),
            "AI Score": st.column_config.TextColumn(width="small"),
            "HR Score": st.column_config.TextColumn(width="small"),
            "Final Score ⭐": st.column_config.TextColumn(width="small"),
            "Delta": st.column_config.TextColumn(width="small"),
            "Final Decision": st.column_config.TextColumn(width="medium"),
        }
    )
    
    st.markdown("---")
    
    # Detailed view with expandable sections
    st.subheader("📋 Detailed Candidate Reviews")
    
    for candidate in candidates:
        with st.expander(
            f"**{candidate['candidate_name']}** — Final: {candidate['final_score']:.1f} | {get_status_badge_color(candidate['hr_status'])} {candidate['hr_status']}",
            expanded=False
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("AI Score", f"{candidate['ai_score']:.1f}")
            
            with col2:
                if candidate['hr_score'] is not None:
                    st.metric("HR Score ✓", f"{candidate['hr_score']:.1f}")
                else:
                    st.metric("HR Score", "—")
            
            with col3:
                # Final score in bold to highlight it's the one being used
                if candidate['is_overridden']:
                    st.metric("⭐ Final Score (HR)", f"{candidate['final_score']:.1f}", delta=f"{candidate['delta']:+.1f}")
                else:
                    st.metric("⭐ Final Score (AI)", f"{candidate['final_score']:.1f}")
            
            if candidate['is_overridden']:
                st.success(f"✅ **HR REVIEWED** - Decision: **{candidate['hr_status']}**")
                st.markdown("**Override Details:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Reviewer:** {candidate['reviewer']}")
                    st.write(f"**Decision:** {candidate['hr_status']}")
                with col2:
                    st.write(f"**Score Change:** {candidate['delta']:+.1f}")
                
                if candidate['hr_notes']:
                    st.markdown(f"**Reviewer Notes:** {candidate['hr_notes']}")
            else:
                st.info(f"⚪ **NOT REVIEWED** - AI Recommendation: **{candidate['hr_status']}** (Score: {candidate['ai_score']:.1f})")
            
            # Show skills from breakdown
            breakdown = candidate.get("breakdown", {})
            if breakdown:
                st.markdown("**Skills Analysis**")
                skills = breakdown.get("skills", {})
                if skills:
                    details = skills.get("details", {})
                    matched = details.get("matched_skill_pairs", [])
                    unmatched = details.get("unmatched_skills", [])
                    
                    if matched:
                        st.write(f"✅ Matched: {len(matched)} skills")
                    if unmatched:
                        st.write(f"❌ Missing: {len(unmatched)} skills")


# ==============================================================================
# FILTERS AND SORTING
# ==============================================================================

def apply_filters(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply sidebar filters to candidate list."""
    filtered = candidates.copy()
    
    st.sidebar.markdown("### 🔍 Filters")
    
    # Override filter
    override_filter = st.sidebar.radio(
        "Show:",
        ["All Candidates", "HR Modified Only", "AI Only"],
        key="override_filter"
    )
    
    if override_filter == "HR Modified Only":
        filtered = [c for c in filtered if c["is_overridden"]]
    elif override_filter == "AI Only":
        filtered = [c for c in filtered if not c["is_overridden"]]
    
    # Score range
    score_range = st.sidebar.slider(
        "Final Score Range:",
        0.0, 100.0, (0.0, 100.0),
        key="score_range"
    )
    filtered = [c for c in filtered if score_range[0] <= c["final_score"] <= score_range[1]]
    
    # Status filter
    statuses = list(set(c["hr_status"] for c in candidates))
    selected_statuses = st.sidebar.multiselect(
        "Decision Status:",
        statuses,
        default=statuses,
        key="status_filter"
    )
    filtered = [c for c in filtered if c["hr_status"] in selected_statuses]
    
    return filtered


# ==============================================================================
# MAIN RENDER FUNCTION
# ==============================================================================

def render_dashboard():
    """Main dashboard render function."""
    # Load data
    candidates = load_candidate_results()
    overrides = load_hr_overrides()
    
    if not candidates:
        st.warning("⚠️ No candidate results found. Please run the backend pipeline first.")
        return
    
    # Merge AI and HR data
    merged_candidates = merge_ai_and_hr_data(candidates, overrides)
    
    # Apply filters
    filtered_candidates = apply_filters(merged_candidates)
    
    # Render dashboard
    render_transparency_dashboard(filtered_candidates)
