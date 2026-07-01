"""
AI-Powered Patient Analysis Services
Provides intelligent insights and predictions for patient care
"""
import random
import json
from datetime import datetime, timedelta
from django.utils import timezone
from .advanced_models import AIPatientInsights, PatientJourney

class AIPatientAnalyzer:
    """
    AI service for analyzing patient data and generating insights
    In production, this would integrate with actual ML models
    """
    
    def __init__(self):
        self.model_version = "v1.0"
        
    def analyze_admission_risk(self, admission):
        """
        Analyze patient admission and generate initial risk assessment
        """
        try:
            # Calculate risk factors
            risk_factors = self._calculate_risk_factors(admission)
            
            # Generate risk score (0-10 scale)
            risk_score = self._calculate_risk_score(admission, risk_factors)
            
            # Generate predictions
            predictions = self._generate_predictions(admission, risk_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(admission, risk_score, risk_factors)
            
            # Determine confidence level
            confidence_level = self._determine_confidence_level(risk_score)
            
            # Create AI insight record
            insight = AIPatientInsights.objects.create(
                admission=admission,
                patient=admission.patient,
                insight_type='risk_assessment',
                confidence_level=confidence_level,
                prediction_data=predictions,
                recommendations=recommendations,
                risk_factors=risk_factors,
                risk_score=risk_score,
                accuracy_score=0.85,  # Model accuracy
                model_version=self.model_version,
                expires_at=timezone.now() + timedelta(hours=24)
            )
            
            # Update admission risk score
            admission.ai_risk_score = risk_score
            admission.ai_predictions = predictions
            admission.save()
            
            return insight
            
        except Exception as e:
            print(f"Error in AI risk analysis: {str(e)}")
            return None
    
    def update_patient_insights(self, admission):
        """
        Update AI insights based on current patient status
        """
        try:
            # Generate length of stay prediction
            los_insight = self._generate_length_of_stay_prediction(admission)
            
            # Generate readmission risk if patient is discharge ready
            if admission.current_status == 'discharge_ready':
                readmission_insight = self._generate_readmission_risk(admission)
            
            # Generate treatment recommendations
            treatment_insight = self._generate_treatment_recommendations(admission)
            
            return True
            
        except Exception as e:
            print(f"Error updating AI insights: {str(e)}")
            return False
    
    def generate_insight(self, admission, insight_type):
        """
        Generate specific type of AI insight
        """
        try:
            if insight_type == 'length_of_stay':
                return self._generate_length_of_stay_prediction(admission)
            elif insight_type == 'readmission_risk':
                return self._generate_readmission_risk(admission)
            elif insight_type == 'complication_risk':
                return self._generate_complication_risk(admission)
            elif insight_type == 'treatment_recommendation':
                return self._generate_treatment_recommendations(admission)
            elif insight_type == 'discharge_planning':
                return self._generate_discharge_planning(admission)
            elif insight_type == 'cost_prediction':
                return self._generate_cost_prediction(admission)
            else:
                return None
                
        except Exception as e:
            print(f"Error generating {insight_type} insight: {str(e)}")
            return None
    
    def _calculate_risk_factors(self, admission):
        """
        Calculate risk factors based on patient data
        """
        risk_factors = []
        
        # Age-based risk
        if hasattr(admission.patient, 'date_of_birth') and admission.patient.date_of_birth:
            age = self._calculate_age(admission.patient.date_of_birth)
            if age > 65:
                risk_factors.append({
                    'factor': 'Advanced Age',
                    'value': age,
                    'impact': 'medium',
                    'description': f'Patient age {age} increases complication risk'
                })
        
        # Medical history risk
        if admission.medical_history:
            if any(condition in admission.medical_history.lower() for condition in 
                   ['diabetes', 'hypertension', 'heart disease', 'cancer']):
                risk_factors.append({
                    'factor': 'Chronic Conditions',
                    'value': 'present',
                    'impact': 'high',
                    'description': 'Chronic medical conditions increase treatment complexity'
                })
        
        # Emergency admission risk
        if admission.admission_type == 'emergency':
            risk_factors.append({
                'factor': 'Emergency Admission',
                'value': 'yes',
                'impact': 'medium',
                'description': 'Emergency admissions typically have higher risk'
            })
        
        # Allergy risk
        if admission.allergies:
            risk_factors.append({
                'factor': 'Known Allergies',
                'value': 'present',
                'impact': 'medium',
                'description': 'Patient has documented allergies requiring careful medication management'
            })
        
        return risk_factors
    
    def _calculate_risk_score(self, admission, risk_factors):
        """
        Calculate overall risk score (0-10 scale)
        """
        base_score = 2.0  # Base risk for any admission
        
        # Add risk based on factors
        for factor in risk_factors:
            if factor['impact'] == 'high':
                base_score += 2.0
            elif factor['impact'] == 'medium':
                base_score += 1.0
            else:
                base_score += 0.5
        
        # Add some randomness to simulate real AI model variability
        base_score += random.uniform(-0.5, 0.5)
        
        # Cap at 10.0
        return min(base_score, 10.0)
    
    def _generate_predictions(self, admission, risk_score):
        """
        Generate predictions based on risk analysis
        """
        predictions = {
            'length_of_stay_days': self._predict_length_of_stay(admission, risk_score),
            'complication_probability': min(risk_score * 0.1, 0.8),
            'readmission_risk_30_days': max(0.05, min(risk_score * 0.08, 0.4)),
            'estimated_cost_range': self._predict_cost_range(admission, risk_score),
            'recovery_timeline': self._predict_recovery_timeline(admission, risk_score)
        }
        
        return predictions
    
    def _generate_recommendations(self, admission, risk_score, risk_factors):
        """
        Generate AI-powered recommendations
        """
        recommendations = []
        
        if risk_score >= 7.0:
            recommendations.append({
                'type': 'monitoring',
                'priority': 'high',
                'action': 'Increase vital signs monitoring frequency',
                'rationale': 'High risk score indicates need for closer monitoring'
            })
            
            recommendations.append({
                'type': 'consultation',
                'priority': 'medium',
                'action': 'Consider specialist consultation',
                'rationale': 'Complex case may benefit from specialist input'
            })
        
        # Age-based recommendations
        age_factors = [f for f in risk_factors if f['factor'] == 'Advanced Age']
        if age_factors:
            recommendations.append({
                'type': 'geriatric_care',
                'priority': 'medium',
                'action': 'Implement fall prevention protocols',
                'rationale': 'Elderly patients have increased fall risk'
            })
        
        # Allergy-based recommendations
        allergy_factors = [f for f in risk_factors if f['factor'] == 'Known Allergies']
        if allergy_factors:
            recommendations.append({
                'type': 'medication',
                'priority': 'high',
                'action': 'Double-check all medications against allergy list',
                'rationale': 'Prevent allergic reactions'
            })
        
        # Emergency admission recommendations
        if admission.admission_type == 'emergency':
            recommendations.append({
                'type': 'assessment',
                'priority': 'medium',
                'action': 'Complete comprehensive medical assessment within 2 hours',
                'rationale': 'Emergency admissions require rapid assessment'
            })
        
        return recommendations
    
    def _determine_confidence_level(self, risk_score):
        """
        Determine confidence level based on available data
        """
        # In production, this would be based on model uncertainty
        if risk_score >= 7.0 or risk_score <= 2.0:
            return 'high'  # Extreme values are more confident
        elif risk_score >= 5.0 or risk_score <= 4.0:
            return 'medium'
        else:
            return 'low'
    
    def _predict_length_of_stay(self, admission, risk_score):
        """
        Predict expected length of stay
        """
        base_days = 3  # Base stay
        
        # Adjust based on admission type
        if admission.admission_type == 'emergency':
            base_days += 2
        elif admission.admission_type == 'elective':
            base_days -= 1
        
        # Adjust based on risk score
        base_days += int(risk_score * 0.5)
        
        return max(1, base_days)
    
    def _predict_cost_range(self, admission, risk_score):
        """
        Predict cost range for admission
        """
        base_cost = 5000  # Base cost
        
        # Adjust based on factors
        if admission.admission_type == 'emergency':
            base_cost *= 1.5
        
        # Adjust based on risk
        base_cost *= (1 + risk_score * 0.2)
        
        return {
            'minimum': int(base_cost * 0.8),
            'maximum': int(base_cost * 1.3),
            'expected': int(base_cost)
        }
    
    def _predict_recovery_timeline(self, admission, risk_score):
        """
        Predict recovery milestones
        """
        los_days = self._predict_length_of_stay(admission, risk_score)
        
        return {
            'stabilization': f"{max(1, int(los_days * 0.2))} days",
            'improvement': f"{max(2, int(los_days * 0.6))} days",
            'discharge_ready': f"{max(3, int(los_days * 0.9))} days"
        }
    
    def _generate_length_of_stay_prediction(self, admission):
        """
        Generate detailed length of stay prediction
        """
        current_los = admission.length_of_stay
        predicted_total = self._predict_length_of_stay(admission, admission.ai_risk_score)
        remaining_days = max(0, predicted_total - current_los)
        
        predictions = {
            'current_length_of_stay': current_los,
            'predicted_total_stay': predicted_total,
            'estimated_remaining_days': remaining_days,
            'discharge_probability_by_day': self._calculate_discharge_probabilities(remaining_days)
        }
        
        recommendations = []
        if remaining_days > 7:
            recommendations.append({
                'type': 'review',
                'action': 'Consider case review for extended stay',
                'priority': 'medium'
            })
        
        return AIPatientInsights.objects.create(
            admission=admission,
            patient=admission.patient,
            insight_type='length_of_stay',
            confidence_level='medium',
            prediction_data=predictions,
            recommendations=recommendations,
            risk_factors=[],
            risk_score=admission.ai_risk_score,
            accuracy_score=0.82,
            model_version=self.model_version
        )
    
    def _generate_readmission_risk(self, admission):
        """
        Generate readmission risk assessment
        """
        # Calculate readmission risk factors
        risk_factors = []
        risk_score = 3.0  # Base readmission risk
        
        # Age factor
        if hasattr(admission.patient, 'date_of_birth') and admission.patient.date_of_birth:
            age = self._calculate_age(admission.patient.date_of_birth)
            if age > 70:
                risk_score += 1.5
                risk_factors.append('Advanced age (>70)')
        
        # Length of stay factor
        if admission.length_of_stay > 7:
            risk_score += 1.0
            risk_factors.append('Extended length of stay')
        
        # Medical complexity
        if admission.medical_history and len(admission.medical_history) > 100:
            risk_score += 0.5
            risk_factors.append('Complex medical history')
        
        readmission_probability = min(risk_score * 0.08, 0.5)
        
        predictions = {
            'readmission_probability_7_days': readmission_probability * 0.3,
            'readmission_probability_30_days': readmission_probability,
            'high_risk_period': '7-14 days post-discharge',
            'risk_factors_count': len(risk_factors)
        }
        
        recommendations = []
        if readmission_probability > 0.2:
            recommendations.append({
                'type': 'follow_up',
                'action': 'Schedule follow-up within 48 hours',
                'priority': 'high'
            })
            recommendations.append({
                'type': 'education',
                'action': 'Provide comprehensive discharge education',
                'priority': 'medium'
            })
        
        return AIPatientInsights.objects.create(
            admission=admission,
            patient=admission.patient,
            insight_type='readmission_risk',
            confidence_level='medium',
            prediction_data=predictions,
            recommendations=recommendations,
            risk_factors=risk_factors,
            risk_score=risk_score,
            accuracy_score=0.79,
            model_version=self.model_version
        )
    
    def _generate_treatment_recommendations(self, admission):
        """
        Generate AI-powered treatment recommendations
        """
        recommendations = []
        
        # Based on current status
        if admission.current_status == 'critical':
            recommendations.append({
                'type': 'monitoring',
                'action': 'Continuous cardiac monitoring',
                'priority': 'critical',
                'evidence_level': 'high'
            })
        elif admission.current_status == 'stable':
            recommendations.append({
                'type': 'mobility',
                'action': 'Early mobilization if appropriate',
                'priority': 'medium',
                'evidence_level': 'moderate'
            })
        
        # Pain management
        recommendations.append({
            'type': 'pain_management',
            'action': 'Regular pain assessment using validated scales',
            'priority': 'medium',
            'evidence_level': 'high'
        })
        
        predictions = {
            'treatment_response_probability': 0.85,
            'optimal_treatment_duration': f"{self._predict_length_of_stay(admission, admission.ai_risk_score)} days",
            'recommended_interventions': len(recommendations)
        }
        
        return AIPatientInsights.objects.create(
            admission=admission,
            patient=admission.patient,
            insight_type='treatment_recommendation',
            confidence_level='medium',
            prediction_data=predictions,
            recommendations=recommendations,
            risk_factors=[],
            risk_score=admission.ai_risk_score,
            accuracy_score=0.83,
            model_version=self.model_version
        )
    
    def _calculate_age(self, birth_date):
        """
        Calculate age from birth date
        """
        today = timezone.now().date()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    def _calculate_discharge_probabilities(self, remaining_days):
        """
        Calculate probability of discharge by day
        """
        probabilities = {}
        total_prob = 0
        
        for day in range(1, min(remaining_days + 3, 15)):
            # Higher probability on predicted discharge day
            if day == remaining_days:
                prob = 0.4
            elif day == remaining_days - 1 or day == remaining_days + 1:
                prob = 0.2
            else:
                prob = 0.05
            
            total_prob += prob
            probabilities[f"day_{day}"] = prob
        
        # Normalize probabilities
        for day in probabilities:
            probabilities[day] = round(probabilities[day] / total_prob, 3)
        
        return probabilities
