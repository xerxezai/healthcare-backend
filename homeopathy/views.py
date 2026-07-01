from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg
from datetime import datetime, timedelta
import re
import json

from .models import HomeopathyPatient, HomeopathyRemedy, HomeopathyDiagnosis, HomeopathyRemedySuggestion
from .serializers import (
    HomeopathyPatientSerializer, HomeopathyRemedySerializer, 
    HomeopathyDiagnosisSerializer, DiagnosisCreateSerializer,
    AIAnalysisRequestSerializer, AIAnalysisResponseSerializer,
    HomeopathyRemedyListSerializer
)

class HomeopathyPatientViewSet(viewsets.ModelViewSet):
    queryset = HomeopathyPatient.objects.all()
    serializer_class = HomeopathyPatientSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return HomeopathyPatient.objects.filter(created_by=self.request.user)

class HomeopathyRemedyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = HomeopathyRemedy.objects.all()
    serializer_class = HomeopathyRemedySerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return HomeopathyRemedyListSerializer
        return HomeopathyRemedySerializer

class HomeopathyDiagnosisViewSet(viewsets.ModelViewSet):
    queryset = HomeopathyDiagnosis.objects.all()
    serializer_class = HomeopathyDiagnosisSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return HomeopathyDiagnosis.objects.filter(practitioner=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'create':
            return DiagnosisCreateSerializer
        return HomeopathyDiagnosisSerializer

class AIAnalysisView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Perform AI analysis on diagnosis data"""
        serializer = AIAnalysisRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        
        try:
            # Get or create patient
            patient = HomeopathyPatient.objects.get(
                id=data['patient_id'], 
                created_by=request.user
            )
        except HomeopathyPatient.DoesNotExist:
            return Response(
                {'error': 'Patient not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create diagnosis record
        diagnosis_data = data.copy()
        diagnosis_data.pop('patient_id')
        diagnosis_data['patient'] = patient
        diagnosis_data['practitioner'] = request.user
        diagnosis_data['status'] = 'analyzing'
        
        diagnosis = HomeopathyDiagnosis.objects.create(**diagnosis_data)
        
        # Perform AI analysis
        analysis_result = self.perform_ai_analysis(diagnosis, data)
        
        # Update diagnosis with analysis results
        diagnosis.ai_confidence = analysis_result['ai_confidence']
        diagnosis.suggested_constitution = analysis_result['suggested_constitution']
        diagnosis.suggested_miasm = analysis_result['suggested_miasm']
        diagnosis.mental_emotional_score = analysis_result['mental_emotional_score']
        diagnosis.physical_score = analysis_result['physical_score']
        diagnosis.modality_score = analysis_result['modality_score']
        diagnosis.estimated_duration = analysis_result['estimated_duration']
        diagnosis.suggested_potency = analysis_result['suggested_potency']
        diagnosis.suggested_frequency = analysis_result['suggested_frequency']
        diagnosis.follow_up_recommendations = analysis_result['follow_up_recommendations']
        diagnosis.status = 'completed'
        diagnosis.analyzed_at = datetime.now()
        diagnosis.save()
        
        # Create remedy suggestions
        for i, suggestion in enumerate(analysis_result['remedy_suggestions'], 1):
            HomeopathyRemedySuggestion.objects.create(
                diagnosis=diagnosis,
                remedy_id=suggestion['remedy_id'],
                confidence_score=suggestion['confidence_score'],
                keynote_match_score=suggestion['keynote_match_score'],
                mental_match_score=suggestion['mental_match_score'],
                physical_match_score=suggestion['physical_match_score'],
                constitutional_match_score=suggestion['constitutional_match_score'],
                suggested_potency=suggestion['suggested_potency'],
                suggested_frequency=suggestion['suggested_frequency'],
                duration=suggestion['duration'],
                ai_reasoning=suggestion['ai_reasoning'],
                matching_symptoms=suggestion['matching_symptoms'],
                rank=i
            )
        
        # Return analysis result
        response_data = analysis_result.copy()
        response_data['diagnosis_id'] = diagnosis.id
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    def perform_ai_analysis(self, diagnosis, data):
        """AI analysis engine for homeopathic diagnosis"""
        
        # Get all remedies for analysis
        remedies = HomeopathyRemedy.objects.all()
        remedy_scores = []
        
        # Analyze each remedy
        for remedy in remedies:
            score_data = self.analyze_remedy_match(remedy, data)
            if score_data['total_score'] > 20:  # Minimum threshold
                remedy_scores.append(score_data)
        
        # Sort by total score
        remedy_scores.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Take top 5 remedies
        top_remedies = remedy_scores[:5]
        
        # Determine constitution and miasm
        suggested_constitution = self.determine_constitution(data)
        suggested_miasm = self.determine_miasm(data)
        
        # Calculate overall confidence
        ai_confidence = self.calculate_confidence(data, top_remedies)
        
        # Generate treatment recommendations
        treatment_recommendations = self.generate_treatment_recommendations(
            suggested_constitution, suggested_miasm, data
        )
        
        return {
            'ai_confidence': ai_confidence,
            'suggested_constitution': suggested_constitution,
            'suggested_miasm': suggested_miasm,
            'mental_emotional_score': self.calculate_mental_score(data),
            'physical_score': self.calculate_physical_score(data),
            'modality_score': self.calculate_modality_score(data),
            'estimated_duration': treatment_recommendations['duration'],
            'suggested_potency': treatment_recommendations['potency'],
            'suggested_frequency': treatment_recommendations['frequency'],
            'follow_up_recommendations': treatment_recommendations['follow_up'],
            'remedy_suggestions': [
                {
                    'remedy_id': remedy['remedy'].id,
                    'confidence_score': remedy['total_score'],
                    'keynote_match_score': remedy['keynote_score'],
                    'mental_match_score': remedy['mental_score'],
                    'physical_match_score': remedy['physical_score'],
                    'constitutional_match_score': remedy['constitutional_score'],
                    'suggested_potency': remedy['suggested_potency'],
                    'suggested_frequency': remedy['suggested_frequency'],
                    'duration': remedy['duration'],
                    'ai_reasoning': remedy['reasoning'],
                    'matching_symptoms': remedy['matching_symptoms']
                }
                for remedy in top_remedies
            ]
        }
    
    def analyze_remedy_match(self, remedy, data):
        """Analyze how well a remedy matches the patient's symptoms"""
        
        # Initialize scores
        keynote_score = 0
        mental_score = 0
        physical_score = 0
        constitutional_score = 0
        matching_symptoms = []
        
        # Analyze keynotes
        if remedy.keynotes:
            for keynote in remedy.keynotes:
                if self.symptom_matches(keynote, data.get('primary_symptoms', '')):
                    keynote_score += 15
                    matching_symptoms.append(f"Keynote: {keynote}")
        
        # Analyze mental symptoms
        if remedy.mental_symptoms:
            mental_fields = ['mental_state', 'emotional_pattern', 'fears', 'anxieties', 'mood']
            for mental_symptom in remedy.mental_symptoms:
                for field in mental_fields:
                    if self.symptom_matches(mental_symptom, data.get(field, '')):
                        mental_score += 10
                        matching_symptoms.append(f"Mental: {mental_symptom}")
        
        # Analyze physical symptoms
        if remedy.physical_symptoms:
            physical_fields = ['appetite', 'thirst', 'sleep', 'dreams', 'thermals', 'perspiration']
            for physical_symptom in remedy.physical_symptoms:
                for field in physical_fields:
                    if self.symptom_matches(physical_symptom, data.get(field, '')):
                        physical_score += 8
                        matching_symptoms.append(f"Physical: {physical_symptom}")
        
        # Constitutional analysis
        if remedy.constitution_affinity:
            patient_constitution = self.determine_constitution(data)
            if patient_constitution in remedy.constitution_affinity:
                constitutional_score += 20
                matching_symptoms.append(f"Constitutional match: {patient_constitution}")
        
        # Calculate total score
        total_score = keynote_score + mental_score + physical_score + constitutional_score
        
        # Generate reasoning
        reasoning = self.generate_remedy_reasoning(
            remedy, keynote_score, mental_score, physical_score, constitutional_score
        )
        
        # Suggest potency and frequency
        potency_freq = self.suggest_potency_frequency(remedy, data)
        
        return {
            'remedy': remedy,
            'keynote_score': keynote_score,
            'mental_score': mental_score,
            'physical_score': physical_score,
            'constitutional_score': constitutional_score,
            'total_score': total_score,
            'matching_symptoms': matching_symptoms,
            'reasoning': reasoning,
            'suggested_potency': potency_freq['potency'],
            'suggested_frequency': potency_freq['frequency'],
            'duration': potency_freq['duration']
        }
    
    def symptom_matches(self, remedy_symptom, patient_data):
        """Check if remedy symptom matches patient data using fuzzy matching"""
        if not patient_data or not remedy_symptom:
            return False
        
        # Convert to lowercase for comparison
        remedy_words = set(re.findall(r'\w+', remedy_symptom.lower()))
        patient_words = set(re.findall(r'\w+', patient_data.lower()))
        
        # Check for word overlap
        overlap = remedy_words.intersection(patient_words)
        return len(overlap) >= 2  # At least 2 matching words
    
    def determine_constitution(self, data):
        """Determine constitutional type based on symptoms"""
        constitution_indicators = {
            'carbonic': ['calcium', 'bone', 'teeth', 'slow', 'steady', 'conservative'],
            'phosphoric': ['phosphorus', 'tall', 'lean', 'nervous', 'intellectual'],
            'fluoric': ['flexible', 'elastic', 'changeability', 'fluorine'],
            'sulphuric': ['warm', 'active', 'critical', 'philosophical'],
            'natrum': ['salt', 'emotional', 'reserved', 'grief'],
            'silica': ['delicate', 'refined', 'chilly', 'perfectionist'],
            'iron': ['strong', 'determined', 'anemic', 'iron'],
            'magnesium': ['restless', 'spasmodic', 'cramping']
        }
        
        constitution_scores = {}
        all_data = ' '.join([
            data.get('mental_state', ''),
            data.get('emotional_pattern', ''),
            data.get('energy', ''),
            data.get('thermals', ''),
            data.get('primary_symptoms', '')
        ]).lower()
        
        for constitution, indicators in constitution_indicators.items():
            score = sum(1 for indicator in indicators if indicator in all_data)
            constitution_scores[constitution] = score
        
        if constitution_scores:
            return max(constitution_scores, key=constitution_scores.get)
        return 'sulphuric'  # Default
    
    def determine_miasm(self, data):
        """Determine miasmatic tendency"""
        miasm_indicators = {
            'psoric': ['itching', 'eruption', 'dry', 'worse night'],
            'sycotic': ['warts', 'growths', 'humid', 'worse damp'],
            'syphilitic': ['destructive', 'ulceration', 'worse night'],
            'tubercular': ['restless', 'changeable', 'travel', 'fresh air'],
            'acute': ['sudden', 'violent', 'fever', 'inflammation']
        }
        
        miasm_scores = {}
        all_data = ' '.join([
            data.get('primary_symptoms', ''),
            data.get('worse_by', ''),
            data.get('better_by', ''),
            data.get('family_history', ''),
            data.get('past_illness', '')
        ]).lower()
        
        for miasm, indicators in miasm_indicators.items():
            score = sum(1 for indicator in indicators if indicator in all_data)
            miasm_scores[miasm] = score
        
        if miasm_scores:
            return max(miasm_scores, key=miasm_scores.get)
        return 'psoric'  # Default
    
    def calculate_confidence(self, data, top_remedies):
        """Calculate AI confidence based on data completeness and remedy scores"""
        # Data completeness score (0-50)
        required_fields = ['primary_symptoms', 'mental_state', 'better_by', 'worse_by']
        optional_fields = ['appetite', 'thirst', 'sleep', 'fears', 'anxieties']
        
        completeness = 0
        for field in required_fields:
            if data.get(field):
                completeness += 10
        
        for field in optional_fields:
            if data.get(field):
                completeness += 2
        
        # Remedy score confidence (0-50)
        remedy_confidence = 0
        if top_remedies:
            top_score = top_remedies[0]['total_score']
            if top_score > 80:
                remedy_confidence = 50
            elif top_score > 60:
                remedy_confidence = 40
            elif top_score > 40:
                remedy_confidence = 30
            else:
                remedy_confidence = 20
        
        return min(completeness + remedy_confidence, 100)
    
    def calculate_mental_score(self, data):
        """Calculate mental/emotional symptom strength"""
        mental_fields = ['mental_state', 'emotional_pattern', 'fears', 'anxieties', 'mood']
        score = 0
        for field in mental_fields:
            if data.get(field):
                score += len(data[field].split()) * 2
        return min(score, 100)
    
    def calculate_physical_score(self, data):
        """Calculate physical symptom strength"""
        physical_fields = ['appetite', 'thirst', 'sleep', 'dreams', 'thermals', 'perspiration']
        score = 0
        for field in physical_fields:
            if data.get(field):
                score += len(data[field].split()) * 2
        return min(score, 100)
    
    def calculate_modality_score(self, data):
        """Calculate modality strength"""
        modality_fields = ['better_by', 'worse_by', 'time_aggravation']
        score = 0
        for field in modality_fields:
            if data.get(field):
                score += len(data[field].split()) * 3
        return min(score, 100)
    
    def generate_treatment_recommendations(self, constitution, miasm, data):
        """Generate treatment recommendations"""
        severity = data.get('severity', 5)
        
        # Determine potency based on constitution and severity
        if constitution in ['phosphoric', 'sulphuric'] and severity > 7:
            potency = '200C'
        elif severity > 5:
            potency = '30C'
        else:
            potency = '6C'
        
        # Determine frequency based on severity and miasm
        if severity > 7:
            frequency = 'Twice daily'
        elif miasm == 'acute':
            frequency = 'Three times daily'
        else:
            frequency = 'Once daily'
        
        # Estimate duration
        if miasm == 'acute':
            duration = '3-5 days'
        elif severity > 7:
            duration = '1-2 weeks'
        else:
            duration = '2-4 weeks'
        
        # Follow-up recommendations
        follow_up = [
            'Monitor symptoms daily',
            'Follow-up consultation in 1 week',
            'Avoid coffee and strong odors',
            'Note any changes in mental state'
        ]
        
        if miasm in ['sycotic', 'syphilitic']:
            follow_up.append('Constitutional treatment may be needed')
        
        return {
            'potency': potency,
            'frequency': frequency,
            'duration': duration,
            'follow_up': follow_up
        }
    
    def generate_remedy_reasoning(self, remedy, keynote_score, mental_score, physical_score, constitutional_score):
        """Generate AI reasoning for remedy selection"""
        reasons = []
        
        if keynote_score > 0:
            reasons.append(f"Strong keynote symptom match (score: {keynote_score})")
        if mental_score > 0:
            reasons.append(f"Mental/emotional pattern alignment (score: {mental_score})")
        if physical_score > 0:
            reasons.append(f"Physical symptom correspondence (score: {physical_score})")
        if constitutional_score > 0:
            reasons.append(f"Constitutional type match (score: {constitutional_score})")
        
        total = keynote_score + mental_score + physical_score + constitutional_score
        
        if total > 80:
            confidence = "high"
        elif total > 50:
            confidence = "moderate"
        else:
            confidence = "low"
        
        reasoning = f"{remedy.name} shows {confidence} confidence match. " + "; ".join(reasons)
        
        if remedy.miasm:
            reasoning += f". Miasmatic classification: {remedy.miasm}."
        
        return reasoning
    
    def suggest_potency_frequency(self, remedy, data):
        """Suggest potency and frequency for specific remedy"""
        severity = data.get('severity', 5)
        
        # Default from remedy
        potencies = remedy.common_potencies.split(', ') if remedy.common_potencies else ['30C']
        
        if severity > 8:
            potency = '200C' if '200C' in potencies else potencies[-1]
            frequency = 'Once daily'
            duration = '3-5 days'
        elif severity > 5:
            potency = '30C' if '30C' in potencies else potencies[0]
            frequency = 'Twice daily'
            duration = '1 week'
        else:
            potency = '6C' if '6C' in potencies else potencies[0]
            frequency = 'Three times daily'
            duration = '2 weeks'
        
        return {
            'potency': potency,
            'frequency': frequency,
            'duration': duration
        }

class RemedySearchView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Search remedies by name or symptoms"""
        query = request.GET.get('q', '')
        
        if not query:
            return Response({'remedies': []})
        
        remedies = HomeopathyRemedy.objects.filter(
            Q(name__icontains=query) |
            Q(latin_name__icontains=query) |
            Q(common_name__icontains=query)
        )[:10]
        
        serializer = HomeopathyRemedyListSerializer(remedies, many=True)
        return Response({'remedies': serializer.data})

class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get dashboard statistics"""
        user = request.user
        
        # Patient stats
        total_patients = HomeopathyPatient.objects.filter(created_by=user).count()
        
        # Diagnosis stats
        total_diagnoses = HomeopathyDiagnosis.objects.filter(practitioner=user).count()
        recent_diagnoses = HomeopathyDiagnosis.objects.filter(
            practitioner=user,
            created_at__gte=datetime.now() - timedelta(days=30)
        ).count()
        
        # Success rate (completed diagnoses)
        completed_diagnoses = HomeopathyDiagnosis.objects.filter(
            practitioner=user,
            status='completed'
        ).count()
        
        success_rate = (completed_diagnoses / total_diagnoses * 100) if total_diagnoses > 0 else 0
        
        # Average AI confidence
        avg_confidence = HomeopathyDiagnosis.objects.filter(
            practitioner=user,
            status='completed'
        ).aggregate(avg_confidence=Avg('ai_confidence'))['avg_confidence'] or 0
        
        return Response({
            'total_patients': total_patients,
            'total_diagnoses': total_diagnoses,
            'recent_diagnoses': recent_diagnoses,
            'success_rate': round(success_rate, 1),
            'avg_confidence': round(avg_confidence, 1),
            'total_remedies': HomeopathyRemedy.objects.count()
        })
