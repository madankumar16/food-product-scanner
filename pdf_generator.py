"""
PDF report generation module
"""

import logging
from typing import List
from io import BytesIO

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logging.warning("reportlab not available. PDF generation will be limited.")

from food_scanner import Dashboard, ClassifiedIngredient, HealthRisk, SafetyColor

logger = logging.getLogger(__name__)


class PDFGenerator:
    """Generate PDF reports"""
    
    def __init__(self):
        """Initialize PDF generator"""
        if not REPORTLAB_AVAILABLE:
            logger.warning("reportlab not installed. Install with: pip install reportlab")
    
    def generate(self, dashboard: Dashboard, format: str = "A4") -> bytes:
        """
        Generate PDF report from dashboard
        
        Args:
            dashboard: Dashboard data structure
            format: Page format (default: A4)
            
        Returns:
            PDF content as bytes
        """
        if not REPORTLAB_AVAILABLE:
            logger.warning("PDF generation not available. Returning placeholder.")
            return b"PDF_CONTENT_PLACEHOLDER"
        
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            story = []
            styles = getSampleStyleSheet()
            
            # Title
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                textColor=colors.HexColor('#2c3e50'),
                spaceAfter=30,
                alignment=1  # Center
            )
            story.append(Paragraph("Food Product Analysis Report", title_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Product Information
            story.append(Paragraph("Product Information", styles['Heading2']))
            product_info = [
                ["Product Name:", dashboard.product_name],
                ["Brand:", dashboard.brand],
                ["Vegetarian Status:", dashboard.veg_status.value],
                ["Safety Rating:", f"{dashboard.safety_color.value} ({dashboard.safety_score:.1f}/100)"]
            ]
            
            product_table = Table(product_info, colWidths=[2*inch, 4*inch])
            product_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#ecf0f1')),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey)
            ]))
            story.append(product_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Ingredients
            story.append(Paragraph("Ingredients Analysis", styles['Heading2']))
            ingredient_data = [["Ingredient", "Category"]]
            for ing in dashboard.ingredients:
                ingredient_data.append([ing.name, ing.category.value])
            
            ingredient_table = Table(ingredient_data, colWidths=[4*inch, 2*inch])
            ingredient_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')])
            ]))
            story.append(ingredient_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Health Warnings
            if dashboard.health_warnings:
                story.append(Paragraph("Health Warnings", styles['Heading2']))
                warning_data = [["Ingredient", "Health Conditions"]]
                for warning in dashboard.health_warnings:
                    conditions = ", ".join(warning.conditions)
                    warning_data.append([warning.ingredient, conditions])
                
                warning_table = Table(warning_data, colWidths=[2.5*inch, 3.5*inch])
                warning_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e74c3c')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#ffe6e6')])
                ]))
                story.append(warning_table)
                story.append(Spacer(1, 0.3*inch))
            
            # Exceeded Limits
            if dashboard.exceeded_limits:
                story.append(Paragraph("Safety Thresholds Exceeded", styles['Heading2']))
                limit_text = ", ".join(dashboard.exceeded_limits)
                story.append(Paragraph(f"<b>Warning:</b> The following ingredients exceed safe limits: {limit_text}", 
                                     styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
            
            # Build PDF
            doc.build(story)
            pdf_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"PDF generated successfully ({len(pdf_bytes)} bytes)")
            return pdf_bytes
            
        except Exception as e:
            logger.error(f"Error generating PDF: {e}")
            return b"PDF_ERROR_PLACEHOLDER"

