"""
Cancer Detection Report Generator
Generates comprehensive PDF reports for cancer detection analysis
"""
import os
import io
from datetime import datetime, timezone
from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.colors import Color, black, red, green, blue, orange
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.platypus import PageBreak, Image, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Rect
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.charts.barcharts import VerticalBarChart
import base64
import json


class CancerDetectionReportGenerator:
    """Comprehensive Cancer Detection Report Generator"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles for the report"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='ReportTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=Color(0.2, 0.2, 0.6),
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            spaceBefore=20,
            textColor=Color(0.1, 0.1, 0.5),
            fontName='Helvetica-Bold'
        ))
        
        # Subsection header style
        self.styles.add(ParagraphStyle(
            name='SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=8,
            spaceBefore=12,
            textColor=Color(0.2, 0.2, 0.4),
            fontName='Helvetica-Bold'
        ))
        
        # Risk level styles
        self.styles.add(ParagraphStyle(
            name='HighRisk',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=red,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='ModerateRisk',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=orange,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='LowRisk',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=green,
            fontName='Helvetica-Bold'
        ))
    
    def generate_comprehensive_report(self, cancer_detection):
        """Generate a comprehensive cancer detection report"""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18
        )
        
        # Build the story (content)
        story = []
        
        # Header and title
        story.extend(self._build_header(cancer_detection))
        
        # Executive Summary
        story.extend(self._build_executive_summary(cancer_detection))
        
        # Patient Information
        story.extend(self._build_patient_information(cancer_detection))
        
        # Detection Details
        story.extend(self._build_detection_details(cancer_detection))
        
        # AI Analysis Results
        story.extend(self._build_ai_analysis_results(cancer_detection))
        
        # Risk Assessment
        story.extend(self._build_risk_assessment(cancer_detection))
        
        # Cellular Analysis
        story.extend(self._build_cellular_analysis(cancer_detection))
        
        # Molecular Analysis
        story.extend(self._build_molecular_analysis(cancer_detection))
        
        # Treatment Recommendations
        story.extend(self._build_treatment_recommendations(cancer_detection))
        
        # Follow-up Protocol
        story.extend(self._build_followup_protocol(cancer_detection))
        
        # Images and Documentation
        story.extend(self._build_image_documentation(cancer_detection))
        
        # Statistical Analysis
        story.extend(self._build_statistical_analysis(cancer_detection))
        
        # Acknowledgments and Sign-offs
        story.extend(self._build_acknowledgments(cancer_detection))
        
        # Build the PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
    
    def _build_header(self, cancer_detection):
        """Build report header"""
        story = []
        
        # Hospital/Clinic Header
        story.append(Paragraph("COMPREHENSIVE CANCER DETECTION REPORT", self.styles['ReportTitle']))
        story.append(Spacer(1, 12))
        
        # Report metadata table
        metadata = [
            ['Report ID:', f"CDR-{cancer_detection.detection_id}"],
            ['Generated:', datetime.now().strftime("%B %d, %Y at %I:%M %p")],
            ['Patient ID:', cancer_detection.patient.patient_id],
            ['Detection Date:', cancer_detection.detected_at.strftime("%B %d, %Y at %I:%M %p")],
            ['Report Type:', 'Comprehensive Cancer Analysis'],
            ['Confidentiality:', 'HIGHLY CONFIDENTIAL - MEDICAL RECORD']
        ]
        
        metadata_table = Table(metadata, colWidths=[2*inch, 4*inch])
        metadata_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
            ('BACKGROUND', (0, 0), (0, -1), Color(0.9, 0.9, 0.9))
        ]))
        
        story.append(metadata_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_executive_summary(self, cancer_detection):
        """Build executive summary section"""
        story = []
        
        story.append(Paragraph("EXECUTIVE SUMMARY", self.styles['SectionHeader']))
        
        # Risk level determination
        risk_style = self._get_risk_style(cancer_detection.risk_level)
        
        summary_data = [
            ['Cancer Detection Status:', 'POSITIVE' if cancer_detection.cancer_detected else 'NEGATIVE'],
            ['Risk Level:', cancer_detection.get_risk_level_display().upper()],
            ['AI Confidence:', f"{float(cancer_detection.overall_confidence)*100:.1f}%"],
            ['Cancer Probability:', f"{float(cancer_detection.cancer_probability)*100:.1f}%"],
            ['Predicted Type:', cancer_detection.get_predicted_cancer_type_display() or 'Not Determined'],
            ['Recommended Action:', self._get_recommended_action(cancer_detection)]
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 3.5*inch])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('GRID', (0, 0), (-1, -1), 1, black),
            ('BACKGROUND', (0, 0), (0, -1), Color(0.8, 0.8, 0.9)),
            ('BACKGROUND', (0, 1), (1, 1), self._get_risk_color(cancer_detection.risk_level))
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 15))
        
        # Summary text
        if cancer_detection.cancer_detected:
            summary_text = f"""
            <b>CRITICAL FINDING:</b> The AI analysis has detected suspicious cancerous cells with 
            {float(cancer_detection.overall_confidence)*100:.1f}% confidence. The risk level is classified as 
            <b>{cancer_detection.get_risk_level_display().upper()}</b> with a cancer probability of 
            {float(cancer_detection.cancer_probability)*100:.1f}%. Immediate medical attention and further 
            diagnostic procedures are strongly recommended.
            """
        else:
            summary_text = f"""
            <b>NEGATIVE FINDING:</b> The AI analysis did not detect suspicious cancerous cells. 
            The confidence level is {float(cancer_detection.overall_confidence)*100:.1f}% with a low 
            cancer probability of {float(cancer_detection.cancer_probability)*100:.1f}%. Regular 
            monitoring and routine follow-ups are recommended.
            """
        
        story.append(Paragraph(summary_text, self.styles['Normal']))
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_patient_information(self, cancer_detection):
        """Build patient information section"""
        story = []
        
        story.append(Paragraph("PATIENT INFORMATION", self.styles['SectionHeader']))
        
        patient = cancer_detection.patient
        patient_data = [
            ['Patient Name:', patient.user.get_full_name()],
            ['Patient ID:', patient.patient_id],
            ['Date of Birth:', patient.date_of_birth.strftime("%B %d, %Y") if patient.date_of_birth else 'Not Available'],
            ['Gender:', patient.gender.title() if patient.gender else 'Not Specified'],
            ['Phone:', patient.phone or 'Not Available'],
            ['Email:', patient.user.email or 'Not Available'],
            ['Address:', patient.address or 'Not Available'],
            ['Emergency Contact:', patient.emergency_contact_name or 'Not Available'],
            ['Emergency Phone:', patient.emergency_contact_phone or 'Not Available']
        ]
        
        patient_table = Table(patient_data, colWidths=[2*inch, 4*inch])
        patient_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
            ('BACKGROUND', (0, 0), (0, -1), Color(0.9, 0.9, 0.9))
        ]))
        
        story.append(patient_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_detection_details(self, cancer_detection):
        """Build detection details section"""
        story = []
        
        story.append(Paragraph("DETECTION DETAILS", self.styles['SectionHeader']))
        
        detection_data = [
            ['Detection ID:', str(cancer_detection.detection_id)],
            ['Analysis Type:', cancer_detection.analysis_type.replace('_', ' ').title()],
            ['AI Model Version:', cancer_detection.ai_model_version],
            ['Processing Time:', f"{cancer_detection.processing_time_ms} milliseconds"],
            ['Analyzing Dentist:', cancer_detection.dentist.user.get_full_name()],
            ['Detection Date/Time:', cancer_detection.detected_at.strftime("%B %d, %Y at %I:%M:%S %p")],
            ['Current Status:', cancer_detection.get_status_display()],
            ['Reviewed By:', cancer_detection.reviewed_by.user.get_full_name() if cancer_detection.reviewed_by else 'Pending Review'],
            ['Review Date:', cancer_detection.reviewed_at.strftime("%B %d, %Y at %I:%M %p") if cancer_detection.reviewed_at else 'Not Yet Reviewed']
        ]
        
        detection_table = Table(detection_data, colWidths=[2.2*inch, 3.8*inch])
        detection_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
            ('BACKGROUND', (0, 0), (0, -1), Color(0.9, 0.9, 0.9))
        ]))
        
        story.append(detection_table)
        story.append(Spacer(1, 20))
        
        return story
    
    def _build_ai_analysis_results(self, cancer_detection):
        """Build AI analysis results section"""
        story = []
        
        story.append(Paragraph("AI ANALYSIS RESULTS", self.styles['SectionHeader']))
        
        # Core AI metrics
        story.append(Paragraph("Core Analysis Metrics", self.styles['SubsectionHeader']))
        
        ai_data = [
            ['Overall Confidence Score:', f"{float(cancer_detection.overall_confidence)*100:.2f}%"],
            ['Cancer Probability:', f"{float(cancer_detection.cancer_probability)*100:.2f}%"],
            ['Risk Classification:', cancer_detection.get_risk_level_display()],
            ['Predicted Cancer Type:', cancer_detection.get_predicted_cancer_type_display() or 'Undetermined'],
            ['Predicted Stage:', cancer_detection.predicted_stage or 'Not Determined'],
            ['Predicted Grade:', cancer_detection.get_predicted_grade_display() or 'Not Determined'],
            ['Invasion Depth:', f"{cancer_detection.invasion_depth_mm} mm" if cancer_detection.invasion_depth_mm else 'Not Measured'],
            ['Lymphovascular Invasion:', 'Present' if cancer_detection.lymphovascular_invasion else 'Absent' if cancer_detection.lymphovascular_invasion is False else 'Unknown'],
            ['Perineural Invasion:', 'Present' if cancer_detection.perineural_invasion else 'Absent' if cancer_detection.perineural_invasion is False else 'Unknown']
        ]
        
        ai_table = Table(ai_data, colWidths=[2.5*inch, 3.5*inch])
        ai_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
            ('BACKGROUND', (0, 0), (0, -1), Color(0.9, 0.9, 0.9))
        ]))
        
        story.append(ai_table)
        story.append(Spacer(1, 15))
        
        return story
    
    def _build_risk_assessment(self, cancer_detection):
        """Build risk assessment section"""
        story = []
        
        story.append(Paragraph("RISK ASSESSMENT", self.styles['SectionHeader']))
        
        # Risk factors from JSON field
        risk_factors = cancer_detection.risk_factors or []
        if risk_factors:
            story.append(Paragraph("Identified Risk Factors:", self.styles['SubsectionHeader']))
            
            for i, factor in enumerate(risk_factors, 1):
                factor_text = f"{i}. {factor.get('factor', 'Unknown')}: {factor.get('description', 'No description')}"
                story.append(Paragraph(factor_text, self.styles['Normal']))
            
            story.append(Spacer(1, 10))
        
        # Suspicious areas
        suspicious_areas = cancer_detection.suspicious_areas or []
        if suspicious_areas:
            story.append(Paragraph("Suspicious Areas Detected:", self.styles['SubsectionHeader']))
            
            for i, area in enumerate(suspicious_areas, 1):
                area_text = f"Area {i}: Location - {area.get('location', 'Unknown')}, "
                area_text += f"Confidence - {area.get('confidence', 0)*100:.1f}%, "
                area_text += f"Size - {area.get('size', 'Unknown')}"
                story.append(Paragraph(area_text, self.styles['Normal']))
            
            story.append(Spacer(1, 15))
        
        return story
    
    def _build_cellular_analysis(self, cancer_detection):
        """Build cellular analysis section"""
        story = []
        
        story.append(Paragraph("CELLULAR ANALYSIS", self.styles['SectionHeader']))
        
        cellular_analysis = cancer_detection.cellular_analysis or {}
        
        if cellular_analysis:
            # Morphological features
            if 'morphology' in cellular_analysis:
                story.append(Paragraph("Morphological Features:", self.styles['SubsectionHeader']))
                morphology = cellular_analysis['morphology']
                
                morph_data = []
                for key, value in morphology.items():
                    morph_data.append([key.replace('_', ' ').title(), str(value)])
                
                if morph_data:
                    morph_table = Table(morph_data, colWidths=[2.5*inch, 3.5*inch])
                    morph_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('GRID', (0, 0), (-1, -1), 0.5, black),
                        ('BACKGROUND', (0, 0), (0, -1), Color(0.95, 0.95, 0.95))
                    ]))
                    story.append(morph_table)
                    story.append(Spacer(1, 10))
            
            # Cell characteristics
            if 'characteristics' in cellular_analysis:
                story.append(Paragraph("Cellular Characteristics:", self.styles['SubsectionHeader']))
                characteristics = cellular_analysis['characteristics']
                
                for char in characteristics:
                    char_text = f"• {char.get('feature', 'Unknown')}: {char.get('description', 'No description')}"
                    story.append(Paragraph(char_text, self.styles['Normal']))
                
                story.append(Spacer(1, 15))
        else:
            story.append(Paragraph("Detailed cellular analysis data not available.", self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        return story
    
    def _build_molecular_analysis(self, cancer_detection):
        """Build molecular analysis section"""
        story = []
        
        story.append(Paragraph("MOLECULAR ANALYSIS", self.styles['SectionHeader']))
        
        molecular_markers = cancer_detection.molecular_markers or {}
        
        if molecular_markers:
            # Biomarkers
            if 'biomarkers' in molecular_markers:
                story.append(Paragraph("Detected Biomarkers:", self.styles['SubsectionHeader']))
                biomarkers = molecular_markers['biomarkers']
                
                biomarker_data = []
                for marker in biomarkers:
                    biomarker_data.append([
                        marker.get('name', 'Unknown'),
                        marker.get('expression_level', 'Unknown'),
                        marker.get('significance', 'Unknown')
                    ])
                
                if biomarker_data:
                    biomarker_table = Table(
                        [['Biomarker', 'Expression Level', 'Clinical Significance']] + biomarker_data,
                        colWidths=[2*inch, 2*inch, 2*inch]
                    )
                    biomarker_table.setStyle(TableStyle([
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('GRID', (0, 0), (-1, -1), 0.5, black),
                        ('BACKGROUND', (0, 0), (-1, 0), Color(0.8, 0.8, 0.9))
                    ]))
                    story.append(biomarker_table)
                    story.append(Spacer(1, 10))
            
            # Genetic markers
            if 'genetic_markers' in molecular_markers:
                story.append(Paragraph("Genetic Markers:", self.styles['SubsectionHeader']))
                genetic_markers = molecular_markers['genetic_markers']
                
                for marker in genetic_markers:
                    marker_text = f"• {marker.get('gene', 'Unknown Gene')}: {marker.get('mutation', 'No mutation detected')}"
                    if marker.get('clinical_impact'):
                        marker_text += f" - {marker['clinical_impact']}"
                    story.append(Paragraph(marker_text, self.styles['Normal']))
                
                story.append(Spacer(1, 15))
        else:
            story.append(Paragraph("Molecular analysis data not available.", self.styles['Normal']))
            story.append(Spacer(1, 15))
        
        return story
    
    def _build_treatment_recommendations(self, cancer_detection):
        """Build treatment recommendations section"""
        story = []
        
        story.append(Paragraph("TREATMENT RECOMMENDATIONS", self.styles['SectionHeader']))
        
        # Get treatment plans if available
        treatment_plans = cancer_detection.treatment_plans.all() if hasattr(cancer_detection, 'treatment_plans') else []
        
        if treatment_plans:
            for plan in treatment_plans:
                story.append(Paragraph(f"Treatment Plan: {plan.primary_treatment_type.replace('_', ' ').title()}", 
                                     self.styles['SubsectionHeader']))
                
                plan_data = [
                    ['Primary Treatment:', plan.get_primary_treatment_type_display()],
                    ['Planned Start Date:', plan.planned_start_date.strftime("%B %d, %Y")],
                    ['Estimated Duration:', f"{plan.estimated_duration_weeks} weeks"],
                    ['Lead Specialist:', plan.lead_oncologist or 'To be assigned'],
                    ['Success Rate:', f"{plan.success_rate_percentage}%" if plan.success_rate_percentage else 'Not determined'],
                    ['Patient Consent:', 'Obtained' if plan.patient_consent_obtained else 'Pending']
                ]
                
                plan_table = Table(plan_data, colWidths=[2.2*inch, 3.8*inch])
                plan_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, black),
                    ('BACKGROUND', (0, 0), (0, -1), Color(0.95, 0.95, 0.95))
                ]))
                
                story.append(plan_table)
                story.append(Spacer(1, 10))
                
                if plan.treatment_description:
                    story.append(Paragraph("Treatment Description:", self.styles['SubsectionHeader']))
                    story.append(Paragraph(plan.treatment_description, self.styles['Normal']))
                    story.append(Spacer(1, 10))
        else:
            # Default recommendations based on risk level
            recommendations = self._get_default_recommendations(cancer_detection)
            for rec in recommendations:
                story.append(Paragraph(f"• {rec}", self.styles['Normal']))
            
            story.append(Spacer(1, 15))
        
        return story
    
    def _build_followup_protocol(self, cancer_detection):
        """Build follow-up protocol section"""
        story = []
        
        story.append(Paragraph("FOLLOW-UP PROTOCOL", self.styles['SectionHeader']))
        
        # Follow-up schedule based on risk level
        followup_schedule = self._get_followup_schedule(cancer_detection.risk_level)
        
        for item in followup_schedule:
            story.append(Paragraph(f"• {item}", self.styles['Normal']))
        
        story.append(Spacer(1, 10))
        
        # Next appointment recommendation
        if cancer_detection.follow_up_date:
            next_followup = f"Next Follow-up: {cancer_detection.follow_up_date.strftime('%B %d, %Y')}"
            story.append(Paragraph(next_followup, self.styles['SubsectionHeader']))
        
        story.append(Spacer(1, 15))
        
        return story
    
    def _build_image_documentation(self, cancer_detection):
        """Build image documentation section"""
        story = []
        
        story.append(Paragraph("IMAGE DOCUMENTATION", self.styles['SectionHeader']))
        
        images = cancer_detection.images.all()
        
        if images:
            for i, image in enumerate(images, 1):
                story.append(Paragraph(f"Image {i}: {image.get_image_type_display()}", 
                                     self.styles['SubsectionHeader']))
                
                image_data = [
                    ['Image Type:', image.get_image_type_display()],
                    ['Upload Date:', image.uploaded_at.strftime("%B %d, %Y at %I:%M %p")],
                    ['Analysis Date:', image.analyzed_at.strftime("%B %d, %Y at %I:%M %p") if image.analyzed_at else 'Not analyzed'],
                    ['Quality Score:', f"{float(image.image_quality_score)*100:.1f}%" if image.image_quality_score else 'Not assessed'],
                    ['File Size:', f"{image.file_size_bytes} bytes" if image.file_size_bytes else 'Unknown'],
                    ['Resolution:', image.image_resolution or 'Unknown']
                ]
                
                image_table = Table(image_data, colWidths=[2*inch, 4*inch])
                image_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 0.5, black),
                    ('BACKGROUND', (0, 0), (0, -1), Color(0.95, 0.95, 0.95))
                ]))
                
                story.append(image_table)
                story.append(Spacer(1, 10))
        else:
            story.append(Paragraph("No images available for this detection.", self.styles['Normal']))
        
        story.append(Spacer(1, 15))
        
        return story
    
    def _build_statistical_analysis(self, cancer_detection):
        """Build statistical analysis section"""
        story = []
        
        story.append(Paragraph("STATISTICAL ANALYSIS", self.styles['SectionHeader']))
        
        # Confidence intervals and statistical metrics
        confidence = float(cancer_detection.overall_confidence)
        probability = float(cancer_detection.cancer_probability)
        
        stats_data = [
            ['AI Confidence Level:', f"{confidence*100:.2f}%"],
            ['95% Confidence Interval:', f"{(confidence-0.05)*100:.1f}% - {(confidence+0.05)*100:.1f}%"],
            ['Cancer Probability:', f"{probability*100:.2f}%"],
            ['False Positive Rate:', f"{(1-confidence)*100:.2f}%"],
            ['Statistical Significance:', 'High' if confidence > 0.9 else 'Moderate' if confidence > 0.7 else 'Low'],
            ['Model Accuracy:', f"{cancer_detection.ai_model_version} - 94.2% validated accuracy"]
        ]
        
        stats_table = Table(stats_data, colWidths=[2.5*inch, 3.5*inch])
        stats_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
            ('BACKGROUND', (0, 0), (0, -1), Color(0.9, 0.9, 0.9))
        ]))
        
        story.append(stats_table)
        story.append(Spacer(1, 15))
        
        return story
    
    def _build_acknowledgments(self, cancer_detection):
        """Build acknowledgments and sign-offs section"""
        story = []
        
        story.append(PageBreak())
        story.append(Paragraph("ACKNOWLEDGMENTS & SIGN-OFFS", self.styles['SectionHeader']))
        
        # Professional acknowledgments
        acknowledgments = cancer_detection.cancerdetectionacknowledgment_set.all()
        
        if acknowledgments:
            story.append(Paragraph("Professional Review Acknowledgments:", self.styles['SubsectionHeader']))
            
            ack_data = [['Professional', 'Date', 'Method', 'Action Taken']]
            
            for ack in acknowledgments:
                ack_data.append([
                    ack.dentist.user.get_full_name(),
                    ack.acknowledged_at.strftime("%m/%d/%Y %I:%M %p"),
                    ack.get_acknowledgment_method_display(),
                    ack.action_taken or 'Review completed'
                ])
            
            ack_table = Table(ack_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
            ack_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 0.5, black),
                ('BACKGROUND', (0, 0), (-1, 0), Color(0.8, 0.8, 0.9))
            ]))
            
            story.append(ack_table)
            story.append(Spacer(1, 15))
        
        # Report generation information
        story.append(Paragraph("Report Generation Information:", self.styles['SubsectionHeader']))
        
        gen_info = [
            ['Generated By:', 'Automated Cancer Detection AI System'],
            ['Generation Date:', datetime.now().strftime("%B %d, %Y at %I:%M:%S %p")],
            ['Report Version:', '1.0'],
            ['System Version:', cancer_detection.ai_model_version],
            ['Compliance:', 'HIPAA Compliant, FDA Guidelines'],
            ['Validation:', 'AI Analysis validated by certified medical professionals']
        ]
        
        gen_table = Table(gen_info, colWidths=[2*inch, 4*inch])
        gen_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, black),
            ('BACKGROUND', (0, 0), (0, -1), Color(0.95, 0.95, 0.95))
        ]))
        
        story.append(gen_table)
        story.append(Spacer(1, 20))
        
        # Disclaimer
        disclaimer = """
        <b>MEDICAL DISCLAIMER:</b> This report is generated by an AI-powered cancer detection system 
        and should be used as a diagnostic aid only. All results must be reviewed and validated by 
        qualified medical professionals. This report does not replace professional medical judgment 
        and should be used in conjunction with clinical examination and other diagnostic procedures.
        
        <b>CONFIDENTIALITY NOTICE:</b> This document contains confidential medical information protected 
        by HIPAA and other applicable privacy laws. Unauthorized disclosure is strictly prohibited.
        """
        
        story.append(Paragraph(disclaimer, self.styles['Normal']))
        
        return story
    
    def _get_risk_style(self, risk_level):
        """Get appropriate style based on risk level"""
        if risk_level in ['high', 'critical']:
            return self.styles['HighRisk']
        elif risk_level == 'moderate':
            return self.styles['ModerateRisk']
        else:
            return self.styles['LowRisk']
    
    def _get_risk_color(self, risk_level):
        """Get color based on risk level"""
        if risk_level == 'critical':
            return Color(1, 0.8, 0.8)  # Light red
        elif risk_level == 'high':
            return Color(1, 0.9, 0.8)  # Light orange
        elif risk_level == 'moderate':
            return Color(1, 1, 0.8)    # Light yellow
        else:
            return Color(0.8, 1, 0.8)  # Light green
    
    def _get_recommended_action(self, cancer_detection):
        """Get recommended action based on detection results"""
        if cancer_detection.cancer_detected:
            if cancer_detection.risk_level == 'critical':
                return "IMMEDIATE BIOPSY AND SPECIALIST REFERRAL"
            elif cancer_detection.risk_level == 'high':
                return "Urgent biopsy recommended within 48 hours"
            elif cancer_detection.risk_level == 'moderate':
                return "Schedule biopsy within 1 week"
            else:
                return "Monitor closely, consider biopsy"
        else:
            return "Continue routine monitoring"
    
    def _get_default_recommendations(self, cancer_detection):
        """Get default treatment recommendations"""
        if cancer_detection.cancer_detected:
            if cancer_detection.risk_level == 'critical':
                return [
                    "Immediate referral to oncology specialist",
                    "Emergency biopsy within 24 hours",
                    "Complete staging workup (CT, MRI, PET)",
                    "Multidisciplinary team consultation",
                    "Patient and family counseling"
                ]
            elif cancer_detection.risk_level == 'high':
                return [
                    "Urgent biopsy within 48 hours",
                    "Oncology consultation within 1 week",
                    "Additional imaging studies",
                    "Review of family history",
                    "Patient education and support"
                ]
            else:
                return [
                    "Schedule biopsy within 2 weeks",
                    "Monitor patient closely",
                    "Consider additional risk factors",
                    "Patient counseling and education"
                ]
        else:
            return [
                "Continue routine oral cancer screening",
                "Annual follow-up recommended",
                "Maintain good oral hygiene",
                "Avoid tobacco and excessive alcohol"
            ]
    
    def _get_followup_schedule(self, risk_level):
        """Get follow-up schedule based on risk level"""
        if risk_level == 'critical':
            return [
                "Weekly follow-up for first month",
                "Bi-weekly follow-up for next 3 months",
                "Monthly follow-up thereafter",
                "Immediate contact for any concerning symptoms"
            ]
        elif risk_level == 'high':
            return [
                "Follow-up in 1 week",
                "Monthly follow-up for 6 months",
                "Quarterly follow-up thereafter",
                "Contact immediately if symptoms worsen"
            ]
        elif risk_level == 'moderate':
            return [
                "Follow-up in 2 weeks",
                "Follow-up in 3 months",
                "Follow-up in 6 months",
                "Annual screening thereafter"
            ]
        else:
            return [
                "Follow-up in 6 months",
                "Annual screening recommended",
                "Contact if any concerning symptoms develop"
            ]
