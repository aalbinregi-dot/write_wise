"""
PDF Report Generator using ReportLab
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                  TableStyle, HRFlowable, KeepTogether)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


BRAND_BLUE   = colors.HexColor('#1E40AF')
BRAND_INDIGO = colors.HexColor('#4F46E5')
BRAND_GRAY   = colors.HexColor('#374151')
BRAND_LIGHT  = colors.HexColor('#F3F4F6')
GREEN        = colors.HexColor('#059669')
RED          = colors.HexColor('#DC2626')
AMBER        = colors.HexColor('#D97706')
WHITE        = colors.white


def generate_essay_report(essay, result, student, recommendations=None) -> bytes:
    """
    Generate a comprehensive PDF report for an essay assessment.
    Returns bytes of the PDF.
    """
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story  = []

    # ── Custom Styles ──────────────────────────────────────────────────────
    h1 = ParagraphStyle('h1', parent=styles['Heading1'], fontSize=22, textColor=BRAND_BLUE,
                         spaceAfter=6, alignment=TA_CENTER)
    h2 = ParagraphStyle('h2', parent=styles['Heading2'], fontSize=14, textColor=BRAND_INDIGO,
                         spaceBefore=12, spaceAfter=4)
    body = ParagraphStyle('body', parent=styles['Normal'], fontSize=10, textColor=BRAND_GRAY,
                           leading=14, spaceAfter=4)
    small = ParagraphStyle('small', parent=styles['Normal'], fontSize=9, textColor=colors.gray)
    center = ParagraphStyle('center', parent=styles['Normal'], alignment=TA_CENTER, fontSize=9)

    # ── Header ─────────────────────────────────────────────────────────────
    story.append(Paragraph('WriteWise AI', h1))
    story.append(Paragraph('AI-Powered Writing Assessment Report', center))
    story.append(HRFlowable(width='100%', thickness=2, color=BRAND_BLUE))
    story.append(Spacer(1, 0.3*cm))

    # ── Student Info ────────────────────────────────────────────────────────
    story.append(Paragraph('Student Information', h2))
    info_data = [
        ['Name',        student.get_full_name() or student.username],
        ['Email',       student.email],
        ['Course',      student.course or '—'],
        ['Report Date', datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')],
        ['Essays Total', str(Essay.objects.filter(student=student, status='done').count())],
    ]
    info_table = Table(info_data, colWidths=[4*cm, 12*cm])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), BRAND_LIGHT),
        ('FONTNAME',   (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE',   (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [WHITE, BRAND_LIGHT]),
        ('BOX',        (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('INNERGRID',  (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('PADDING',    (0, 0), (-1, -1), 5),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Score ──────────────────────────────────────────────────────────────
    story.append(Paragraph('Overall Assessment', h2))
    score      = result.final_score or result.predicted_score or 0
    prev_score = result.previous_score
    score_change = f'+{score - prev_score:.2f}' if prev_score else '—'
    conf       = result.score_confidence or 0

    score_data = [
        ['Overall Score',    f'{score:.1f} / 6.0',    _score_label(score)],
        ['Previous Score',   f'{prev_score:.1f}' if prev_score else '—', ''],
        ['Change',           score_change,            ''],
        ['Confidence',       f'{conf * 100:.0f}%',    '⚠ Teacher review recommended' if conf < 0.65 else ''],
    ]
    score_table = Table(score_data, colWidths=[5*cm, 5*cm, 6*cm])
    score_table.setStyle(TableStyle([
        ('BACKGROUND',  (0, 0), (-1, 0), BRAND_BLUE),
        ('TEXTCOLOR',   (0, 0), (-1, 0), WHITE),
        ('FONTNAME',    (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',    (0, 0), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, BRAND_LIGHT]),
        ('BOX',         (0, 0), (-1, -1), 0.5, BRAND_BLUE),
        ('INNERGRID',   (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('PADDING',     (0, 0), (-1, -1), 6),
    ]))
    story.append(score_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Writing Analysis ───────────────────────────────────────────────────
    story.append(Paragraph('Writing Analysis', h2))
    wa = result.writing_analysis or {}
    analysis_data = [
        ['Metric',             'Value',                              'Status'],
        ['Word Count',         str(result.word_count or 0),          _word_status(result.word_count)],
        ['Grammar Errors',     str(result.grammar_error_count or 0), _count_status(result.grammar_error_count, 5, 2)],
        ['Spelling Errors',    str(result.spelling_error_count or 0),_count_status(result.spelling_error_count, 3, 1)],
        ['Vocabulary Quality', wa.get('vocab_quality', '—'),         ''],
        ['Readability',        wa.get('readability_label', '—'),     ''],
        ['Structure',          wa.get('structure_quality', '—'),     ''],
        ['Argument Dev.',      wa.get('argument_quality', '—'),      ''],
        ['Coherence',          f'{wa.get("coherence_score", 0):.1f}/5', ''],
    ]
    analysis_table = Table(analysis_data, colWidths=[5*cm, 4*cm, 7*cm])
    analysis_table.setStyle(TableStyle([
        ('BACKGROUND',     (0, 0), (-1, 0), BRAND_INDIGO),
        ('TEXTCOLOR',      (0, 0), (-1, 0), WHITE),
        ('FONTNAME',       (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',       (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [WHITE, BRAND_LIGHT]),
        ('BOX',            (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ('INNERGRID',      (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('PADDING',        (0, 0), (-1, -1), 5),
    ]))
    story.append(analysis_table)
    story.append(Spacer(1, 0.4*cm))

    # ── Problems ───────────────────────────────────────────────────────────
    story.append(Paragraph('Problems Detected', h2))
    problems = result.problems or []
    if problems:
        for p in problems[:6]:
            priority_color = {'HIGH': RED, 'MEDIUM': AMBER, 'LOW': GREEN}.get(p.get('priority', 'LOW'), BRAND_GRAY)
            story.append(Paragraph(
                f'<font color="#{priority_color.hexval()[1:]}"><b>[{p.get("priority","?")}]</b></font> '
                f'<b>{p.get("title", "")}</b> ({p.get("category", "")})',
                body
            ))
            story.append(Paragraph(p.get('description', ''), small))
            story.append(Spacer(1, 0.15*cm))
    else:
        story.append(Paragraph('No major problems detected. Well done!', body))

    story.append(Spacer(1, 0.3*cm))

    # ── Corrections ────────────────────────────────────────────────────────
    corrections = result.corrections or []
    if corrections:
        story.append(Paragraph('Sentence Corrections', h2))
        for c in corrections[:5]:
            story.append(Paragraph(f'<b>Type:</b> {c.get("error_type", "")}', small))
            story.append(Paragraph(f'<b>Original:</b> {c.get("original", "")}', body))
            story.append(Paragraph(f'<b>Corrected:</b> {c.get("correction", "")}', body))
            story.append(Paragraph(f'<i>{c.get("explanation", "")}</i>', small))
            story.append(HRFlowable(width='100%', thickness=0.5, color=colors.lightgrey))
        story.append(Spacer(1, 0.3*cm))

    # ── Recommendations ────────────────────────────────────────────────────
    if recommendations:
        story.append(Paragraph('Personalized Learning Recommendations', h2))
        for i, rec in enumerate(recommendations[:5], 1):
            story.append(Paragraph(
                f'{i}. <b>{rec.get("lesson", "")}</b> ({rec.get("category", "")}) '
                f'— Est. {rec.get("time_to_learn", 1)} hr(s)',
                body
            ))
        story.append(Spacer(1, 0.3*cm))

    # ── AI Disclaimer ──────────────────────────────────────────────────────
    story.append(HRFlowable(width='100%', thickness=1, color=BRAND_LIGHT))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        '⚠ AI-generated scores and feedback are automated estimates and should support, '
        'not replace, qualified human evaluation. Teacher review is always available.',
        small
    ))
    story.append(Paragraph('WriteWise AI — Write. Understand. Improve. Grow.', center))

    doc.build(story)
    return buffer.getvalue()


def _score_label(score):
    if score >= 5.5:  return 'Excellent'
    if score >= 4.5:  return 'Good'
    if score >= 3.5:  return 'Satisfactory'
    if score >= 2.5:  return 'Developing'
    return 'Beginning'


def _word_status(count):
    if not count:    return 'No text'
    if count < 100:  return 'Too short'
    if count < 300:  return 'Short'
    if count < 600:  return 'Standard'
    return 'Long'


def _count_status(count, high_threshold, medium_threshold):
    if not count or count == 0: return '✓ None'
    if count >= high_threshold: return '⚠ High'
    if count >= medium_threshold: return '△ Moderate'
    return '✓ Low'


# Import here to avoid circular import
from essays.models import Essay
