"""
PDF Report Generation System for Insurance Vehicle Assessments
"""
import os
import io
from datetime import datetime
from decimal import Decimal
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import render_to_string
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.platypus.flowables import HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF
import logging

logger = logging.getLogger(__name__)

class AssessmentReportGenerator:
    """Generate comprehensive PDF reports for vehicle assessments"""
    
    def __init__(self, assessment):
        self.assessment = assessment
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles for the report"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1f2937')
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=colors.HexColor('#374151'),
            borderWidth=1,
            borderColor=colors.HexColor('#e5e7eb'),
            borderPadding=8
        ))
        
        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=colors.HexColor('#4b5563')
        ))
        
        # Info text style
        self.styles.add(ParagraphStyle(
            name='InfoText',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#6b7280'),
            alignment=TA_LEFT
        ))
        
        # Highlight style
        self.styles.add(ParagraphStyle(
            name='Highlight',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#dc2626'),
            fontName='Helvetica-Bold'
        ))
    
    def generate_report(self, report_type='detailed'):
        """
        Generate PDF report based on type
        
        Args:
            report_type (str): Type of report - 'summary', 'detailed', or 'photos_only'
        
        Returns:
            HttpResponse: PDF response
        """
        try:
            # Create PDF buffer
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build story based on report type
            story = []
            
            if report_type == 'summary':
                story = self._build_summary_report()
            elif report_type == 'photos_only':
                story = self._build_photos_report()
            else:  # detailed
                story = self._build_detailed_report()
            
            # Build PDF
            doc.build(story)
            
            # Get PDF data
            pdf_data = buffer.getvalue()
            buffer.close()
            
            # Create response
            response = HttpResponse(pdf_data, content_type='application/pdf')
            filename = f"assessment_report_{self.assessment.id}_{report_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating PDF report: {str(e)}")
            raise
    
    def _build_detailed_report(self):
        """Build detailed assessment report"""
        story = []
        
        # Title page
        story.extend(self._add_title_page())
        story.append(PageBreak())
        
        # Executive summary
        story.extend(self._add_executive_summary())
        story.append(Spacer(1, 20))
        
        # Vehicle information
        story.extend(self._add_vehicle_information())
        story.append(Spacer(1, 20))
        
        # Assessment details
        story.extend(self._add_assessment_details())
        story.append(Spacer(1, 20))
        
        # Cost breakdown
        story.extend(self._add_cost_breakdown())
        story.append(PageBreak())
        
        # Section details
        story.extend(self._add_section_details())
        
        # Photos
        if hasattr(self.assessment, 'photos') and self.assessment.photos.exists():
            story.append(PageBreak())
            story.extend(self._add_photo_section())
        
        return story
    
    def _build_summary_report(self):
        """Build summary assessment report"""
        story = []
        
        # Title
        story.extend(self._add_title_page())
        story.append(Spacer(1, 30))
        
        # Executive summary
        story.extend(self._add_executive_summary())
        story.append(Spacer(1, 20))
        
        # Vehicle information
        story.extend(self._add_vehicle_information())
        story.append(Spacer(1, 20))
        
        # Cost breakdown
        story.extend(self._add_cost_breakdown())
        
        return story
    
    def _build_photos_report(self):
        """Build photos-only report"""
        story = []
        
        # Title
        story.append(Paragraph("Vehicle Assessment Photos", self.styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Basic info
        story.extend(self._add_vehicle_information())
        story.append(Spacer(1, 30))
        
        # Photos
        story.extend(self._add_photo_section())
        
        return story
    
    def _add_title_page(self):
        """Add title page elements"""
        elements = []
        
        # Main title
        elements.append(Paragraph("Vehicle Assessment Report", self.styles['CustomTitle']))
        elements.append(Spacer(1, 30))
        
        # Assessment info table
        assessment_data = [
            ['Assessment ID:', str(self.assessment.id)],
            ['Vehicle:', f"{self.assessment.vehicle.year} {self.assessment.vehicle.make} {self.assessment.vehicle.model}"],
            ['VIN:', self.assessment.vehicle.vin],
            ['Assessment Date:', self.assessment.assessment_date.strftime('%B %d, %Y')],
            ['Assessor:', self.assessment.assessor.get_full_name() if self.assessment.assessor else 'N/A'],
            ['Report Generated:', datetime.now().strftime('%B %d, %Y at %I:%M %p')]
        ]
        
        assessment_table = Table(assessment_data, colWidths=[2*inch, 4*inch])
        assessment_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(assessment_table)
        
        return elements
    
    def _add_executive_summary(self):
        """Add executive summary section"""
        elements = []
        
        elements.append(Paragraph("Executive Summary", self.styles['SectionHeader']))
        
        # Calculate totals
        total_cost = self._calculate_total_cost()
        
        summary_text = f"""
        This comprehensive vehicle assessment report details the condition and estimated repair costs 
        for the {self.assessment.vehicle.year} {self.assessment.vehicle.make} {self.assessment.vehicle.model}.
        
        Total estimated repair cost: ${total_cost:,.2f}
        
        Assessment status: {self.assessment.get_status_display() if hasattr(self.assessment, 'get_status_display') else 'Completed'}
        """
        
        elements.append(Paragraph(summary_text, self.styles['Normal']))
        
        return elements
    
    def _add_vehicle_information(self):
        """Add vehicle information section"""
        elements = []
        
        elements.append(Paragraph("Vehicle Information", self.styles['SectionHeader']))
        
        vehicle_data = [
            ['Make:', self.assessment.vehicle.make],
            ['Model:', self.assessment.vehicle.model],
            ['Year:', str(self.assessment.vehicle.year)],
            ['VIN:', self.assessment.vehicle.vin],
            ['Mileage:', f"{self.assessment.vehicle.mileage:,} miles" if self.assessment.vehicle.mileage else 'N/A'],
            ['Color:', getattr(self.assessment.vehicle, 'color', 'N/A')],
        ]
        
        vehicle_table = Table(vehicle_data, colWidths=[1.5*inch, 4*inch])
        vehicle_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        ]))
        
        elements.append(vehicle_table)
        
        return elements
    
    def _add_assessment_details(self):
        """Add assessment details section"""
        elements = []
        
        elements.append(Paragraph("Assessment Details", self.styles['SectionHeader']))
        
        assessment_data = [
            ['Assessment Date:', self.assessment.assessment_date.strftime('%B %d, %Y')],
            ['Assessor:', self.assessment.assessor.get_full_name() if self.assessment.assessor else 'N/A'],
            ['Assessment Type:', getattr(self.assessment, 'assessment_type', 'Standard')],
            ['Location:', getattr(self.assessment, 'location', 'N/A')],
        ]
        
        if hasattr(self.assessment, 'notes') and self.assessment.notes:
            assessment_data.append(['Notes:', self.assessment.notes])
        
        assessment_table = Table(assessment_data, colWidths=[1.5*inch, 4*inch])
        assessment_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(assessment_table)
        
        return elements
    
    def _add_cost_breakdown(self):
        """Add cost breakdown section"""
        elements = []
        
        elements.append(Paragraph("Cost Breakdown", self.styles['SectionHeader']))
        
        # Get cost data from related assessment sections
        cost_data = self._get_cost_breakdown_data()
        
        if cost_data:
            # Create cost table
            table_data = [['Category', 'Estimated Cost']]
            total_cost = Decimal('0.00')
            
            for category, cost in cost_data.items():
                table_data.append([category, f"${cost:,.2f}"])
                total_cost += cost
            
            # Add total row
            table_data.append(['TOTAL', f"${total_cost:,.2f}"])
            
            cost_table = Table(table_data, colWidths=[3*inch, 2*inch])
            cost_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ]))
            
            elements.append(cost_table)
        else:
            elements.append(Paragraph("No cost breakdown data available.", self.styles['InfoText']))
        
        return elements
    
    def _add_section_details(self):
        """Add detailed section information"""
        elements = []
        
        elements.append(Paragraph("Detailed Assessment Sections", self.styles['SectionHeader']))
        
        # Get all assessment sections
        sections = self._get_assessment_sections()
        
        for section_name, section_data in sections.items():
            elements.append(Paragraph(section_name, self.styles['SubsectionHeader']))
            
            if section_data:
                for item in section_data:
                    item_text = f"• {item.get('description', 'N/A')}"
                    if item.get('cost'):
                        item_text += f" - ${item['cost']:,.2f}"
                    elements.append(Paragraph(item_text, self.styles['Normal']))
            else:
                elements.append(Paragraph("No issues found in this section.", self.styles['InfoText']))
            
            elements.append(Spacer(1, 12))
        
        return elements
    
    def _add_photo_section(self):
        """Add photos section"""
        elements = []
        
        elements.append(Paragraph("Assessment Photos", self.styles['SectionHeader']))
        
        if hasattr(self.assessment, 'photos') and self.assessment.photos.exists():
            photos = self.assessment.photos.all()
            
            for i, photo in enumerate(photos):
                try:
                    # Add photo if file exists
                    if photo.image and os.path.exists(photo.image.path):
                        img = Image(photo.image.path, width=4*inch, height=3*inch)
                        elements.append(img)
                        
                        # Add photo caption
                        caption = f"Photo {i+1}"
                        if photo.description:
                            caption += f": {photo.description}"
                        elements.append(Paragraph(caption, self.styles['InfoText']))
                        elements.append(Spacer(1, 12))
                        
                        # Add page break every 2 photos
                        if (i + 1) % 2 == 0 and i < len(photos) - 1:
                            elements.append(PageBreak())
                            
                except Exception as e:
                    logger.warning(f"Could not add photo {photo.id} to report: {str(e)}")
                    continue
        else:
            elements.append(Paragraph("No photos available for this assessment.", self.styles['InfoText']))
        
        return elements
    
    def _calculate_total_cost(self):
        """Calculate total estimated cost"""
        total = Decimal('0.00')
        
        # Add costs from different assessment sections
        cost_data = self._get_cost_breakdown_data()
        for cost in cost_data.values():
            total += cost
        
        return total
    
    def _get_cost_breakdown_data(self):
        """Get cost breakdown data from assessment sections"""
        cost_data = {}
        
        # Check for exterior damage costs
        if hasattr(self.assessment, 'exterior_damage'):
            exterior_cost = getattr(self.assessment.exterior_damage, 'estimated_cost', 0) or 0
            if exterior_cost > 0:
                cost_data['Exterior Body Damage'] = Decimal(str(exterior_cost))
        
        # Check for mechanical costs
        if hasattr(self.assessment, 'mechanical_systems'):
            mechanical_cost = getattr(self.assessment.mechanical_systems, 'estimated_cost', 0) or 0
            if mechanical_cost > 0:
                cost_data['Mechanical Systems'] = Decimal(str(mechanical_cost))
        
        # Check for interior costs
        if hasattr(self.assessment, 'interior_condition'):
            interior_cost = getattr(self.assessment.interior_condition, 'estimated_cost', 0) or 0
            if interior_cost > 0:
                cost_data['Interior Condition'] = Decimal(str(interior_cost))
        
        # Check for electrical costs
        if hasattr(self.assessment, 'electrical_systems'):
            electrical_cost = getattr(self.assessment.electrical_systems, 'estimated_cost', 0) or 0
            if electrical_cost > 0:
                cost_data['Electrical Systems'] = Decimal(str(electrical_cost))
        
        # Check for wheels/tires costs
        if hasattr(self.assessment, 'wheels_tires'):
            wheels_cost = getattr(self.assessment.wheels_tires, 'estimated_cost', 0) or 0
            if wheels_cost > 0:
                cost_data['Wheels & Tires'] = Decimal(str(wheels_cost))
        
        return cost_data
    
    def _get_assessment_sections(self):
        """Get detailed assessment section data"""
        sections = {}
        
        # Exterior damage
        if hasattr(self.assessment, 'exterior_damage'):
            exterior = self.assessment.exterior_damage
            sections['Exterior Body Damage'] = self._format_section_data(exterior)
        
        # Mechanical systems
        if hasattr(self.assessment, 'mechanical_systems'):
            mechanical = self.assessment.mechanical_systems
            sections['Mechanical Systems'] = self._format_section_data(mechanical)
        
        # Interior condition
        if hasattr(self.assessment, 'interior_condition'):
            interior = self.assessment.interior_condition
            sections['Interior Condition'] = self._format_section_data(interior)
        
        # Electrical systems
        if hasattr(self.assessment, 'electrical_systems'):
            electrical = self.assessment.electrical_systems
            sections['Electrical Systems'] = self._format_section_data(electrical)
        
        # Wheels and tires
        if hasattr(self.assessment, 'wheels_tires'):
            wheels = self.assessment.wheels_tires
            sections['Wheels & Tires'] = self._format_section_data(wheels)
        
        return sections
    
    def _format_section_data(self, section):
        """Format section data for display"""
        data = []
        
        if not section:
            return data
        
        # Get all fields from the section model
        for field in section._meta.fields:
            field_name = field.name
            if field_name in ['id', 'assessment', 'created_at', 'updated_at']:
                continue
            
            field_value = getattr(section, field_name, None)
            if field_value and field_value != 'good' and field_value != 'none':
                description = field.verbose_name or field_name.replace('_', ' ').title()
                
                item = {'description': f"{description}: {field_value}"}
                
                # Add cost if it's a cost field
                if 'cost' in field_name.lower() and isinstance(field_value, (int, float, Decimal)):
                    item['cost'] = Decimal(str(field_value))
                
                data.append(item)
        
        return data


def generate_assessment_report(assessment, report_type='detailed'):
    """
    Convenience function to generate assessment report
    
    Args:
        assessment: VehicleAssessment instance
        report_type (str): Type of report - 'summary', 'detailed', or 'photos_only'
    
    Returns:
        HttpResponse: PDF response
    """
    generator = AssessmentReportGenerator(assessment)
    return generator.generate_report(report_type)