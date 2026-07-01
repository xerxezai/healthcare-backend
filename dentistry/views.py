from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import datetime, timedelta
import json
import random
import base64

from subscriptions.permissions import SuperAdminPermission, SubscriptionOrSuperAdminPermission
from .services.cancer_report_generator import CancerDetectionReportGenerator

from .models import (
    Patient, Dentist, DentalHistory, Appointment, Treatment,
    DentalXray, PeriodontalChart, DentalAIAnalysis, Prescription,
    DentalEmergency, TreatmentPlan, CancerDetection, CancerDetectionImage,
    CancerDetectionAcknowledgment, CancerRiskAssessment, CancerTreatmentPlan,
    CancerNotification
)
from .serializers import (
    PatientSerializer, DentistSerializer, DentalHistorySerializer,
    AppointmentSerializer, TreatmentSerializer, DentalXraySerializer,
    PeriodontalChartSerializer, DentalAIAnalysisSerializer,
    PrescriptionSerializer, DentalEmergencySerializer,
    TreatmentPlanSerializer, DashboardStatsSerializer,
    AppointmentCalendarSerializer, PatientSummarySerializer,
    CancerDetectionSerializer, CancerDetectionImageSerializer,
    CancerDetectionAcknowledgmentSerializer, CancerRiskAssessmentSerializer,
    CancerTreatmentPlanSerializer, CancerNotificationSerializer
)

class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [SubscriptionOrSuperAdminPermission]

    def get_queryset(self):
        queryset = Patient.objects.all().select_related('user')
        patient_id = self.request.query_params.get('patient_id', None)
        if patient_id:
            queryset = queryset.filter(patient_id__icontains=patient_id)
        return queryset

    def create(self, request, *args, **kwargs):
        """Custom create method to handle patient creation"""
        data = request.data.copy()
        
        # Generate unique patient ID if not provided
        if 'patient_id' not in data or not data['patient_id']:
            patient_count = Patient.objects.count() + 1
            data['patient_id'] = f"DENT{patient_count:06d}"
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Create the patient
        patient = serializer.save()
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=True, methods=['get'])
    def dental_history(self, request, pk=None):
        patient = self.get_object()
        try:
            history = patient.dental_history
            serializer = DentalHistorySerializer(history)
            return Response(serializer.data)
        except DentalHistory.DoesNotExist:
            return Response({'message': 'No dental history found'}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=['get'])
    def appointments(self, request, pk=None):
        patient = self.get_object()
        appointments = patient.appointments.all()
        serializer = AppointmentSerializer(appointments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def treatments(self, request, pk=None):
        patient = self.get_object()
        treatments = patient.treatments.all()
        serializer = TreatmentSerializer(treatments, many=True)
        return Response(serializer.data)

class DentistViewSet(viewsets.ModelViewSet):
    queryset = Dentist.objects.all()
    serializer_class = DentistSerializer
    permission_classes = [SubscriptionOrSuperAdminPermission]

    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        dentist = self.get_object()
        date_str = request.query_params.get('date', None)
        
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
                appointments = dentist.appointments.filter(
                    appointment_date__date=target_date
                ).order_by('appointment_date')
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD'}, 
                              status=status.HTTP_400_BAD_REQUEST)
        else:
            # Get today's appointments
            appointments = dentist.appointments.filter(
                appointment_date__date=timezone.now().date()
            ).order_by('appointment_date')

        serializer = AppointmentCalendarSerializer(appointments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def patients(self, request, pk=None):
        dentist = self.get_object()
        patients = Patient.objects.filter(appointments__dentist=dentist).distinct()
        serializer = PatientSummarySerializer(patients, many=True)
        return Response(serializer.data)

class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [SubscriptionOrSuperAdminPermission]

    def get_queryset(self):
        queryset = Appointment.objects.all()
        status_filter = self.request.query_params.get('status', None)
        date_filter = self.request.query_params.get('date', None)
        dentist_filter = self.request.query_params.get('dentist', None)

        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if date_filter:
            queryset = queryset.filter(appointment_date__date=date_filter)
        if dentist_filter:
            queryset = queryset.filter(dentist_id=dentist_filter)

        return queryset.order_by('-appointment_date')

    @action(detail=False, methods=['get'])
    def calendar(self, request):
        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')
        
        if not start_date or not end_date:
            return Response({'error': 'start and end dates are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        appointments = self.queryset.filter(
            appointment_date__date__range=[start_date, end_date]
        )
        serializer = AppointmentCalendarSerializer(appointments, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        appointment = self.get_object()
        appointment.status = 'confirmed'
        appointment.save()
        return Response({'message': 'Appointment confirmed'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        appointment.status = 'cancelled'
        appointment.save()
        return Response({'message': 'Appointment cancelled'})

class TreatmentViewSet(viewsets.ModelViewSet):
    queryset = Treatment.objects.all()
    serializer_class = TreatmentSerializer
    permission_classes = [SubscriptionOrSuperAdminPermission]

    @action(detail=False, methods=['post'])
    def ai_recommendation(self, request):
        """AI-powered treatment recommendation endpoint"""
        import time
        import random
        
        patient_id = request.data.get('patient_id')
        symptoms = request.data.get('symptoms', '')
        diagnosis = request.data.get('diagnosis', '')
        medical_history = request.data.get('medical_history', '')
        
        if not patient_id:
            return Response({'error': 'patient_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Simulate AI processing time
        processing_start = time.time()
        
        # Mock AI treatment recommendations based on symptoms and diagnosis
        treatment_options = []
        
        # Base treatments based on common dental conditions
        if 'cavity' in symptoms.lower() or 'tooth decay' in diagnosis.lower():
            treatment_options.extend([
                {
                    'treatment_name': 'Composite Filling',
                    'treatment_code': 'D2391',
                    'priority': 'high',
                    'estimated_cost': random.randint(150, 350),
                    'success_rate': random.uniform(85, 95),
                    'duration': '1 hour',
                    'description': 'Direct restoration with tooth-colored composite material'
                },
                {
                    'treatment_name': 'Amalgam Filling',
                    'treatment_code': 'D2140',
                    'priority': 'medium',
                    'estimated_cost': random.randint(100, 250),
                    'success_rate': random.uniform(80, 90),
                    'duration': '45 minutes',
                    'description': 'Traditional silver filling material'
                }
            ])
        
        if 'pain' in symptoms.lower() or 'root canal' in diagnosis.lower():
            treatment_options.append({
                'treatment_name': 'Root Canal Therapy',
                'treatment_code': 'D3310',
                'priority': 'urgent',
                'estimated_cost': random.randint(800, 1500),
                'success_rate': random.uniform(85, 95),
                'duration': '2-3 hours',
                'description': 'Endodontic treatment to save infected tooth'
            })
        
        if 'gum' in symptoms.lower() or 'periodontal' in diagnosis.lower():
            treatment_options.extend([
                {
                    'treatment_name': 'Deep Cleaning (SRP)',
                    'treatment_code': 'D4341',
                    'priority': 'high',
                    'estimated_cost': random.randint(200, 400),
                    'success_rate': random.uniform(75, 85),
                    'duration': '1-2 hours',
                    'description': 'Scaling and root planing for gum disease'
                },
                {
                    'treatment_name': 'Periodontal Maintenance',
                    'treatment_code': 'D4910',
                    'priority': 'medium',
                    'estimated_cost': random.randint(100, 200),
                    'success_rate': random.uniform(80, 90),
                    'duration': '1 hour',
                    'description': 'Ongoing periodontal care'
                }
            ])
        
        # Default recommendations if no specific conditions detected
        if not treatment_options:
            treatment_options.extend([
                {
                    'treatment_name': 'Comprehensive Exam',
                    'treatment_code': 'D0150',
                    'priority': 'routine',
                    'estimated_cost': random.randint(75, 150),
                    'success_rate': 100,
                    'duration': '30 minutes',
                    'description': 'Thorough dental examination and assessment'
                },
                {
                    'treatment_name': 'Prophylaxis (Cleaning)',
                    'treatment_code': 'D1110',
                    'priority': 'routine',
                    'estimated_cost': random.randint(80, 120),
                    'success_rate': 100,
                    'duration': '45 minutes',
                    'description': 'Professional dental cleaning'
                }
            ])
        
        # AI risk assessment
        risk_factors = []
        if 'diabetes' in medical_history.lower():
            risk_factors.append('Diabetes increases risk of gum disease')
        if 'smoking' in medical_history.lower():
            risk_factors.append('Smoking affects healing and treatment success')
        if 'heart disease' in medical_history.lower():
            risk_factors.append('Cardiac conditions may require antibiotic prophylaxis')
        
        # Alternative treatments
        alternative_options = [
            'Conservative monitoring with regular check-ups',
            'Lifestyle modifications and improved oral hygiene',
            'Referral to specialist if condition is complex'
        ]
        
        processing_time = time.time() - processing_start
        
        ai_recommendation = {
            'patient_id': patient_id,
            'recommended_treatments': treatment_options,
            'risk_assessment': {
                'overall_risk': random.choice(['low', 'moderate', 'high']),
                'risk_factors': risk_factors,
                'success_probability': random.uniform(70, 95)
            },
            'alternative_options': alternative_options,
            'urgency_level': random.choice(['routine', 'priority', 'urgent']),
            'follow_up_required': random.choice([True, False]),
            'specialist_referral': random.choice([False, False, True]),  # 33% chance
            'ai_confidence': random.uniform(0.75, 0.95),
            'processing_time': round(processing_time, 3),
            'generated_at': timezone.now().isoformat()
        }
        
        return Response(ai_recommendation, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        treatment = self.get_object()
        treatment.status = 'completed'
        treatment.completion_date = timezone.now().date()
        treatment.save()
        return Response({'message': 'Treatment marked as completed'})

class DentalAIAnalysisViewSet(viewsets.ModelViewSet):
    queryset = DentalAIAnalysis.objects.all()
    serializer_class = DentalAIAnalysisSerializer
    permission_classes = [SubscriptionOrSuperAdminPermission]

    @action(detail=False, methods=['post'])
    def analyze_xray(self, request):
        """AI-powered X-ray analysis endpoint"""
        # Mock AI analysis - in real implementation, this would use actual AI models
        import time
        import random
        
        patient_id = request.data.get('patient_id')
        dentist_id = request.data.get('dentist_id')
        analysis_type = request.data.get('analysis_type', 'xray_analysis')
        
        if not patient_id or not dentist_id:
            return Response({'error': 'patient_id and dentist_id are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Simulate AI processing time
        processing_start = time.time()
        
        # Mock AI findings
        mock_findings = {
            'cavities_detected': random.randint(0, 3),
            'bone_loss_percentage': round(random.uniform(0, 25), 2),
            'root_canal_needed': random.choice([True, False]),
            'wisdom_teeth_present': random.choice([True, False]),
            'overall_oral_health': random.choice(['excellent', 'good', 'fair', 'poor'])
        }
        
        mock_conditions = [
            {'name': 'Dental Caries', 'probability': random.uniform(0.1, 0.9)},
            {'name': 'Periodontal Disease', 'probability': random.uniform(0.1, 0.7)},
            {'name': 'Impacted Tooth', 'probability': random.uniform(0.0, 0.5)},
        ]
        
        mock_suggestions = [
            'Regular dental cleaning recommended',
            'Consider fluoride treatment',
            'Monitor suspicious areas in 6 months',
            'Patient education on oral hygiene'
        ]
        
        processing_time = time.time() - processing_start
        
        # Create AI analysis record
        analysis = DentalAIAnalysis.objects.create(
            patient_id=patient_id,
            dentist_id=dentist_id,
            analysis_type=analysis_type,
            ai_findings=mock_findings,
            confidence_level=random.choice(['moderate', 'high', 'very_high']),
            risk_score=random.uniform(10, 80),
            detected_conditions=mock_conditions,
            treatment_suggestions=mock_suggestions,
            processing_time=processing_time
        )
        
        serializer = DentalAIAnalysisSerializer(analysis)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Dentist approval of AI analysis"""
        analysis = self.get_object()
        analysis.approved_by_dentist = True
        analysis.dentist_review = request.data.get('review', '')
        analysis.clinical_notes = request.data.get('clinical_notes', '')
        analysis.save()
        return Response({'message': 'AI analysis approved'})

class DentalEmergencyViewSet(viewsets.ModelViewSet):
    queryset = DentalEmergency.objects.all()
    serializer_class = DentalEmergencySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        queryset = DentalEmergency.objects.all()
        if self.request.query_params.get('unresolved'):
            queryset = queryset.filter(is_resolved=False)
        return queryset.order_by('-created_at')

    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        emergency = self.get_object()
        emergency.is_resolved = True
        emergency.resolution_notes = request.data.get('resolution_notes', '')
        emergency.save()
        return Response({'message': 'Emergency case resolved'})

class TreatmentPlanViewSet(viewsets.ModelViewSet):
    queryset = TreatmentPlan.objects.all()
    serializer_class = TreatmentPlanSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        plan = self.get_object()
        plan.patient_approved = True
        plan.patient_approval_date = timezone.now()
        plan.status = 'approved'
        plan.save()
        return Response({'message': 'Treatment plan approved'})

    @action(detail=False, methods=['post'])
    def generate_ai_plan(self, request):
        """AI-assisted treatment planning"""
        patient_id = request.data.get('patient_id')
        dentist_id = request.data.get('dentist_id')
        chief_complaint = request.data.get('chief_complaint', '')
        
        if not patient_id or not dentist_id:
            return Response({'error': 'patient_id and dentist_id are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)

        # Mock AI treatment planning
        mock_ai_assessment = {
            'risk_factors': ['Age', 'Smoking history', 'Poor oral hygiene'],
            'predicted_outcomes': {
                'success_probability': random.uniform(0.7, 0.95),
                'healing_time': f"{random.randint(2, 8)} weeks",
                'complications_risk': random.uniform(0.05, 0.20)
            },
            'cost_optimization': {
                'alternative_treatments': ['Option A', 'Option B'],
                'insurance_coverage_estimate': random.uniform(0.6, 0.9)
            }
        }
        
        mock_suggestions = [
            'Phase 1: Emergency care and pain management',
            'Phase 2: Periodontal therapy and disease control',
            'Phase 3: Restorative treatment',
            'Phase 4: Maintenance and follow-up'
        ]
        
        # Create treatment plan with AI enhancement
        plan = TreatmentPlan.objects.create(
            patient_id=patient_id,
            primary_dentist_id=dentist_id,
            plan_name=f"AI-Generated Plan - {timezone.now().strftime('%Y%m%d')}",
            description="Comprehensive treatment plan generated with AI assistance",
            chief_complaint=chief_complaint,
            ai_risk_assessment=mock_ai_assessment,
            ai_treatment_suggestions=mock_suggestions,
            total_estimated_cost=random.uniform(1000, 5000),
            patient_portion=random.uniform(500, 2000),
            estimated_duration=random.randint(4, 16),
            start_date=timezone.now().date(),
            estimated_completion=timezone.now().date() + timedelta(weeks=random.randint(4, 16))
        )
        
        serializer = TreatmentPlanSerializer(plan)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class DashboardViewSet(viewsets.ViewSet):
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get dashboard statistics"""
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        
        stats = {
            'total_patients': Patient.objects.count(),
            'total_appointments': Appointment.objects.count(),
            'todays_appointments': Appointment.objects.filter(
                appointment_date__date=today
            ).count(),
            'pending_treatments': Treatment.objects.filter(
                status__in=['planned', 'in_progress']
            ).count(),
            'emergency_cases': DentalEmergency.objects.filter(
                is_resolved=False
            ).count(),
            'ai_analyses_today': DentalAIAnalysis.objects.filter(
                created_at__date=today
            ).count(),
            'revenue_this_month': Treatment.objects.filter(
                completion_date__gte=this_month_start,
                status='completed'
            ).aggregate(Sum('patient_payment'))['patient_payment__sum'] or 0,
            'patient_satisfaction': 4.5  # Mock rating
        }
        
        serializer = DashboardStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent_activities(self, request):
        """Get recent activities for dashboard"""
        recent_appointments = Appointment.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:10]
        
        recent_treatments = Treatment.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:10]
        
        recent_ai_analyses = DentalAIAnalysis.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:10]
        
        return Response({
            'recent_appointments': AppointmentSerializer(recent_appointments, many=True).data,
            'recent_treatments': TreatmentSerializer(recent_treatments, many=True).data,
            'recent_ai_analyses': DentalAIAnalysisSerializer(recent_ai_analyses, many=True).data
        })


# Cancer Detection ViewSets
class CancerDetectionViewSet(viewsets.ModelViewSet):
    queryset = CancerDetection.objects.all()
    serializer_class = CancerDetectionSerializer
    permission_classes = [SubscriptionOrSuperAdminPermission]

    def get_queryset(self):
        queryset = CancerDetection.objects.select_related(
            'patient__user', 'dentist__user', 'reviewed_by__user'
        ).prefetch_related('images', 'notifications')
        
        # Filter by patient if specified
        patient_id = self.request.query_params.get('patient_id', None)
        if patient_id:
            queryset = queryset.filter(patient__patient_id=patient_id)
        
        # Filter by risk level
        risk_level = self.request.query_params.get('risk_level', None)
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        
        # Filter by status
        status = self.request.query_params.get('status', None)
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-detected_at')

    @action(detail=False, methods=['get'])
    def active_alerts(self, request):
        """Get active cancer detection alerts"""
        active_detections = self.get_queryset().filter(
            cancer_detected=True,
            status__in=['pending_review', 'under_review', 'requires_biopsy']
        )
        serializer = self.get_serializer(active_detections, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def high_risk_patients(self, request):
        """Get patients with high cancer risk"""
        high_risk_detections = self.get_queryset().filter(
            risk_level__in=['high', 'critical']
        )
        serializer = self.get_serializer(high_risk_detections, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def acknowledge(self, request, pk=None):
        """Acknowledge a cancer detection alert"""
        detection = self.get_object()
        dentist_id = request.data.get('dentist_id')
        
        if not dentist_id:
            return Response(
                {'error': 'dentist_id is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            dentist = Dentist.objects.get(id=dentist_id)
            acknowledgment, created = CancerDetectionAcknowledgment.objects.get_or_create(
                cancer_detection=detection,
                dentist=dentist,
                defaults={
                    'acknowledgment_method': request.data.get('method', 'dashboard'),
                    'notes': request.data.get('notes', ''),
                    'action_taken': request.data.get('action_taken', '')
                }
            )
            
            if not created:
                # Update existing acknowledgment
                acknowledgment.notes = request.data.get('notes', acknowledgment.notes)
                acknowledgment.action_taken = request.data.get('action_taken', acknowledgment.action_taken)
                acknowledgment.save()
            
            serializer = CancerDetectionAcknowledgmentSerializer(acknowledgment)
            return Response(serializer.data)
            
        except Dentist.DoesNotExist:
            return Response(
                {'error': 'Dentist not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )

    @action(detail=True, methods=['get'])
    def generate_pdf_report(self, request, pk=None):
        """Generate comprehensive PDF report for cancer detection"""
        detection = self.get_object()
        
        try:
            # Generate the PDF report
            report_generator = CancerDetectionReportGenerator()
            pdf_buffer = report_generator.generate_comprehensive_report(detection)
            
            # Create response with PDF
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            filename = f"Cancer_Detection_Report_{detection.detection_id}_{detection.detected_at.strftime('%Y%m%d')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate PDF report: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def preview_pdf_report(self, request, pk=None):
        """Preview PDF report in browser"""
        detection = self.get_object()
        
        try:
            # Generate the PDF report
            report_generator = CancerDetectionReportGenerator()
            pdf_buffer = report_generator.generate_comprehensive_report(detection)
            
            # Create response for inline viewing
            response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
            filename = f"Cancer_Detection_Report_{detection.detection_id}_{detection.detected_at.strftime('%Y%m%d')}.pdf"
            response['Content-Disposition'] = f'inline; filename="{filename}"'
            
            return response
            
        except Exception as e:
            return Response(
                {'error': f'Failed to generate PDF report: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=['post'])
    def bulk_generate_reports(self, request):
        """Generate PDF reports for multiple cancer detections"""
        detection_ids = request.data.get('detection_ids', [])
        
        if not detection_ids:
            return Response(
                {'error': 'detection_ids list is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            reports = []
            report_generator = CancerDetectionReportGenerator()
            
            for detection_id in detection_ids:
                try:
                    detection = CancerDetection.objects.get(detection_id=detection_id)
                    pdf_buffer = report_generator.generate_comprehensive_report(detection)
                    
                    # Convert to base64 for JSON response
                    pdf_b64 = base64.b64encode(pdf_buffer.getvalue()).decode('utf-8')
                    filename = f"Cancer_Detection_Report_{detection.detection_id}_{detection.detected_at.strftime('%Y%m%d')}.pdf"
                    
                    reports.append({
                        'detection_id': str(detection.detection_id),
                        'filename': filename,
                        'pdf_data': pdf_b64,
                        'patient_name': detection.patient.user.get_full_name(),
                        'detection_date': detection.detected_at.isoformat()
                    })
                    
                except CancerDetection.DoesNotExist:
                    reports.append({
                        'detection_id': detection_id,
                        'error': 'Cancer detection not found'
                    })
                except Exception as e:
                    reports.append({
                        'detection_id': detection_id,
                        'error': f'Failed to generate report: {str(e)}'
                    })
            
            return Response({
                'reports': reports,
                'total_requested': len(detection_ids),
                'successful': len([r for r in reports if 'pdf_data' in r]),
                'failed': len([r for r in reports if 'error' in r])
            })
            
        except Exception as e:
            return Response(
                {'error': f'Bulk report generation failed: {str(e)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CancerDetectionImageViewSet(viewsets.ModelViewSet):
    queryset = CancerDetectionImage.objects.all()
    serializer_class = CancerDetectionImageSerializer
    permission_classes = [SubscriptionOrSuperAdminPermission]

    def get_queryset(self):
        queryset = CancerDetectionImage.objects.select_related('cancer_detection')
        
        # Filter by cancer detection
        detection_id = self.request.query_params.get('detection_id', None)
        if detection_id:
            queryset = queryset.filter(cancer_detection__detection_id=detection_id)
        
        return queryset.order_by('-uploaded_at')


class CancerRiskAssessmentViewSet(viewsets.ModelViewSet):
    queryset = CancerRiskAssessment.objects.all()
    serializer_class = CancerRiskAssessmentSerializer
    permission_classes = [SubscriptionOrSuperAdminPermission]

    def get_queryset(self):
        queryset = CancerRiskAssessment.objects.select_related(
            'patient__user', 'dentist__user'
        )
        
        # Filter by patient
        patient_id = self.request.query_params.get('patient_id', None)
        if patient_id:
            queryset = queryset.filter(patient__patient_id=patient_id)
        
        return queryset.order_by('-assessment_date')


class CancerTreatmentPlanViewSet(viewsets.ModelViewSet):
    queryset = CancerTreatmentPlan.objects.all()
    serializer_class = CancerTreatmentPlanSerializer
    permission_classes = [SubscriptionOrSuperAdminPermission]

    def get_queryset(self):
        queryset = CancerTreatmentPlan.objects.select_related(
            'cancer_detection__patient__user', 'primary_dentist__user'
        )
        
        # Filter by patient
        patient_id = self.request.query_params.get('patient_id', None)
        if patient_id:
            queryset = queryset.filter(cancer_detection__patient__patient_id=patient_id)
        
        return queryset.order_by('-created_at')


class CancerNotificationViewSet(viewsets.ModelViewSet):
    queryset = CancerNotification.objects.all()
    serializer_class = CancerNotificationSerializer
    permission_classes = [SubscriptionOrSuperAdminPermission]

    def get_queryset(self):
        queryset = CancerNotification.objects.select_related(
            'cancer_detection__patient__user', 'patient__user'
        ).prefetch_related('recipient_dentists')
        
        # Filter by priority
        priority = self.request.query_params.get('priority', None)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-created_at')

    @action(detail=False, methods=['get'])
    def unread_notifications(self, request):
        """Get unread notifications"""
        unread = self.get_queryset().filter(
            status__in=['pending', 'sent', 'delivered']
        )
        serializer = self.get_serializer(unread, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        """Mark notification as read"""
        notification = self.get_object()
        notification.status = 'read'
        notification.read_at = timezone.now()
        notification.save()
        
        serializer = self.get_serializer(notification)
        return Response(serializer.data)


# S3 Data Management Views
from .models import DentistryInstitution, DentistryPatient, DentistryFile, DentistryAnalysis
from .services.s3_data_manager import dentistry_s3_manager

class DentistryInstitutionViewSet(viewsets.ModelViewSet):
    """API endpoints for managing dental institutions"""
    queryset = DentistryInstitution.objects.all()
    permission_classes = [SubscriptionOrSuperAdminPermission]
    
    def get_serializer_class(self):
        from rest_framework import serializers
        
        class DentistryInstitutionSerializer(serializers.ModelSerializer):
            class Meta:
                model = DentistryInstitution
                fields = '__all__'
        
        return DentistryInstitutionSerializer
    
    @action(detail=True, methods=['get'])
    def files(self, request, pk=None):
        """Get files for a specific institution"""
        institution = self.get_object()
        files = DentistryFile.objects.filter(institution=institution)
        
        file_data = []
        for file_obj in files:
            file_data.append({
                'id': file_obj.id,
                'name': file_obj.name,
                'file_type': file_obj.file_type,
                's3_url': file_obj.s3_url,
                'size': file_obj.size,
                'created_at': file_obj.created_at
            })
        
        return Response({'files': file_data})


class DentistryPatientViewSet(viewsets.ModelViewSet):
    """API endpoints for managing dental patients in S3 system"""
    queryset = DentistryPatient.objects.all()
    permission_classes = [SubscriptionOrSuperAdminPermission]
    
    def get_serializer_class(self):
        from rest_framework import serializers
        
        class DentistryPatientSerializer(serializers.ModelSerializer):
            institution_name = serializers.CharField(source='institution.name', read_only=True)
            
            class Meta:
                model = DentistryPatient
                fields = '__all__'
        
        return DentistryPatientSerializer
    
    @action(detail=True, methods=['get'])
    def files(self, request, pk=None):
        """Get files for a specific patient"""
        patient = self.get_object()
        files = DentistryFile.objects.filter(patient=patient)
        
        file_data = []
        for file_obj in files:
            file_data.append({
                'id': file_obj.id,
                'name': file_obj.name,
                'file_type': file_obj.file_type,
                's3_url': file_obj.s3_url,
                'size': file_obj.size,
                'created_at': file_obj.created_at
            })
        
        return Response({'files': file_data})
    
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Get patient history including files and analyses"""
        patient = self.get_object()
        files = DentistryFile.objects.filter(patient=patient)
        analyses = DentistryAnalysis.objects.filter(file__patient=patient)
        
        return Response({
            'patient': self.get_serializer(patient).data,
            'files_count': files.count(),
            'analyses_count': analyses.count(),
            'recent_files': [
                {
                    'id': f.id,
                    'name': f.name,
                    'file_type': f.file_type,
                    'created_at': f.created_at
                } for f in files.order_by('-created_at')[:5]
            ]
        })


class DentistryFileViewSet(viewsets.ModelViewSet):
    """API endpoints for managing dental files"""
    queryset = DentistryFile.objects.all()
    permission_classes = [SubscriptionOrSuperAdminPermission]
    
    def get_serializer_class(self):
        from rest_framework import serializers
        
        class DentistryFileSerializer(serializers.ModelSerializer):
            institution_name = serializers.CharField(source='institution.name', read_only=True)
            patient_name = serializers.CharField(source='patient.full_name', read_only=True)
            
            class Meta:
                model = DentistryFile
                fields = '__all__'
        
        return DentistryFileSerializer
    
    def create(self, request, *args, **kwargs):
        """Handle file upload to S3"""
        try:
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                return Response(
                    {'error': 'No file provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Extract parameters
            institution_id = request.data.get('institution_id')
            patient_id = request.data.get('patient_id')
            file_type = request.data.get('file_type', 'general')
            
            # Upload to S3
            result = dentistry_s3_manager.upload_dental_file(
                uploaded_file,
                institution_id=institution_id,
                patient_id=patient_id,
                file_type=file_type
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'file_id': result['file_id'],
                    's3_url': result['s3_url'],
                    'message': 'File uploaded successfully'
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': result['error']},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'])
    def download(self, request, pk=None):
        """Generate presigned URL for file download"""
        file_obj = self.get_object()
        presigned_url = dentistry_s3_manager.generate_presigned_url(file_obj.s3_key)
        
        if presigned_url:
            return Response({'download_url': presigned_url})
        else:
            return Response(
                {'error': 'Failed to generate download URL'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def destroy(self, request, *args, **kwargs):
        """Delete file from S3 and database"""
        file_obj = self.get_object()
        
        # Delete from S3
        success = dentistry_s3_manager.delete_dental_file(file_obj.s3_key, file_obj.id)
        
        if success:
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            return Response(
                {'error': 'Failed to delete file'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DentistryAnalysisViewSet(viewsets.ModelViewSet):
    """API endpoints for AI analysis of dental files"""
    queryset = DentistryAnalysis.objects.all()
    permission_classes = [SubscriptionOrSuperAdminPermission]
    
    def get_serializer_class(self):
        from rest_framework import serializers
        
        class DentistryAnalysisSerializer(serializers.ModelSerializer):
            file_name = serializers.CharField(source='file.name', read_only=True)
            
            class Meta:
                model = DentistryAnalysis
                fields = '__all__'
        
        return DentistryAnalysisSerializer


class DentistryS3ManagementViewSet(viewsets.ViewSet):
    """API endpoints for S3 data management operations"""
    permission_classes = [SubscriptionOrSuperAdminPermission]
    
    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload files to S3"""
        return DentistryFileViewSet().create(request)
    
    @action(detail=False, methods=['post'])
    def bulk_upload(self, request):
        """Handle bulk file upload"""
        try:
            files = request.FILES.getlist('files')
            if not files:
                return Response(
                    {'error': 'No files provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            institution_id = request.data.get('institution_id')
            patient_id = request.data.get('patient_id')
            file_type = request.data.get('file_type', 'general')
            
            results = []
            for uploaded_file in files:
                result = dentistry_s3_manager.upload_dental_file(
                    uploaded_file,
                    institution_id=institution_id,
                    patient_id=patient_id,
                    file_type=file_type
                )
                results.append({
                    'filename': uploaded_file.name,
                    'success': result['success'],
                    'file_id': result.get('file_id'),
                    'error': result.get('error')
                })
            
            return Response({'results': results})
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def analyze(self, request):
        """Perform AI analysis on uploaded file"""
        try:
            file_id = request.data.get('file_id')
            analysis_type = request.data.get('analysis_type')
            
            if not file_id or not analysis_type:
                return Response(
                    {'error': 'file_id and analysis_type are required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create analysis record
            file_obj = DentistryFile.objects.get(id=file_id)
            analysis = DentistryAnalysis.objects.create(
                file=file_obj,
                analysis_type=analysis_type,
                status='processing',
                analyzed_by=request.user
            )
            
            # Simulate AI analysis (replace with actual AI service)
            import time
            time.sleep(2)  # Simulate processing time
            
            # Mock results
            mock_results = {
                'findings': f'Analysis completed for {analysis_type}',
                'recommendations': 'Follow up recommended',
                'severity': 'low',
                'processed_at': timezone.now().isoformat()
            }
            
            analysis.status = 'completed'
            analysis.confidence_score = 0.85
            analysis.results = mock_results
            analysis.save()
            
            return Response({
                'analysis_id': analysis.id,
                'status': analysis.status,
                'confidence': analysis.confidence_score,
                'results': analysis.results
            })
            
        except DentistryFile.DoesNotExist:
            return Response(
                {'error': 'File not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def status(self, request):
        """Get S3 storage status and analytics"""
        try:
            analytics = dentistry_s3_manager.get_storage_analytics()
            return Response(analytics)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def sync(self, request):
        """Synchronize S3 files with database"""
        try:
            sync_result = dentistry_s3_manager.sync_files_with_database()
            return Response(sync_result)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def cleanup(self, request):
        """Cleanup old files from S3"""
        try:
            days_old = int(request.data.get('days_old', 90))
            cleanup_result = dentistry_s3_manager.cleanup_old_files(days_old)
            return Response(cleanup_result)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """Get detailed analytics for dentistry data"""
        try:
            # Get basic analytics
            analytics = dentistry_s3_manager.get_storage_analytics()
            
            # Add additional statistics
            recent_analyses = DentistryAnalysis.objects.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count()
            
            file_types_data = DentistryFile.objects.values('file_type').annotate(
                count=Count('id')
            )
            
            analytics.update({
                'recent_analyses_last_week': recent_analyses,
                'file_types_distribution': list(file_types_data)
            })
            
            return Response(analytics)
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
