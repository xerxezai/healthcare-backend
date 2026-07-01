"""
Patient Report Generation Service
Generate comprehensive patient reports with AI analysis
"""
import json
from datetime import datetime
from django.utils import timezone
from django.template.loader import render_to_string
from .advanced_models import PatientReport

class PatientReportGenerator:
    """
    Service for generating various types of patient reports
    """
    
    def __init__(self):
        self.report_templates = {
            'comprehensive': 'reports/comprehensive_report.html',
            'discharge_summary': 'reports/discharge_summary.html',
            'ai_analysis': 'reports/ai_analysis.html',
            'clinical_summary': 'reports/clinical_summary.html'
        }
    
    def generate_comprehensive_report(self, admission):
        """
        Generate comprehensive patient report including all data
        """
        try:
            # Gather all patient data
            patient_data = self._gather_patient_data(admission)
            journey_data = self._gather_journey_data(admission)
            ai_insights_data = self._gather_ai_insights(admission)
            metrics_data = self._gather_metrics_data(admission)
            
            # Compile report content
            content = {
                'report_type': 'comprehensive',
                'generated_at': timezone.now().isoformat(),
                'patient_info': patient_data,
                'admission_details': self._format_admission_details(admission),
                'clinical_journey': journey_data,
                'ai_insights': ai_insights_data,
                'quality_metrics': metrics_data,
                'summary': self._generate_comprehensive_summary(admission, ai_insights_data),
                'recommendations': self._compile_all_recommendations(admission)
            }
            
            return content
            
        except Exception as e:
            print(f"Error generating comprehensive report: {str(e)}")
            return {'error': str(e)}
    
    def generate_discharge_summary(self, admission):
        """
        Generate discharge summary report
        """
        try:
            content = {
                'report_type': 'discharge_summary',
                'generated_at': timezone.now().isoformat(),
                'patient_info': self._gather_patient_data(admission),
                'admission_summary': {
                    'admission_date': admission.admission_date.isoformat(),
                    'discharge_date': admission.discharge_date.isoformat() if admission.discharge_date else None,
                    'length_of_stay': admission.length_of_stay,
                    'admission_diagnosis': admission.initial_diagnosis,
                    'discharge_diagnosis': admission.discharge_diagnosis,
                    'department': admission.department,
                    'attending_physician': admission.attending_physician.get_full_name() if admission.attending_physician else 'Not assigned'
                },
                'treatment_summary': self._generate_treatment_summary(admission),
                'discharge_instructions': {
                    'medications': admission.discharge_medications,
                    'instructions': admission.discharge_instructions,
                    'follow_up_required': admission.follow_up_required,
                    'follow_up_date': admission.follow_up_date.isoformat() if admission.follow_up_date else None
                },
                'final_assessments': self._generate_final_assessments(admission),
                'summary': f"Patient successfully treated for {admission.initial_diagnosis} over {admission.length_of_stay} days and discharged in stable condition."
            }
            
            return content
            
        except Exception as e:
            print(f"Error generating discharge summary: {str(e)}")
            return {'error': str(e)}
    
    def generate_ai_analysis_report(self, admission):
        """
        Generate AI analysis and insights report
        """
        try:
            ai_insights = admission.ai_insights.all().order_by('-generated_at')
            
            content = {
                'report_type': 'ai_analysis',
                'generated_at': timezone.now().isoformat(),
                'patient_info': self._gather_patient_data(admission),
                'overall_risk_assessment': {
                    'risk_score': admission.ai_risk_score,
                    'risk_level': self._categorize_risk_level(admission.ai_risk_score),
                    'last_updated': admission.updated_at.isoformat()
                },
                'detailed_insights': self._format_ai_insights(ai_insights),
                'predictive_analytics': self._compile_predictions(ai_insights),
                'recommendations_summary': self._compile_ai_recommendations(ai_insights),
                'model_performance': {
                    'insights_generated': ai_insights.count(),
                    'average_confidence': self._calculate_average_confidence(ai_insights),
                    'validated_insights': ai_insights.filter(is_validated=True).count()
                },
                'summary': self._generate_ai_summary(admission, ai_insights)
            }
            
            return content
            
        except Exception as e:
            print(f"Error generating AI analysis report: {str(e)}")
            return {'error': str(e)}
    
    def generate_basic_report(self, admission):
        """
        Generate basic patient report
        """
        try:
            content = {
                'report_type': 'basic',
                'generated_at': timezone.now().isoformat(),
                'patient_info': self._gather_patient_data(admission),
                'admission_info': self._format_admission_details(admission),
                'current_status': {
                    'status': admission.current_status,
                    'priority': admission.priority_level,
                    'length_of_stay': admission.length_of_stay,
                    'location': f"{admission.department} - Room {admission.room_number}" if admission.room_number else admission.department
                },
                'summary': f"Patient {admission.patient.first_name} {admission.patient.last_name} currently {admission.current_status} in {admission.department}."
            }
            
            return content
            
        except Exception as e:
            print(f"Error generating basic report: {str(e)}")
            return {'error': str(e)}
    
    def _gather_patient_data(self, admission):
        """
        Gather comprehensive patient information
        """
        patient = admission.patient
        
        return {
            'patient_id': patient.patient_id,
            'full_name': f"{patient.first_name} {patient.last_name}",
            'date_of_birth': patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            'age': self._calculate_age(patient.date_of_birth) if patient.date_of_birth else None,
            'gender': patient.gender,
            'phone': patient.phone_number,
            'email': patient.email,
            'address': patient.address,
            'emergency_contact': patient.emergency_contact_name,
            'emergency_phone': patient.emergency_contact_phone,
            'insurance': {
                'provider': admission.insurance_provider,
                'policy_number': admission.insurance_policy_number
            }
        }
    
    def _format_admission_details(self, admission):
        """
        Format admission details for report
        """
        return {
            'admission_id': admission.admission_id,
            'admission_date': admission.admission_date.isoformat(),
            'admission_type': admission.get_admission_type_display(),
            'department': admission.department,
            'room_number': admission.room_number,
            'bed_number': admission.bed_number,
            'chief_complaint': admission.chief_complaint,
            'initial_diagnosis': admission.initial_diagnosis,
            'attending_physician': admission.attending_physician.get_full_name() if admission.attending_physician else 'Not assigned',
            'current_status': admission.get_current_status_display(),
            'priority_level': admission.get_priority_level_display(),
            'medical_history': admission.medical_history,
            'allergies': admission.allergies,
            'current_medications': admission.current_medications
        }
    
    def _gather_journey_data(self, admission):
        """
        Gather patient journey timeline data
        """
        journey_events = admission.journey_events.all().order_by('timestamp')
        
        timeline = []
        for event in journey_events:
            timeline.append({
                'timestamp': event.timestamp.isoformat(),
                'stage': event.get_stage_display(),
                'location': event.location,
                'action': event.action_taken,
                'staff_member': event.staff_member.get_full_name() if event.staff_member else 'System',
                'notes': event.notes,
                'duration_minutes': event.duration_minutes,
                'vital_signs': event.vital_signs
            })
        
        return {
            'total_events': len(timeline),
            'timeline': timeline,
            'key_milestones': self._identify_key_milestones(timeline)
        }
    
    def _gather_ai_insights(self, admission):
        """
        Gather AI insights data
        """
        insights = admission.ai_insights.all().order_by('-generated_at')
        
        insights_data = []
        for insight in insights:
            insights_data.append({
                'type': insight.get_insight_type_display(),
                'confidence': insight.get_confidence_level_display(),
                'risk_score': insight.risk_score,
                'predictions': insight.prediction_data,
                'recommendations': insight.recommendations,
                'risk_factors': insight.risk_factors,
                'generated_at': insight.generated_at.isoformat(),
                'is_validated': insight.is_validated,
                'validation_notes': insight.validation_notes
            })
        
        return insights_data
    
    def _gather_metrics_data(self, admission):
        """
        Gather quality metrics data
        """
        try:
            metrics = admission.metrics
            
            return {
                'time_metrics': {
                    'door_to_doctor_minutes': metrics.door_to_doctor_minutes,
                    'diagnosis_time_minutes': metrics.diagnosis_time_minutes,
                    'treatment_start_minutes': metrics.treatment_start_minutes
                },
                'quality_indicators': {
                    'medication_errors': metrics.medication_errors,
                    'falls_incidents': metrics.falls_incidents,
                    'hospital_acquired_infections': metrics.hospital_acquired_infections,
                    'pressure_ulcers': metrics.pressure_ulcers
                },
                'satisfaction': {
                    'satisfaction_score': metrics.satisfaction_score,
                    'complaints_filed': metrics.complaints_filed,
                    'compliments_received': metrics.compliments_received
                },
                'financial': {
                    'total_cost': float(metrics.total_cost) if metrics.total_cost else 0,
                    'insurance_coverage': float(metrics.insurance_coverage_amount) if metrics.insurance_coverage_amount else 0,
                    'patient_responsibility': float(metrics.patient_responsibility) if metrics.patient_responsibility else 0
                },
                'outcomes': {
                    'treatment_successful': metrics.treatment_successful,
                    'readmission_30_days': metrics.readmission_30_days,
                    'complications_occurred': metrics.complications_occurred
                }
            }
            
        except AttributeError:
            # No metrics available
            return {
                'message': 'Metrics data not available',
                'calculated': False
            }
    
    def _generate_comprehensive_summary(self, admission, ai_insights):
        """
        Generate comprehensive report summary
        """
        patient_name = f"{admission.patient.first_name} {admission.patient.last_name}"
        
        summary_parts = [
            f"Comprehensive medical report for {patient_name} (ID: {admission.admission_id})",
            f"Admitted on {admission.admission_date.strftime('%B %d, %Y')} for {admission.chief_complaint}",
            f"Current status: {admission.get_current_status_display()} with {admission.get_priority_level_display().lower()} priority",
            f"Length of stay: {admission.length_of_stay} days in {admission.department}"
        ]
        
        if ai_insights:
            risk_level = self._categorize_risk_level(admission.ai_risk_score)
            summary_parts.append(f"AI risk assessment: {risk_level} risk (score: {admission.ai_risk_score}/10)")
        
        if admission.is_discharged:
            summary_parts.append(f"Successfully discharged on {admission.discharge_date.strftime('%B %d, %Y')}")
        
        return ". ".join(summary_parts) + "."
    
    def _generate_treatment_summary(self, admission):
        """
        Generate treatment summary for discharge report
        """
        journey_events = admission.journey_events.all().order_by('timestamp')
        
        treatment_events = [event for event in journey_events if event.stage in ['treatment', 'surgery', 'consultation']]
        
        summary = {
            'primary_treatment': admission.initial_diagnosis,
            'treatment_events_count': len(treatment_events),
            'key_treatments': [],
            'procedures_performed': [],
            'medications_administered': admission.current_medications or 'Standard care medications as per protocol'
        }
        
        # Extract key treatments from journey
        for event in treatment_events:
            if event.action_taken:
                summary['key_treatments'].append({
                    'date': event.timestamp.date().isoformat(),
                    'treatment': event.action_taken,
                    'location': event.location,
                    'staff': event.staff_member.get_full_name() if event.staff_member else 'Medical team'
                })
        
        return summary
    
    def _generate_final_assessments(self, admission):
        """
        Generate final assessments for discharge
        """
        assessments = {
            'clinical_condition': 'Stable and improved' if admission.current_status == 'discharged' else admission.get_current_status_display(),
            'treatment_response': 'Good response to treatment',
            'functional_status': 'Able to perform activities of daily living',
            'discharge_readiness': admission.current_status == 'discharged'
        }
        
        # Add AI insights if available
        latest_insight = admission.ai_insights.filter(insight_type='risk_assessment').first()
        if latest_insight:
            assessments['risk_assessment'] = f"Low to moderate risk (AI score: {latest_insight.risk_score}/10)"
        
        return assessments
    
    def _format_ai_insights(self, insights):
        """
        Format AI insights for report
        """
        formatted_insights = []
        
        for insight in insights:
            formatted_insights.append({
                'type': insight.get_insight_type_display(),
                'risk_score': insight.risk_score,
                'risk_level': self._categorize_risk_level(insight.risk_score),
                'confidence': insight.get_confidence_level_display(),
                'key_predictions': self._extract_key_predictions(insight.prediction_data),
                'recommendations': insight.recommendations[:3],  # Top 3 recommendations
                'generated_at': insight.generated_at.strftime('%B %d, %Y at %I:%M %p'),
                'is_validated': insight.is_validated
            })
        
        return formatted_insights
    
    def _compile_predictions(self, insights):
        """
        Compile all predictions from AI insights
        """
        predictions = {
            'length_of_stay': None,
            'readmission_risk': None,
            'complication_risk': None,
            'cost_estimate': None
        }
        
        for insight in insights:
            if insight.insight_type == 'length_of_stay' and insight.prediction_data:
                predictions['length_of_stay'] = insight.prediction_data.get('predicted_total_stay')
            elif insight.insight_type == 'readmission_risk' and insight.prediction_data:
                predictions['readmission_risk'] = insight.prediction_data.get('readmission_probability_30_days')
            elif insight.insight_type == 'complication_risk' and insight.prediction_data:
                predictions['complication_risk'] = insight.prediction_data.get('complication_probability')
            elif insight.insight_type == 'cost_prediction' and insight.prediction_data:
                predictions['cost_estimate'] = insight.prediction_data.get('expected_cost')
        
        return predictions
    
    def _compile_all_recommendations(self, admission):
        """
        Compile all recommendations from various sources
        """
        recommendations = []
        
        # AI recommendations
        for insight in admission.ai_insights.all():
            if insight.recommendations:
                for rec in insight.recommendations:
                    recommendations.append({
                        'source': 'AI Analysis',
                        'type': rec.get('type', 'general'),
                        'priority': rec.get('priority', 'medium'),
                        'action': rec.get('action', ''),
                        'rationale': rec.get('rationale', '')
                    })
        
        # Clinical recommendations based on status
        if admission.current_status == 'discharge_ready':
            recommendations.append({
                'source': 'Clinical Assessment',
                'type': 'discharge',
                'priority': 'high',
                'action': 'Complete discharge process and provide patient education',
                'rationale': 'Patient meets discharge criteria'
            })
        
        return recommendations[:10]  # Limit to top 10 recommendations
    
    def _categorize_risk_level(self, risk_score):
        """
        Categorize risk score into levels
        """
        if risk_score >= 7:
            return 'High'
        elif risk_score >= 4:
            return 'Medium'
        else:
            return 'Low'
    
    def _calculate_age(self, birth_date):
        """
        Calculate age from birth date
        """
        today = timezone.now().date()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    def _identify_key_milestones(self, timeline):
        """
        Identify key milestones in patient journey
        """
        milestones = []
        
        for event in timeline:
            if event['stage'] in ['Admission', 'Diagnosis', 'Surgery', 'Discharge']:
                milestones.append({
                    'milestone': event['stage'],
                    'timestamp': event['timestamp'],
                    'description': event['action']
                })
        
        return milestones
    
    def _extract_key_predictions(self, prediction_data):
        """
        Extract key predictions from prediction data
        """
        if not prediction_data:
            return []
        
        key_predictions = []
        
        for key, value in prediction_data.items():
            if key in ['length_of_stay_days', 'complication_probability', 'readmission_probability_30_days']:
                key_predictions.append({
                    'metric': key.replace('_', ' ').title(),
                    'value': value,
                    'type': 'numeric'
                })
        
        return key_predictions[:5]  # Top 5 predictions
    
    def _compile_ai_recommendations(self, insights):
        """
        Compile AI recommendations
        """
        all_recommendations = []
        
        for insight in insights:
            if insight.recommendations:
                for rec in insight.recommendations:
                    all_recommendations.append({
                        'insight_type': insight.get_insight_type_display(),
                        'action': rec.get('action', ''),
                        'priority': rec.get('priority', 'medium'),
                        'rationale': rec.get('rationale', ''),
                        'generated_at': insight.generated_at.strftime('%B %d, %Y')
                    })
        
        return all_recommendations
    
    def _calculate_average_confidence(self, insights):
        """
        Calculate average confidence level
        """
        if not insights.exists():
            return 'N/A'
        
        confidence_mapping = {'low': 1, 'medium': 2, 'high': 3, 'very_high': 4}
        total_confidence = sum(confidence_mapping.get(insight.confidence_level, 2) for insight in insights)
        avg_confidence = total_confidence / insights.count()
        
        if avg_confidence >= 3.5:
            return 'High'
        elif avg_confidence >= 2.5:
            return 'Medium'
        else:
            return 'Low'
    
    def _generate_ai_summary(self, admission, insights):
        """
        Generate AI analysis summary
        """
        patient_name = f"{admission.patient.first_name} {admission.patient.last_name}"
        insights_count = insights.count()
        
        if insights_count == 0:
            return f"No AI insights available for {patient_name} at this time."
        
        risk_level = self._categorize_risk_level(admission.ai_risk_score)
        validated_count = insights.filter(is_validated=True).count()
        
        summary = f"AI analysis for {patient_name} generated {insights_count} insights with overall {risk_level.lower()} risk assessment. "
        summary += f"{validated_count} insights have been clinically validated. "
        summary += f"Current risk score: {admission.ai_risk_score}/10."
        
        return summary
