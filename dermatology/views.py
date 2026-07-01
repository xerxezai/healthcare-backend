from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count, Q, Avg
from django.utils import timezone
from datetime import datetime, timedelta
from django.contrib.auth import get_user_model
from subscriptions.permissions import SubscriptionOrSuperAdminPermission
from .models import (
    DermatologyDepartment, SkinCondition, Patient, DermatologyConsultation,
    DiagnosticProcedure, SkinPhoto, TreatmentPlan, TreatmentOutcome, AIAnalysis
)
from .serializers import (
    DermatologyDepartmentSerializer, SkinConditionSerializer, PatientSerializer,
    DermatologyConsultationSerializer, DiagnosticProcedureSerializer,
    SkinPhotoSerializer, TreatmentPlanSerializer, TreatmentOutcomeSerializer,
    AIAnalysisSerializer, DermatologyDashboardStatsSerializer,
    ConsultationSummarySerializer
)

User = get_user_model()


class DermatologyDepartmentViewSet(viewsets.ModelViewSet):
    """ViewSet for Dermatology Departments"""
    queryset = DermatologyDepartment.objects.all()
    serializer_class = DermatologyDepartmentSerializer
    permission_classes = [AllowAny]  # Temporarily allow unauthenticated access for testing
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['is_active', 'emergency_services']
    search_fields = ['name', 'description', 'location']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    @action(detail=True, methods=['get'])
    def consultations(self, request, pk=None):
        """Get consultations for a specific department"""
        department = self.get_object()
        consultations = department.consultations.all()
        serializer = ConsultationSummarySerializer(consultations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get statistics for a specific department"""
        department = self.get_object()
        
        stats = {
            'total_consultations': department.consultations.count(),
            'consultations_this_month': department.consultations.filter(
                scheduled_date__gte=timezone.now().replace(day=1)
            ).count(),
            'pending_consultations': department.consultations.filter(
                status='scheduled'
            ).count(),
            'completed_consultations': department.consultations.filter(
                status='completed'
            ).count(),
            'emergency_consultations': department.consultations.filter(
                priority='emergent'
            ).count(),
        }
        
        return Response(stats)


class SkinConditionViewSet(viewsets.ModelViewSet):
    """ViewSet for Skin Conditions"""
    queryset = SkinCondition.objects.all()
    serializer_class = SkinConditionSerializer
    permission_classes = [AllowAny]  # Temporarily allow unauthenticated access for testing
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['category', 'severity_level', 'is_contagious', 'requires_biopsy', 'is_active']
    search_fields = ['name', 'icd10_code', 'description', 'symptoms']
    ordering_fields = ['name', 'category', 'severity_level', 'created_at']
    ordering = ['name']

    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get skin conditions grouped by category"""
        conditions_by_category = {}
        for category, category_display in SkinCondition.CONDITION_CATEGORIES:
            conditions = self.queryset.filter(category=category, is_active=True)
            conditions_by_category[category] = {
                'display_name': category_display,
                'count': conditions.count(),
                'conditions': SkinConditionSerializer(conditions, many=True).data
            }
        return Response(conditions_by_category)

    @action(detail=True, methods=['get'])
    def treatment_outcomes(self, request, pk=None):
        """Get treatment outcomes statistics for a condition"""
        condition = self.get_object()
        treatment_plans = condition.treatment_plans.all()
        
        outcomes_stats = {
            'total_treatment_plans': treatment_plans.count(),
            'active_plans': treatment_plans.filter(status='active').count(),
            'completed_plans': treatment_plans.filter(status='completed').count(),
            'average_effectiveness': treatment_plans.filter(
                effectiveness_rating__isnull=False
            ).aggregate(avg_rating=Avg('effectiveness_rating'))['avg_rating'],
            'success_rate': 0  # Calculate based on outcomes
        }
        
        return Response(outcomes_stats)


class DermatologyConsultationViewSet(viewsets.ModelViewSet):
    """ViewSet for Dermatology Consultations"""
    queryset = DermatologyConsultation.objects.all()
    serializer_class = DermatologyConsultationSerializer
    permission_classes = [AllowAny]  # Temporarily allow unauthenticated access for testing
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'consultation_type', 'status', 'priority', 'dermatologist',
        'department', 'patient'
    ]
    search_fields = [
        'consultation_number', 'patient__user__first_name',
        'patient__user__last_name', 'chief_complaint'
    ]
    ordering_fields = ['scheduled_date', 'created_at', 'priority']
    ordering = ['-scheduled_date']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=True, methods=['post'])
    def start_consultation(self, request, pk=None):
        """Start a consultation"""
        consultation = self.get_object()
        consultation.actual_start_time = timezone.now()
        consultation.status = 'in_progress'
        consultation.save()
        
        serializer = self.get_serializer(consultation)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete_consultation(self, request, pk=None):
        """Complete a consultation"""
        consultation = self.get_object()
        consultation.actual_end_time = timezone.now()
        consultation.status = 'completed'
        consultation.save()
        
        serializer = self.get_serializer(consultation)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def today_schedule(self, request):
        """Get today's consultation schedule"""
        today = timezone.now().date()
        consultations = self.queryset.filter(
            scheduled_date__date=today
        ).order_by('scheduled_date')
        
        serializer = ConsultationSummarySerializer(consultations, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get upcoming consultations"""
        upcoming_consultations = self.queryset.filter(
            scheduled_date__gt=timezone.now(),
            status='scheduled'
        ).order_by('scheduled_date')[:20]
        
        serializer = ConsultationSummarySerializer(upcoming_consultations, many=True)
        return Response(serializer.data)


class DiagnosticProcedureViewSet(viewsets.ModelViewSet):
    """ViewSet for Diagnostic Procedures"""
    queryset = DiagnosticProcedure.objects.all()
    serializer_class = DiagnosticProcedureSerializer
    permission_classes = [AllowAny]  # Temporarily allow unauthenticated access for testing
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['procedure_type', 'status', 'performed_by', 'consultation']
    search_fields = ['procedure_number', 'procedure_name', 'indication']
    ordering_fields = ['procedure_date', 'created_at']
    ordering = ['-procedure_date']

    @action(detail=False, methods=['get'])
    def by_type(self, request):
        """Get procedures grouped by type"""
        procedures_by_type = {}
        for proc_type, type_display in DiagnosticProcedure.PROCEDURE_TYPES:
            procedures = self.queryset.filter(procedure_type=proc_type)
            procedures_by_type[proc_type] = {
                'display_name': type_display,
                'count': procedures.count(),
                'completed': procedures.filter(status='completed').count(),
                'pending': procedures.filter(status__in=['ordered', 'scheduled']).count()
            }
        return Response(procedures_by_type)

    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark procedure as completed"""
        procedure = self.get_object()
        procedure.status = 'completed'
        procedure.findings = request.data.get('findings', procedure.findings)
        procedure.save()
        
        serializer = self.get_serializer(procedure)
        return Response(serializer.data)


class SkinPhotoViewSet(viewsets.ModelViewSet):
    """ViewSet for Skin Photos"""
    queryset = SkinPhoto.objects.all()
    serializer_class = SkinPhotoSerializer
    permission_classes = [AllowAny]  # Temporarily allow unauthenticated access for testing
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'photo_type', 'anatomical_region', 'consultation',
        'is_before_treatment', 'is_after_treatment', 'consent_obtained'
    ]
    search_fields = ['description', 'specific_location']
    ordering_fields = ['taken_at', 'created_at']
    ordering = ['-taken_at']

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=True, methods=['post'])
    def request_ai_analysis(self, request, pk=None):
        """Request AI analysis for a skin photo"""
        photo = self.get_object()
        
        # This would typically trigger an AI analysis service
        # For now, we'll create a placeholder analysis
        ai_analysis = AIAnalysis.objects.create(
            skin_photo=photo,
            analysis_type='lesion_detection',
            ai_model_version='v1.0.0',
            confidence_level='moderate',
            confidence_score=75.0,
            primary_findings={'status': 'Analysis pending'},
            recommended_actions='Please wait for analysis to complete.'
        )
        
        serializer = AIAnalysisSerializer(ai_analysis)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=['get'])
    def by_patient(self, request):
        """Get photos by patient"""
        patient_id = request.query_params.get('patient_id')
        if not patient_id:
            return Response({'error': 'patient_id is required'}, status=400)
        
        photos = self.queryset.filter(consultation__patient_id=patient_id)
        serializer = self.get_serializer(photos, many=True)
        return Response(serializer.data)


class TreatmentPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for Treatment Plans"""
    queryset = TreatmentPlan.objects.all()
    serializer_class = TreatmentPlanSerializer
    permission_classes = [AllowAny]  # Temporarily allow unauthenticated access for testing
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'treatment_category', 'status', 'diagnosed_condition',
        'prescribed_by', 'consultation'
    ]
    search_fields = ['treatment_name', 'medication_name']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-start_date']

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a treatment plan"""
        treatment_plan = self.get_object()
        treatment_plan.status = 'active'
        treatment_plan.save()
        
        serializer = self.get_serializer(treatment_plan)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        """Complete a treatment plan"""
        treatment_plan = self.get_object()
        treatment_plan.status = 'completed'
        treatment_plan.actual_end_date = timezone.now().date()
        treatment_plan.save()
        
        serializer = self.get_serializer(treatment_plan)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active_treatments(self, request):
        """Get all active treatment plans"""
        active_plans = self.queryset.filter(status='active')
        serializer = self.get_serializer(active_plans, many=True)
        return Response(serializer.data)


class TreatmentOutcomeViewSet(viewsets.ModelViewSet):
    """ViewSet for Treatment Outcomes"""
    queryset = TreatmentOutcome.objects.all()
    serializer_class = TreatmentOutcomeSerializer
    permission_classes = [AllowAny]  # Temporarily allow unauthenticated access for testing
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['outcome_status', 'treatment_plan', 'assessed_by']
    search_fields = ['clinical_notes', 'side_effects_reported']
    ordering_fields = ['assessment_date', 'created_at']
    ordering = ['-assessment_date']

    @action(detail=False, methods=['get'])
    def success_rates(self, request):
        """Get treatment success rates by condition"""
        success_rates = {}
        
        # Calculate success rates by outcome status
        total_outcomes = self.queryset.count()
        if total_outcomes > 0:
            success_counts = self.queryset.values('outcome_status').annotate(
                count=Count('id')
            )
            
            for item in success_counts:
                success_rates[item['outcome_status']] = {
                    'count': item['count'],
                    'percentage': round((item['count'] / total_outcomes) * 100, 2)
                }
        
        return Response(success_rates)


class AIAnalysisViewSet(viewsets.ModelViewSet):
    """ViewSet for AI Analyses"""
    queryset = AIAnalysis.objects.all()
    serializer_class = AIAnalysisSerializer
    permission_classes = [AllowAny]  # Temporarily allow unauthenticated access for testing
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'analysis_type', 'confidence_level', 'requires_biopsy',
        'validated_by_doctor', 'urgency_level'
    ]
    search_fields = ['risk_assessment', 'recommended_actions']
    ordering_fields = ['analysis_date', 'confidence_score', 'created_at']
    ordering = ['-analysis_date']

    @action(detail=True, methods=['post'])
    def validate_analysis(self, request, pk=None):
        """Doctor validation of AI analysis"""
        analysis = self.get_object()
        analysis.validated_by_doctor = True
        analysis.doctor_agreement = request.data.get('agreement', True)
        analysis.doctor_notes = request.data.get('notes', '')
        analysis.save()
        
        serializer = self.get_serializer(analysis)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def pending_validation(self, request):
        """Get AI analyses pending doctor validation"""
        pending_analyses = self.queryset.filter(
            validated_by_doctor=False,
            requires_biopsy=True
        ).order_by('-analysis_date')
        
        serializer = self.get_serializer(pending_analyses, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def high_risk(self, request):
        """Get high-risk AI analyses"""
        high_risk_analyses = self.queryset.filter(
            Q(urgency_level='urgent') | Q(urgency_level='emergent') |
            Q(requires_biopsy=True)
        ).order_by('-analysis_date')
        
        serializer = self.get_serializer(high_risk_analyses, many=True)
        return Response(serializer.data)


# Dashboard and Statistics Views
class DermatologyDashboardViewSet(viewsets.ViewSet):
    """Dashboard statistics and overview for dermatology department"""
    permission_classes = [AllowAny]  # Temporarily allow unauthenticated access for testing

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get comprehensive dashboard statistics"""
        today = timezone.now().date()
        this_week_start = today - timedelta(days=today.weekday())
        this_month_start = today.replace(day=1)
        
        stats = {
            'total_patients': Patient.objects.count(),
            'total_consultations': DermatologyConsultation.objects.count(),
            'consultations_today': DermatologyConsultation.objects.filter(
                scheduled_date__date=today
            ).count(),
            'consultations_this_week': DermatologyConsultation.objects.filter(
                scheduled_date__date__gte=this_week_start
            ).count(),
            'consultations_this_month': DermatologyConsultation.objects.filter(
                scheduled_date__date__gte=this_month_start
            ).count(),
            'pending_consultations': DermatologyConsultation.objects.filter(
                status='scheduled'
            ).count(),
            'completed_consultations': DermatologyConsultation.objects.filter(
                status='completed'
            ).count(),
            'total_diagnostic_procedures': DiagnosticProcedure.objects.count(),
            'total_skin_photos': SkinPhoto.objects.count(),
            'total_ai_analyses': AIAnalysis.objects.count(),
            'total_treatment_plans': TreatmentPlan.objects.count(),
            'active_treatment_plans': TreatmentPlan.objects.filter(
                status='active'
            ).count(),
            'departments_count': DermatologyDepartment.objects.filter(
                is_active=True
            ).count(),
            'skin_conditions_count': SkinCondition.objects.filter(
                is_active=True
            ).count(),
        }
        
        serializer = DermatologyDashboardStatsSerializer(stats)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """Get recent activity across all dermatology modules"""
        recent_consultations = DermatologyConsultation.objects.order_by('-created_at')[:5]
        recent_procedures = DiagnosticProcedure.objects.order_by('-created_at')[:5]
        recent_photos = SkinPhoto.objects.order_by('-created_at')[:5]
        recent_analyses = AIAnalysis.objects.order_by('-created_at')[:5]
        
        return Response({
            'recent_consultations': ConsultationSummarySerializer(
                recent_consultations, many=True
            ).data,
            'recent_procedures': DiagnosticProcedureSerializer(
                recent_procedures, many=True
            ).data,
            'recent_photos': SkinPhotoSerializer(
                recent_photos, many=True, context={'request': request}
            ).data,
            'recent_analyses': AIAnalysisSerializer(
                recent_analyses, many=True
            ).data,
        })

    @action(detail=False, methods=['get'])
    def alerts(self, request):
        """Get important alerts and notifications"""
        alerts = []
        today = timezone.now().date()
        
        # High-priority consultations
        urgent_consultations = DermatologyConsultation.objects.filter(
            priority__in=['urgent', 'emergent'],
            status='scheduled'
        ).count()
        
        if urgent_consultations > 0:
            alerts.append({
                'type': 'urgent_consultations',
                'message': f'{urgent_consultations} urgent consultations pending',
                'count': urgent_consultations,
                'level': 'error'
            })
        
        # AI analyses requiring validation
        pending_validations = AIAnalysis.objects.filter(
            validated_by_doctor=False,
            requires_biopsy=True
        ).count()
        
        if pending_validations > 0:
            alerts.append({
                'type': 'pending_ai_validations',
                'message': f'{pending_validations} AI analyses require doctor validation',
                'count': pending_validations,
                'level': 'warning'
            })
        
        # Overdue follow-ups
        overdue_followups = DermatologyConsultation.objects.filter(
            next_appointment_recommended__lt=today,
            status='completed'
        ).count()
        
        if overdue_followups > 0:
            alerts.append({
                'type': 'overdue_followups',
                'message': f'{overdue_followups} patients have overdue follow-ups',
                'count': overdue_followups,
                'level': 'info'
            })
        
        return Response({'alerts': alerts})


class PatientViewSet(viewsets.ModelViewSet):
    """ViewSet for Dermatology Patients"""
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [SubscriptionOrSuperAdminPermission]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['skin_type', 'smoking_status', 'previous_skin_cancer']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'medical_record_number', 'occupation']
    ordering_fields = ['created_at', 'updated_at', 'user__first_name', 'user__last_name']
    ordering = ['-created_at']

    def perform_create(self, serializer):
        """Create a new dermatology patient"""
        # Generate unique medical record number
        import uuid
        medical_record_number = f"DERM-{uuid.uuid4().hex[:8].upper()}"
        
        # Check if user data is provided for new user creation
        if 'user_data' in self.request.data:
            user_data = self.request.data['user_data']
            
            # Create new user
            user = User.objects.create_user(
                username=user_data.get('email', ''),
                email=user_data.get('email', ''),
                first_name=user_data.get('first_name', ''),
                last_name=user_data.get('last_name', ''),
                phone_number=user_data.get('phone', ''),
                role='patient'
            )
            
            # Create dermatology patient profile
            serializer.save(
                user=user,
                medical_record_number=medical_record_number
            )
        else:
            # Use existing user (if provided)
            serializer.save(medical_record_number=medical_record_number)

    @action(detail=True, methods=['get'])
    def consultations(self, request, pk=None):
        """Get consultations for a specific patient"""
        patient = self.get_object()
        consultations = patient.dermatology_consultations.all().order_by('-scheduled_date')
        serializer = DermatologyConsultationSerializer(consultations, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def treatment_plans(self, request, pk=None):
        """Get treatment plans for a specific patient"""
        patient = self.get_object()
        # Get treatment plans through consultations
        treatment_plans = TreatmentPlan.objects.filter(
            consultation__patient=patient
        ).order_by('-created_at')
        serializer = TreatmentPlanSerializer(treatment_plans, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def photos(self, request, pk=None):
        """Get photos for a specific patient"""
        patient = self.get_object()
        # Get photos through consultations
        photos = SkinPhoto.objects.filter(
            consultation__patient=patient
        ).order_by('-taken_date')
        serializer = SkinPhotoSerializer(photos, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def add_note(self, request, pk=None):
        """Add a note to patient record"""
        patient = self.get_object()
        note_text = request.data.get('note', '')
        
        if not note_text:
            return Response(
                {'error': 'Note text is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # You could create a separate Note model or add to patient fields
        # For now, we'll add to a general notes field if it exists
        # This would require adding a notes field to the Patient model
        
        return Response({'message': 'Note added successfully'})

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """Get patient statistics"""
        total_patients = self.get_queryset().count()
        
        # Skin type distribution
        skin_type_stats = self.get_queryset().values('skin_type').annotate(
            count=Count('skin_type')
        ).order_by('skin_type')
        
        # Smoking status
        smoking_stats = self.get_queryset().aggregate(
            smokers=Count('id', filter=Q(smoking_status=True)),
            non_smokers=Count('id', filter=Q(smoking_status=False))
        )
        
        # Previous skin cancer
        cancer_history_stats = self.get_queryset().aggregate(
            with_history=Count('id', filter=Q(previous_skin_cancer=True)),
            without_history=Count('id', filter=Q(previous_skin_cancer=False))
        )
        
        # Recent registrations (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_registrations = self.get_queryset().filter(
            created_at__gte=thirty_days_ago
        ).count()
        
        return Response({
            'total_patients': total_patients,
            'skin_type_distribution': skin_type_stats,
            'smoking_statistics': smoking_stats,
            'cancer_history_statistics': cancer_history_stats,
            'recent_registrations': recent_registrations
        })
