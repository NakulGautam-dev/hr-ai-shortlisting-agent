"""
Report Generator for HR AI Shortlisting System

Creates professional PDF and HTML candidate reports, batch reports, and JSON exports.

Dependencies: reportlab, jinja2, plotly, kaleido

Functions:
- generate_candidate_pdf(candidate, output_path)
- generate_candidate_html(candidate, output_path)
- export_json_report(candidate, output_path)
- create_score_chart(candidate, output_path)
- create_skill_match_table_pdf(canvas, x, y, candidate)

"""
from reportlab.lib.pagesizes import A4, landscape, portrait
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
import os
from pathlib import Path
import json
from datetime import datetime
import uuid
import io
import plotly.graph_objects as go


REPORTS_DIR = Path(__file__).parent.parent / "outputs" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def safe_filename(name: str) -> str:
    return "_".join(name.strip().split()).replace('/', '_')


def create_score_chart(candidate: dict, output_png: Path) -> None:
    """Create a horizontal bar chart for category breakdown and save as PNG."""
    breakdown = candidate.get("breakdown", {})
    categories = []
    values = []

    order = ["skills", "experience", "education", "projects", "communication"]
    for cat in order:
        data = breakdown.get(cat, {})
        score = data.get("score", 0) * 10  # convert to 0-100
        categories.append(cat.capitalize())
        values.append(score)

    fig = go.Figure(go.Bar(x=values, y=categories, orientation='h', marker_color=['#10B981' if v>=80 else '#3B82F6' if v>=60 else '#F59E0B' if v>=40 else '#EF4444' for v in values]))
    fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), xaxis=dict(range=[0,100], title='Score'), height=300)

    # write image using kaleido
    try:
        fig.write_image(str(output_png), engine='kaleido')
    except Exception:
        # fallback: save an empty PNG placeholder
        from reportlab.graphics import renderPM
        from reportlab.graphics.shapes import Drawing, Rect
        d = Drawing(400, 200)
        d.add(Rect(0,0,400,200, fillColor=colors.lightgrey))
        renderPM.drawToFile(d, str(output_png), fmt='PNG')


def generate_candidate_pdf(candidate: dict, output_path: Path) -> Path:
    """Generate a PDF report for a single candidate."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(str(output_path), pagesize=portrait(A4), rightMargin=20, leftMargin=20, topMargin=20, bottomMargin=20)
    styles = getSampleStyleSheet()
    story = []

    # Header
    title_style = ParagraphStyle('title', parent=styles['Heading1'], alignment=1, fontSize=18, spaceAfter=6)
    story.append(Paragraph('AI HR Resume Intelligence Report', title_style))
    meta = f"<b>Candidate:</b> {candidate.get('candidate_name', 'Unknown')}  &nbsp;&nbsp; <b>Generated:</b> {datetime.now().isoformat()}  &nbsp;&nbsp; <b>Report ID:</b> {uuid.uuid4()}"
    story.append(Paragraph(meta, styles['Normal']))
    story.append(Spacer(1, 8))

    # Executive summary table
    story.append(Paragraph('<b>Executive Summary</b>', styles['Heading2']))
    exec_data = [
        ['Final Score', f"{candidate.get('final_score', 0):.1f}/100"],
        ['AI Score', f"{candidate.get('ai_score', candidate.get('final_score',0)):.1f}/100"],
        ['HR Score', f"{candidate.get('hr_score', '—') if candidate.get('hr_score') is not None else '—'}"],
        ['Final Recommendation', candidate.get('recommendation', '—')],
        ['Hiring Status', candidate.get('status', '—')],
        ['Priority', candidate.get('priority', '—')]
    ]
    t = Table(exec_data, colWidths=[120*mm, 60*mm])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(1,0),colors.lightgrey),('BOX',(0,0),(-1,-1),0.5,colors.grey),('INNERGRID', (0,0), (-1,-1), 0.25, colors.grey)]))
    story.append(t)
    story.append(Spacer(1,12))

    # Score chart image
    chart_path = REPORTS_DIR / f"{safe_filename(candidate.get('candidate_name','candidate'))}_score.png"
    create_score_chart(candidate, chart_path)
    if chart_path.exists():
        story.append(Image(str(chart_path), width=160*mm, height=60*mm))
        story.append(Spacer(1,12))

    # Score breakdown
    story.append(Paragraph('<b>Score Breakdown</b>', styles['Heading3']))
    breakdown = candidate.get('breakdown', {})
    breakdown_rows = [['Category', 'Score (0-10)', 'Justification']]
    for cat in ['skills','experience','education','projects','communication']:
        data = breakdown.get(cat, {})
        breakdown_rows.append([cat.capitalize(), str(data.get('score','—')), data.get('justification','—')])

    bt = Table(breakdown_rows, colWidths=[50*mm, 30*mm, 100*mm])
    bt.setStyle(TableStyle([('BACKGROUND',(0,0),(2,0),colors.HexColor('#F3F4F6')),('BOX',(0,0),(-1,-1),0.5,colors.grey),('VALIGN',(0,0),(-1,-1),'TOP')]))
    story.append(bt)
    story.append(Spacer(1,12))

    # Skills analysis
    story.append(Paragraph('<b>Skills Match Analysis</b>', styles['Heading3']))
    skills = breakdown.get('skills',{}).get('details',{})
    matched = skills.get('matched_skill_pairs', [])
    unmatched = skills.get('unmatched_skills', [])

    story.append(Paragraph(f'<b>Matched Skills:</b> {len(matched)}', styles['Normal']))
    if matched:
        for m in matched[:50]:
            story.append(Paragraph(f'• {m}', styles['Normal']))

    story.append(Spacer(1,6))
    story.append(Paragraph(f'<b>Missing Skills:</b> {len(unmatched)}', styles['Normal']))
    if unmatched:
        for u in unmatched[:50]:
            story.append(Paragraph(f'• {u}', styles['Normal']))

    story.append(PageBreak())

    # AI analysis & experience
    story.append(Paragraph('<b>AI Analysis</b>', styles['Heading2']))
    ai_text = candidate.get('ai_analysis', '') or candidate.get('ai_justification', '') or 'AI analysis not available.'
    story.append(Paragraph(ai_text, styles['Normal']))
    story.append(Spacer(1,12))

    story.append(Paragraph('<b>Experience Summary</b>', styles['Heading3']))
    exp_entries = candidate.get('experience_entries', []) or candidate.get('experience', [])
    if exp_entries:
        for e in exp_entries[:50]:
            if isinstance(e, dict):
                title = e.get('title','')
                years = e.get('years','')
                org = e.get('organization','')
                story.append(Paragraph(f'• {title} at {org} — {years} years', styles['Normal']))
            else:
                story.append(Paragraph(f'• {str(e)}', styles['Normal']))
    else:
        story.append(Paragraph('No experience details available.', styles['Normal']))

    story.append(Spacer(1,12))

    # Education & certifications
    story.append(Paragraph('<b>Education & Certifications</b>', styles['Heading3']))
    edu = candidate.get('education', [])
    if edu:
        for e in edu[:20]:
            if isinstance(e, dict):
                story.append(Paragraph(f"• {e.get('degree','')} — {e.get('institution','')} ({e.get('year','')})", styles['Normal']))
            else:
                story.append(Paragraph(f'• {str(e)}', styles['Normal']))
    else:
        story.append(Paragraph('No education data available.', styles['Normal']))

    story.append(Spacer(1,12))

    # HR Review section
    story.append(Paragraph('<b>HR Review</b>', styles['Heading2']))
    if candidate.get('is_overridden'):
        story.append(Paragraph(f"HR Reviewer: {candidate.get('reviewer', 'Unknown')}", styles['Normal']))
        story.append(Paragraph(f"HR Score: {candidate.get('hr_score')}", styles['Normal']))
        if candidate.get('hr_notes'):
            story.append(Paragraph('<b>Reviewer Notes</b>', styles['Normal']))
            story.append(Paragraph(candidate.get('hr_notes'), styles['Normal']))
    else:
        story.append(Paragraph('Candidate evaluated using AI-only pipeline.', styles['Normal']))

    story.append(Spacer(1,12))

    # Final decision
    story.append(Paragraph('<b>Final Decision Summary</b>', styles['Heading2']))
    story.append(Paragraph(f"Decision: {candidate.get('final_recommendation', candidate.get('recommendation','—'))}", styles['Normal']))
    story.append(Paragraph(f"Confidence: {candidate.get('confidence', 'N/A')}", styles['Normal']))
    story.append(Spacer(1,12))

    # Audit trail
    story.append(Paragraph('<b>Audit Trail</b>', styles['Heading3']))
    audit = candidate.get('audit_trail', [])
    if audit:
        for a in audit[-20:]:
            ts = a.get('timestamp', '')
            action = a.get('action', '')
            story.append(Paragraph(f"• {ts} — {action} — {a.get('details',{})}", styles['Normal']))
    else:
        story.append(Paragraph('No audit events available for this candidate.', styles['Normal']))

    # Footer
    story.append(Spacer(1,24))
    story.append(Paragraph('Generated by AI HR Shortlisting System. AI recommendations are assistive and should support, not replace, human judgment.', ParagraphStyle('footer', parent=styles['Normal'], fontSize=8, alignment=1)))

    # Build PDF
    doc.build(story)

    return output_path


def generate_candidate_html(candidate: dict, output_path: Path) -> Path:
    """Generate a simple responsive HTML report for a candidate."""
    html = []
    html.append('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Candidate Report</title>')
    # Inline minimal styles
    html.append('<style>body{font-family:Arial,Helvetica,sans-serif;color:#111;padding:20px;max-width:900px;margin:auto}h1,h2{color:#0f172a} .card{border-left:4px solid #3B82F6;padding:12px;margin:10px 0;background:#f8fafc} table{width:100%;border-collapse:collapse} td,th{padding:8px;border:1px solid #e6e6e6}</style></head><body>')
    html.append(f'<h1>AI HR Resume Intelligence Report</h1><p><strong>Candidate:</strong> {candidate.get("candidate_name","Unknown")} &nbsp; <strong>Generated:</strong> {datetime.now().isoformat()}</p>')

    html.append('<h2>Executive Summary</h2>')
    html.append('<div class="card">')
    html.append(f'<p><strong>Final Score:</strong> {candidate.get("final_score",0):.1f}/100</p>')
    html.append(f'<p><strong>AI Score:</strong> {candidate.get("ai_score",0):.1f}/100</p>')
    html.append(f'<p><strong>HR Score:</strong> {candidate.get("hr_score","—")}</p>')
    html.append('</div>')

    html.append('<h2>Score Breakdown</h2>')
    html.append('<table><tr><th>Category</th><th>Score</th><th>Justification</th></tr>')
    for cat in ['skills','experience','education','projects','communication']:
        data = candidate.get('breakdown', {}).get(cat, {})
        html.append(f"<tr><td>{cat.capitalize()}</td><td>{data.get('score','—')}</td><td>{data.get('justification','—')}</td></tr>")
    html.append('</table>')

    # Skills
    html.append('<h2>Skills Match Analysis</h2>')
    skills = candidate.get('breakdown',{}).get('skills',{}).get('details',{})
    matched = skills.get('matched_skill_pairs', [])
    unmatched = skills.get('unmatched_skills', [])
    html.append(f'<p><strong>Matched:</strong> {len(matched)} &nbsp; <strong>Missing:</strong> {len(unmatched)}</p>')
    if matched:
        html.append('<h4>Matched Skills</h4><ul>')
        for m in matched[:50]:
            html.append(f'<li>{m}</li>')
        html.append('</ul>')
    if unmatched:
        html.append('<h4>Missing Skills</h4><ul>')
        for u in unmatched[:50]:
            html.append(f'<li>{u}</li>')
        html.append('</ul>')

    # HR review
    html.append('<h2>HR Review</h2>')
    if candidate.get('is_overridden'):
        html.append(f"<p><strong>Reviewer:</strong> {candidate.get('reviewer','Unknown')}</p>")
        html.append(f"<p><strong>HR Score:</strong> {candidate.get('hr_score')}</p>")
        if candidate.get('hr_notes'):
            html.append(f"<p><strong>Notes:</strong> {candidate.get('hr_notes')}</p>")
    else:
        html.append('<p>Candidate evaluated using AI-only pipeline.</p>')

    html.append('<footer style="margin-top:30px;font-size:12px;color:#6b7280">Generated by AI HR Shortlisting System. AI recommendations are assistive and should support, not replace, human judgment.</footer>')
    html.append('</body></html>')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(''.join(html))

    return output_path


def export_json_report(candidate: dict, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(candidate, f, indent=2, default=str)
    return output_path
