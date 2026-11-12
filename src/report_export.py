import os
from io import BytesIO
from datetime import datetime
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, HRFlowable
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from src.utils import format_inr

FONT_REGULAR = 'Helvetica'
FONT_BOLD = 'Helvetica-Bold'

_arial = r'C:\Windows\Fonts\arial.ttf'
_arial_bold = r'C:\Windows\Fonts\arialbd.ttf'
if os.path.exists(_arial) and os.path.exists(_arial_bold):
    pdfmetrics.registerFont(TTFont('Arial', _arial))
    pdfmetrics.registerFont(TTFont('Arial-Bold', _arial_bold))
    FONT_REGULAR = 'Arial'
    FONT_BOLD = 'Arial-Bold'



def generate_pdf_report(report):
    """Builds a shop-owner-facing PDF summary of the current report."""
    output = BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter, topMargin=0.75 * inch,
                             bottomMargin=0.75 * inch, leftMargin=0.85 * inch, rightMargin=0.85 * inch)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('T', parent=styles['Title'], fontSize=20, fontName=FONT_BOLD)
    meta_style = ParagraphStyle('M', parent=styles['Normal'], fontSize=9, textColor=colors.grey, fontName=FONT_REGULAR)
    heading_style = ParagraphStyle('H', parent=styles['Heading2'], spaceBefore=14, spaceAfter=6, fontName=FONT_BOLD)
    body_style = ParagraphStyle('B', parent=styles['Normal'], fontName=FONT_REGULAR)
    story = [
        Paragraph("BizPal Business Report", title_style),
        Paragraph(f"Generated on {datetime.now().strftime('%d %B %Y, %I:%M %p')}", meta_style),
        HRFlowable(width="100%", thickness=0.75, color=colors.HexColor('#1C2541')),
        Paragraph("Overview", heading_style),
    ]

    overview_data = [
        ["Total Revenue (2013-2017)", format_inr(report['kpi_summary']['total_revenue'])],
        ["Total Profit (2013-2017)", format_inr(report['kpi_summary']['total_profit'])],
        ["Top Product", f"Item {report['top_revenue_items'][0]}"],
    ]
    t = Table(overview_data, colWidths=[3 * inch, 3 * inch])
    t.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT_REGULAR),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DDDFD9')),
    ]))
    story.append(t)

    story.append(Paragraph("Items Needing Reorder", heading_style))
    high_priority = [r for r in report['recommendations'] if r['priority'] == 'High']
    for r in (high_priority or [{'message': 'No items currently need reordering.'}]):
        story.append(Paragraph(f"&bull;&nbsp;{r['message']}", body_style))

    story.append(Paragraph("All Recommendations", heading_style))
    for r in report['recommendations']:
        story.append(Paragraph(f"[{r['priority']}] {r['message']}", body_style))

    doc.build(story)
    return output.getvalue()


def generate_excel_report(report):
    """Builds a multi-sheet Excel workbook: Overview, Inventory, Recommendations."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        pd.DataFrame([{
            'Total Revenue': report['kpi_summary']['total_revenue'],
            'Total Profit': report['kpi_summary']['total_profit'],
            'Top Product': report['top_revenue_items'][0],
        }]).to_excel(writer, sheet_name='Overview', index=False)

        report['inventory'][['item', 'current_stock', 'days_of_supply_forecasted', 'status_forecasted']].rename(
            columns={'item': 'Item', 'current_stock': 'Stock on Hand',
                     'days_of_supply_forecasted': 'Days of Supply', 'status_forecasted': 'Status'}
        ).to_excel(writer, sheet_name='Inventory', index=False)

        pd.DataFrame(report['recommendations']).to_excel(writer, sheet_name='Recommendations', index=False)

    return output.getvalue()