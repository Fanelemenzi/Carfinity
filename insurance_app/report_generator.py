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
        
        # Assessment summary statistics
        story.extend(self._add_assessment_summary_stats())
        story.append(Spacer(1, 20))
        
        # Cost breakdown
        story.extend(self._add_cost_breakdown())
        story.append(Spacer(1, 20))
        
        # Recommendations and next steps
        story.extend(self._add_recommendations())
        story.append(PageBreak())
        
        # Section details
        story.extend(self._add_section_details())
        
        # Recommendations and next steps
        story.append(PageBreak())
        story.extend(self._add_recommendations())
        
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
            ['Vehicle:', f"{self.assessment.vehicle.manufacture_year} {self.assessment.vehicle.make} {self.assessment.vehicle.model}"],
            ['VIN:', self.assessment.vehicle.vin],
            ['Assessment Date:', self.assessment.assessment_date.strftime('%B %d, %Y')],
            ['Assessor:', self.assessment.assessor_name if self.assessment.assessor_name else (self.assessment.user.get_full_name() if self.assessment.user else 'N/A')],
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
        for the {self.assessment.vehicle.manufacture_year} {self.assessment.vehicle.make} {self.assessment.vehicle.model}.
        
        Total estimated repair cost: R{total_cost:,.2f}
        
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
            ['Year:', str(self.assessment.vehicle.manufacture_year)],
            ['VIN:', self.assessment.vehicle.vin],
            ['Mileage:', f"{self.assessment.vehicle.current_mileage:,} miles" if self.assessment.vehicle.current_mileage else 'N/A'],
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
            ['Assessor:', self.assessment.assessor_name if self.assessment.assessor_name else (self.assessment.user.get_full_name() if self.assessment.user else 'N/A')],
            ['Assessment Type:', getattr(self.assessment, 'assessment_type', 'Standard')],
            ['Location:', getattr(self.assessment, 'incident_location', 'N/A')],
        ]
        
        if hasattr(self.assessment, 'overall_notes') and self.assessment.overall_notes:
            assessment_data.append(['Notes:', self.assessment.overall_notes])
        
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
    
    def _add_assessment_summary_stats(self):
        """Add assessment summary statistics section"""
        elements = []
        
        elements.append(Paragraph("Assessment Summary Statistics", self.styles['SectionHeader']))
        
        # Get comprehensive section data for statistics
        sections = self._get_comprehensive_assessment_sections()
        
        # Calculate statistics
        total_sections = len(sections)
        sections_with_issues = len([s for s in sections if s['cost'] > 0])
        sections_no_issues = total_sections - sections_with_issues
        
        # Severity breakdown
        severity_counts = {}
        for section in sections:
            severity = section['severity']
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Create statistics table
        stats_data = [
            ['Metric', 'Value', 'Details'],
            ['Total Sections Assessed', str(total_sections), 'Complete vehicle assessment coverage'],
            ['Sections with Issues', str(sections_with_issues), f'{(sections_with_issues/total_sections*100):.1f}% of total sections'],
            ['Sections in Good Condition', str(sections_no_issues), f'{(sections_no_issues/total_sections*100):.1f}% of total sections'],
        ]
        
        # Add severity breakdown
        for severity, count in severity_counts.items():
            if count > 0 and severity != 'none':
                stats_data.append([
                    f'{severity.title()} Severity Issues',
                    str(count),
                    f'{(count/total_sections*100):.1f}% of sections'
                ])
        
        # Overall assessment status
        if sections_with_issues == 0:
            overall_status = "Excellent - No issues found"
        elif sections_with_issues <= total_sections * 0.2:
            overall_status = "Good - Minor issues only"
        elif sections_with_issues <= total_sections * 0.5:
            overall_status = "Fair - Moderate issues present"
        else:
            overall_status = "Poor - Multiple issues require attention"
        
        stats_data.append(['Overall Vehicle Condition', overall_status, 'Based on comprehensive assessment'])
        
        stats_table = Table(stats_data, colWidths=[2.2*inch, 1.3*inch, 2.5*inch])
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(stats_table)
        
        return elements
    
    def _add_recommendations(self):
        """Add recommendations and next steps section"""
        elements = []
        
        elements.append(Paragraph("Recommendations & Next Steps", self.styles['SectionHeader']))
        
        # Get comprehensive section data for recommendations
        sections = self._get_comprehensive_assessment_sections()
        
        # Generate recommendations based on assessment findings
        recommendations = []
        
        # Check for critical issues
        critical_sections = [s for s in sections if s['severity'] in ['major', 'severe']]
        if critical_sections:
            recommendations.append({
                'priority': 'CRITICAL',
                'text': f"Immediate attention required for {len(critical_sections)} critical section(s): {', '.join([s['name'] for s in critical_sections])}. These issues may affect vehicle safety and should be addressed before driving.",
                'color': colors.red
            })
        
        # Check for moderate issues
        moderate_sections = [s for s in sections if s['severity'] == 'moderate']
        if moderate_sections:
            recommendations.append({
                'priority': 'HIGH',
                'text': f"Schedule repairs for {len(moderate_sections)} section(s) with moderate damage within 30 days to prevent further deterioration.",
                'color': colors.orange
            })
        
        # Check for minor issues
        minor_sections = [s for s in sections if s['severity'] == 'minor']
        if minor_sections:
            recommendations.append({
                'priority': 'MEDIUM',
                'text': f"Address {len(minor_sections)} minor issue(s) during next scheduled maintenance to maintain vehicle condition.",
                'color': colors.blue
            })
        
        # Cost-based recommendations
        total_cost = sum(s['cost'] for s in sections)
        if total_cost > 50000:  # High cost threshold
            recommendations.append({
                'priority': 'FINANCIAL',
                'text': f"Total repair cost (R{total_cost:,.2f}) is significant. Consider obtaining multiple quotes and reviewing insurance coverage options.",
                'color': colors.purple
            })
        
        # Add general recommendations
        if not critical_sections and not moderate_sections:
            recommendations.append({
                'priority': 'MAINTENANCE',
                'text': "Vehicle is in good overall condition. Continue with regular maintenance schedule to preserve vehicle value and safety.",
                'color': colors.green
            })
        
        # Create recommendations list
        for i, rec in enumerate(recommendations, 1):
            priority_style = ParagraphStyle(
                name=f'Priority{i}',
                parent=self.styles['Normal'],
                fontSize=11,
                textColor=rec['color'],
                fontName='Helvetica-Bold',
                spaceBefore=8,
                spaceAfter=4
            )
            
            elements.append(Paragraph(f"{i}. [{rec['priority']}] {rec['text']}", priority_style))
        
        # Add next steps
        elements.append(Spacer(1, 15))
        elements.append(Paragraph("Recommended Next Steps:", self.styles['SubsectionHeader']))
        
        next_steps = [
            "1. Review this assessment with a qualified mechanic or body shop",
            "2. Obtain detailed repair quotes from certified service providers",
            "3. Contact your insurance provider to discuss coverage options",
            "4. Schedule repairs in order of priority (critical issues first)",
            "5. Keep this report for insurance and maintenance records"
        ]
        
        for step in next_steps:
            elements.append(Paragraph(step, self.styles['Normal']))
        
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
                table_data.append([category, f"R{cost:,.2f}"])
                total_cost += cost
            
            # Add total row
            table_data.append(['TOTAL', f"R{total_cost:,.2f}"])
            
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
        
        # Get all assessment sections with comprehensive details
        sections = self._get_comprehensive_assessment_sections()
        
        for section_info in sections:
            section_name = section_info['name']
            section_data = section_info['data']
            section_cost = section_info['cost']
            section_severity = section_info['severity']
            section_icon = section_info.get('icon', '')
            
            # Section header with cost and severity
            header_text = f"{section_icon} {section_name}"
            if section_cost > 0:
                header_text += f" - Estimated Cost: R{section_cost:,.2f}"
            if section_severity and section_severity != 'none':
                header_text += f" (Severity: {section_severity.title()})"
            
            elements.append(Paragraph(header_text, self.styles['SubsectionHeader']))
            
            if section_data and len(section_data) > 0:
                # Create detailed table for this section
                table_data = [['Component', 'Condition', 'Notes', 'Estimated Cost']]
                section_total = 0
                
                for item in section_data:
                    component = item.get('component', 'N/A')
                    condition = item.get('condition', 'N/A')
                    notes = item.get('notes', '-')
                    cost = item.get('cost', 0)
                    
                    # Truncate long notes for table display
                    if len(notes) > 50:
                        notes = notes[:47] + "..."
                    
                    cost_str = f"R{cost:,.2f}" if cost > 0 else "-"
                    table_data.append([component, condition.title(), notes, cost_str])
                    section_total += cost
                
                # Add section total if there are costs
                if section_total > 0:
                    table_data.append(['', '', 'Section Total:', f"R{section_total:,.2f}"])
                
                # Create and style the table
                section_table = Table(table_data, colWidths=[2*inch, 1.2*inch, 2.3*inch, 1*inch])
                section_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ]))
                
                # Highlight total row if present
                if section_total > 0:
                    section_table.setStyle(TableStyle([
                        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                        ('BACKGROUND', (0, -1), (-1, -1), colors.lightyellow),
                    ]))
                
                elements.append(section_table)
            else:
                elements.append(Paragraph("✓ No issues found in this section - All components in good condition.", self.styles['InfoText']))
            
            elements.append(Spacer(1, 15))
            
            # Add page break after every 2-3 sections to prevent overcrowding
            if len([s for s in sections if sections.index(section_info) <= sections.index(section_info)]) % 3 == 0:
                elements.append(PageBreak())
        
        return elements
    
    def _add_recommendations(self):
        """Add recommendations and next steps section"""
        elements = []
        
        elements.append(Paragraph("Recommendations & Next Steps", self.styles['SectionHeader']))
        
        # Get comprehensive section data for recommendations
        sections = self._get_comprehensive_assessment_sections()
        
        # Generate recommendations based on findings
        recommendations = []
        
        # Priority recommendations based on severity
        critical_sections = [s for s in sections if s['severity'] in ['severe', 'major']]
        moderate_sections = [s for s in sections if s['severity'] == 'moderate']
        minor_sections = [s for s in sections if s['severity'] == 'minor']
        
        if critical_sections:
            recommendations.append({
                'priority': 'CRITICAL',
                'title': 'Immediate Attention Required',
                'items': [f"• {s['name']}: Requires immediate professional repair due to {s['severity']} damage" for s in critical_sections],
                'timeline': 'Within 24-48 hours'
            })
        
        if moderate_sections:
            recommendations.append({
                'priority': 'HIGH',
                'title': 'Schedule Repairs Soon',
                'items': [f"• {s['name']}: Schedule repair within 1-2 weeks" for s in moderate_sections],
                'timeline': 'Within 1-2 weeks'
            })
        
        if minor_sections:
            recommendations.append({
                'priority': 'MEDIUM',
                'title': 'Plan for Future Maintenance',
                'items': [f"• {s['name']}: Address during next scheduled maintenance" for s in minor_sections],
                'timeline': 'Next maintenance cycle'
            })
        
        # Safety recommendations
        safety_issues = [s for s in sections if 'safety' in s['name'].lower() and s['cost'] > 0]
        if safety_issues:
            recommendations.insert(0, {
                'priority': 'SAFETY',
                'title': 'Safety System Concerns',
                'items': [f"• {s['name']}: Safety system requires immediate inspection" for s in safety_issues],
                'timeline': 'Before operating vehicle'
            })
        
        # Add general recommendations if no specific issues
        if not any(s['cost'] > 0 for s in sections):
            recommendations.append({
                'priority': 'MAINTENANCE',
                'title': 'Preventive Maintenance',
                'items': [
                    '• Continue regular maintenance schedule',
                    '• Monitor vehicle condition regularly',
                    '• Keep maintenance records updated'
                ],
                'timeline': 'Ongoing'
            })
        
        # Create recommendations content
        for rec in recommendations:
            # Priority header
            priority_colors = {
                'CRITICAL': colors.red,
                'SAFETY': colors.red,
                'HIGH': colors.orange,
                'MEDIUM': colors.blue,
                'MAINTENANCE': colors.green
            }
            
            priority_text = f"<b>{rec['priority']} PRIORITY: {rec['title']}</b>"
            elements.append(Paragraph(priority_text, self.styles['SubsectionHeader']))
            
            # Items
            for item in rec['items']:
                elements.append(Paragraph(item, self.styles['Normal']))
            
            # Timeline
            timeline_text = f"<i>Recommended Timeline: {rec['timeline']}</i>"
            elements.append(Paragraph(timeline_text, self.styles['InfoText']))
            elements.append(Spacer(1, 10))
        
        # Add cost summary and insurance information
        total_cost = sum(s['cost'] for s in sections)
        if total_cost > 0:
            elements.append(Paragraph("Financial Summary", self.styles['SubsectionHeader']))
            
            cost_summary = f"""
            Total Estimated Repair Cost: R{total_cost:,.2f}
            
            Insurance Considerations:
            • Obtain multiple repair quotes for comparison
            • Check policy coverage and deductibles
            • Consider authorized repair facilities
            • Keep all documentation for claims processing
            """
            
            elements.append(Paragraph(cost_summary, self.styles['Normal']))
        
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
        
        # First try to use the assessment's total if available
        if hasattr(self.assessment, 'estimated_repair_cost') and self.assessment.estimated_repair_cost:
            return Decimal(str(self.assessment.estimated_repair_cost))
        
        # Otherwise, calculate from sections
        cost_data = self._get_cost_breakdown_data()
        for cost in cost_data.values():
            total += cost
        
        return total
    
    def _get_cost_breakdown_data(self):
        """Get cost breakdown data from assessment sections"""
        cost_data = {}
        
        # Get comprehensive section data
        sections = self._get_comprehensive_assessment_sections()
        
        for section in sections:
            section_cost = section['cost']
            if section_cost > 0:
                cost_data[section['name']] = Decimal(str(section_cost))
        
        # Add additional costs if available from the main assessment
        if hasattr(self.assessment, 'estimated_repair_cost') and self.assessment.estimated_repair_cost:
            # If we have a total from the assessment that's higher than our calculated total,
            # add the difference as "Additional Costs"
            calculated_total = sum(cost_data.values())
            assessment_total = Decimal(str(self.assessment.estimated_repair_cost))
            
            if assessment_total > calculated_total:
                difference = assessment_total - calculated_total
                cost_data['Additional Costs'] = difference
        
        return cost_data
    
    def _get_comprehensive_assessment_sections(self):
        """Get comprehensive assessment section data with all details"""
        sections = []
        
        # Define all assessment sections with their details
        section_definitions = [
            {
                'name': 'Exterior Body Damage',
                'icon': '🚗',
                'attribute': 'exterior_damage',
                'cost_multiplier': 1500,  # Base cost multiplier for damage levels
            },
            {
                'name': 'Wheels & Tires',
                'icon': '🛞',
                'attribute': 'wheels_tires',
                'cost_multiplier': 800,
            },
            {
                'name': 'Interior Damage',
                'icon': '🪑',
                'attribute': 'interior_damage',
                'cost_multiplier': 1200,
            },
            {
                'name': 'Mechanical Systems',
                'icon': '⚙️',
                'attribute': 'mechanical_systems',
                'cost_multiplier': 2000,
            },
            {
                'name': 'Electrical Systems',
                'icon': '🔌',
                'attribute': 'electrical_systems',
                'cost_multiplier': 1000,
            },
            {
                'name': 'Safety Systems',
                'icon': '🛡️',
                'attribute': 'safety_systems',
                'cost_multiplier': 1800,
            },
            {
                'name': 'Frame & Structural',
                'icon': '🏗️',
                'attribute': 'frame_structural',
                'cost_multiplier': 3000,
            },
            {
                'name': 'Fluid Systems',
                'icon': '🛢️',
                'attribute': 'fluid_systems',
                'cost_multiplier': 600,
            },
            {
                'name': 'Documentation & Identification',
                'icon': '📋',
                'attribute': 'documentation',
                'cost_multiplier': 200,
            }
        ]
        
        for section_def in section_definitions:
            try:
                section_obj = getattr(self.assessment, section_def['attribute'], None)
                
                if section_obj:
                    section_data = self._format_comprehensive_section_data(
                        section_obj, 
                        section_def['cost_multiplier']
                    )
                    section_cost = self._calculate_section_cost(section_data)
                    section_severity = self._determine_section_severity(section_data)
                    
                    sections.append({
                        'name': section_def['name'],
                        'icon': section_def['icon'],
                        'data': section_data,
                        'cost': section_cost,
                        'severity': section_severity,
                    })
                else:
                    # Add placeholder for missing sections
                    sections.append({
                        'name': section_def['name'],
                        'icon': section_def['icon'],
                        'data': [],
                        'cost': 0,
                        'severity': 'none',
                    })
            except Exception as e:
                logger.warning(f"Error processing section {section_def['name']}: {str(e)}")
                # Add placeholder for error sections
                sections.append({
                    'name': section_def['name'],
                    'icon': section_def['icon'],
                    'data': [],
                    'cost': 0,
                    'severity': 'none',
                })
        
        return sections
    
    def _format_comprehensive_section_data(self, section, cost_multiplier):
        """Format section data comprehensively for detailed reporting"""
        data = []
        
        if not section:
            return data
        
        # Define cost mapping for different damage/condition levels
        cost_mapping = {
            'none': 0,
            'good': 0,
            'excellent': 0,
            'working': 0,
            'intact': 0,
            'light': cost_multiplier * 0.1,
            'minor': cost_multiplier * 0.15,
            'minor_damage': cost_multiplier * 0.2,
            'fair': cost_multiplier * 0.25,
            'moderate': cost_multiplier * 0.4,
            'moderate_damage': cost_multiplier * 0.5,
            'intermittent': cost_multiplier * 0.3,
            'poor': cost_multiplier * 0.6,
            'severe': cost_multiplier * 0.8,
            'severe_damage': cost_multiplier * 0.9,
            'major': cost_multiplier * 1.0,
            'destroyed': cost_multiplier * 1.2,
            'failed': cost_multiplier * 1.1,
            'not_working': cost_multiplier * 0.8,
            'compromised': cost_multiplier * 1.5,
            'deployed': cost_multiplier * 2.0,  # Airbags deployed
            'fault': cost_multiplier * 0.7,
        }
        
        # Get all fields from the section model
        for field in section._meta.fields:
            field_name = field.name
            
            # Skip system fields and notes fields (we'll handle notes separately)
            if field_name in ['id', 'assessment', 'created_at', 'updated_at'] or field_name.endswith('_notes'):
                continue
            
            field_value = getattr(section, field_name, None)
            notes_field_name = f"{field_name}_notes"
            notes_value = getattr(section, notes_field_name, '') if hasattr(section, notes_field_name) else ''
            
            # Only include items that have issues or are not in perfect condition
            if field_value and field_value not in ['good', 'none', 'excellent', 'working', 'intact']:
                component_name = field.verbose_name or field_name.replace('_', ' ').title()
                
                # Calculate estimated cost based on condition
                estimated_cost = cost_mapping.get(field_value, 0)
                
                # Adjust cost based on component importance
                if any(keyword in field_name.lower() for keyword in ['engine', 'transmission', 'brake', 'airbag', 'frame']):
                    estimated_cost *= 1.5  # Critical components cost more
                elif any(keyword in field_name.lower() for keyword in ['trim', 'molding', 'handle', 'cap']):
                    estimated_cost *= 0.5  # Cosmetic components cost less
                
                item = {
                    'component': component_name,
                    'condition': field_value,
                    'notes': notes_value or f"Requires attention - {field_value} condition",
                    'cost': round(estimated_cost, 2)
                }
                
                data.append(item)
        
        return data
    
    def _calculate_section_cost(self, section_data):
        """Calculate total cost for a section"""
        return sum(item.get('cost', 0) for item in section_data)
    
    def _determine_section_severity(self, section_data):
        """Determine overall severity for a section based on individual components"""
        if not section_data:
            return 'none'
        
        severity_levels = {
            'none': 0, 'good': 0, 'excellent': 0, 'working': 0, 'intact': 0,
            'light': 1, 'minor': 2, 'minor_damage': 2, 'fair': 3,
            'moderate': 4, 'moderate_damage': 4, 'intermittent': 3,
            'poor': 5, 'severe': 6, 'severe_damage': 6, 'major': 7,
            'destroyed': 8, 'failed': 7, 'not_working': 6,
            'compromised': 8, 'deployed': 9, 'fault': 5
        }
        
        max_severity = 0
        for item in section_data:
            condition = item.get('condition', 'none')
            severity_score = severity_levels.get(condition, 0)
            max_severity = max(max_severity, severity_score)
        
        # Convert back to severity names
        if max_severity == 0:
            return 'none'
        elif max_severity <= 2:
            return 'minor'
        elif max_severity <= 4:
            return 'moderate'
        elif max_severity <= 6:
            return 'major'
        else:
            return 'severe'
    
    def _format_section_data(self, section):
        """Format section data for display (legacy method for compatibility)"""
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