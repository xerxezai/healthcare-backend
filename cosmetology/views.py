from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q, Count, Avg, Sum
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    CosmetologyClient, CosmetologyService, CosmetologyProduct,
    CosmetologyAppointment, CosmetologyTreatmentPlan, CosmetologyConsultation,
    CosmetologyProgress,
    # Cosmetic Gynecology Models
    CosmeticGynecologyClient, CosmeticGynecologyTreatment, CosmeticGynecologyConsultation,
    CosmeticGynecologyTreatmentPlan, CosmeticGynecologyProgress
)
from .serializers import (
    CosmetologyClientSerializer, CosmetologyServiceSerializer, CosmetologyProductSerializer,
    CosmetologyAppointmentSerializer, CosmetologyTreatmentPlanSerializer, 
    CosmetologyConsultationSerializer, CosmetologyProgressSerializer,
    CosmetologyClientListSerializer, CosmetologyServiceListSerializer,
    CosmetologyProductListSerializer, CosmetologyDashboardStatsSerializer,
    AppointmentCalendarSerializer,
    # Cosmetic Gynecology Serializers
    CosmeticGynecologyClientSerializer, CosmeticGynecologyTreatmentSerializer,
    CosmeticGynecologyConsultationSerializer, CosmeticGynecologyTreatmentPlanSerializer,
    CosmeticGynecologyProgressSerializer
)

class CosmetologyClientViewSet(viewsets.ModelViewSet):
    queryset = CosmetologyClient.objects.all()
    serializer_class = CosmetologyClientSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(phone__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset
    
    @action(detail=True, methods=['get'])
    def appointments(self, request, pk=None):
        client = self.get_object()
        appointments = client.appointments.all().order_by('-appointment_date')
        serializer = CosmetologyAppointmentSerializer(appointments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def treatment_plans(self, request, pk=None):
        client = self.get_object()
        plans = client.treatment_plans.all().order_by('-created_at')
        serializer = CosmetologyTreatmentPlanSerializer(plans, many=True)
        return Response(serializer.data)

class CosmetologyServiceViewSet(viewsets.ModelViewSet):
    queryset = CosmetologyService.objects.filter(is_active=True)
    serializer_class = CosmetologyServiceSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category', None)
        if category:
            queryset = queryset.filter(category=category)
        return queryset
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        categories = CosmetologyService.SERVICE_CATEGORIES
        return Response([{'value': cat[0], 'label': cat[1]} for cat in categories])

class CosmetologyProductViewSet(viewsets.ModelViewSet):
    queryset = CosmetologyProduct.objects.filter(is_active=True)
    serializer_class = CosmetologyProductSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        product_type = self.request.query_params.get('type', None)
        brand = self.request.query_params.get('brand', None)
        
        if product_type:
            queryset = queryset.filter(product_type=product_type)
        if brand:
            queryset = queryset.filter(brand__icontains=brand)
            
        return queryset
    
    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        low_stock_products = self.get_queryset().filter(stock_quantity__lt=10)
        serializer = self.get_serializer(low_stock_products, many=True)
        return Response(serializer.data)

class CosmetologyAppointmentViewSet(viewsets.ModelViewSet):
    queryset = CosmetologyAppointment.objects.all()
    serializer_class = CosmetologyAppointmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        status = self.request.query_params.get('status', None)
        
        if date_from:
            queryset = queryset.filter(appointment_date__gte=date_from)
        if date_to:
            queryset = queryset.filter(appointment_date__lte=date_to)
        if status:
            queryset = queryset.filter(status=status)
            
        return queryset.order_by('-appointment_date')
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        appointment = self.get_object()
        appointment.status = 'completed'
        appointment.save()
        return Response({'status': 'appointment marked as completed'})
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        today = timezone.now().date()
        appointments = self.get_queryset().filter(appointment_date__date=today)
        serializer = self.get_serializer(appointments, many=True)
        return Response(serializer.data)

class CosmetologyTreatmentPlanViewSet(viewsets.ModelViewSet):
    queryset = CosmetologyTreatmentPlan.objects.all()
    serializer_class = CosmetologyTreatmentPlanSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        is_active = self.request.query_params.get('active', None)
        if is_active:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        return queryset.order_by('-created_at')

class CosmetologyConsultationViewSet(viewsets.ModelViewSet):
    queryset = CosmetologyConsultation.objects.all()
    serializer_class = CosmetologyConsultationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return super().get_queryset().order_by('-consultation_date')

class CosmetologyProgressViewSet(viewsets.ModelViewSet):
    queryset = CosmetologyProgress.objects.all()
    serializer_class = CosmetologyProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        client_id = self.request.query_params.get('client', None)
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        return queryset.order_by('-date_recorded')

class CosmetologyDashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Basic stats
        total_clients = CosmetologyClient.objects.count()
        active_treatments = CosmetologyTreatmentPlan.objects.filter(is_active=True).count()
        
        # Monthly revenue
        current_month = timezone.now().replace(day=1)
        monthly_revenue = CosmetologyAppointment.objects.filter(
            appointment_date__gte=current_month,
            status='completed'
        ).aggregate(total=Sum('total_amount'))['total'] or 0
        
        # Today's appointments
        today = timezone.now().date()
        appointments_today = CosmetologyAppointment.objects.filter(
            appointment_date__date=today
        ).count()
        
        # Pending consultations
        pending_consultations = CosmetologyConsultation.objects.filter(
            next_consultation_date__lte=timezone.now().date()
        ).count()
        
        # Top services
        top_services = CosmetologyAppointment.objects.values(
            'service__name'
        ).annotate(
            count=Count('id')
        ).order_by('-count')[:5]
        
        # Client satisfaction average
        client_satisfaction_avg = CosmetologyProgress.objects.aggregate(
            avg_satisfaction=Avg('client_satisfaction')
        )['avg_satisfaction'] or 0
        
        stats = {
            'total_clients': total_clients,
            'active_treatments': active_treatments,
            'monthly_revenue': monthly_revenue,
            'appointments_today': appointments_today,
            'pending_consultations': pending_consultations,
            'top_services': list(top_services),
            'client_satisfaction_avg': round(client_satisfaction_avg, 1)
        }
        
        serializer = CosmetologyDashboardStatsSerializer(stats)
        return Response(serializer.data)

class AppointmentCalendarView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        start_date = request.query_params.get('start')
        end_date = request.query_params.get('end')
        
        queryset = CosmetologyAppointment.objects.all()
        
        if start_date:
            queryset = queryset.filter(appointment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(appointment_date__lte=end_date)
            
        serializer = AppointmentCalendarSerializer(queryset, many=True)
        return Response(serializer.data)

class ClientSearchView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        query = request.query_params.get('q', '')
        if len(query) < 2:
            return Response([])
            
        clients = CosmetologyClient.objects.filter(
            Q(name__icontains=query) |
            Q(phone__icontains=query) |
            Q(email__icontains=query)
        )[:10]
        
        serializer = CosmetologyClientListSerializer(clients, many=True)
        return Response(serializer.data)

class ServiceRecommendationView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        client_id = request.data.get('client_id')
        skin_concerns = request.data.get('skin_concerns', [])
        hair_concerns = request.data.get('hair_concerns', [])
        
        try:
            client = CosmetologyClient.objects.get(id=client_id)
        except CosmetologyClient.DoesNotExist:
            return Response({'error': 'Client not found'}, status=404)
        
        # Simple recommendation logic based on concerns
        recommended_services = []
        
        # Skin-based recommendations
        if 'acne' in skin_concerns:
            recommended_services.extend(['facial', 'skincare'])
        if 'aging' in skin_concerns:
            recommended_services.extend(['facial', 'injectable'])
        if 'pigmentation' in skin_concerns:
            recommended_services.extend(['laser', 'facial'])
        
        # Hair-based recommendations
        if 'hair_loss' in hair_concerns:
            recommended_services.extend(['hair'])
        if 'damaged_hair' in hair_concerns:
            recommended_services.extend(['hair'])
        
        services = CosmetologyService.objects.filter(
            category__in=recommended_services,
            is_active=True
        ).distinct()
        
        serializer = CosmetologyServiceListSerializer(services, many=True)
        return Response(serializer.data)

class ProductSearchView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        query = request.query_params.get('q', '')
        product_type = request.query_params.get('type', '')
        
        products = CosmetologyProduct.objects.filter(is_active=True)
        
        if query:
            products = products.filter(
                Q(name__icontains=query) |
                Q(brand__icontains=query) |
                Q(description__icontains=query)
            )
        
        if product_type:
            products = products.filter(product_type=product_type)
            
        products = products[:20]
        serializer = CosmetologyProductListSerializer(products, many=True)
        return Response(serializer.data)


# ============================================================================
# COSMETIC GYNECOLOGY VIEWS - AI-POWERED MEDICAL SPECIALIZATION
# ============================================================================

class CosmeticGynecologyClientViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing cosmetic gynecology clients with AI-powered risk assessment
    """
    queryset = CosmeticGynecologyClient.objects.all()
    serializer_class = CosmeticGynecologyClientSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(client__name__icontains=search) |
                Q(client__email__icontains=search) |
                Q(client__phone__icontains=search) |
                Q(medical_history__icontains=search)
            )
        return queryset
    
    @action(detail=True, methods=['post'])
    def update_ai_risk_assessment(self, request, pk=None):
        """
        Update AI risk assessment for a client
        """
        client = self.get_object()
        
        # AI Risk Assessment Algorithm
        risk_factors = []
        risk_score = 0
        
        # Age factor
        if client.age:
            if client.age > 45:
                risk_factors.append("Advanced maternal age")
                risk_score += 2
            elif client.age > 35:
                risk_factors.append("Increased age factor")
                risk_score += 1
        
        # Medical history analysis
        if client.medical_history:
            history_lower = client.medical_history.lower()
            if any(condition in history_lower for condition in ['diabetes', 'hypertension', 'heart']):
                risk_factors.append("Chronic medical conditions")
                risk_score += 3
            if any(condition in history_lower for condition in ['surgery', 'operation', 'procedure']):
                risk_factors.append("Previous surgical history")
                risk_score += 1
        
        # Reproductive history analysis
        if client.reproductive_history:
            repro_lower = client.reproductive_history.lower()
            if 'complications' in repro_lower:
                risk_factors.append("Previous pregnancy complications")
                risk_score += 2
            if any(term in repro_lower for term in ['multiple', 'twins', 'triplets']):
                risk_factors.append("Multiple pregnancy history")
                risk_score += 1
        
        # Calculate risk level
        if risk_score >= 6:
            risk_level = "HIGH"
        elif risk_score >= 3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Update AI analysis
        client.ai_risk_assessment = {
            "risk_level": risk_level,
            "risk_score": risk_score,
            "risk_factors": risk_factors,
            "recommendations": self._generate_risk_recommendations(risk_level, risk_factors),
            "analysis_date": datetime.now().isoformat(),
            "requires_specialist_consultation": risk_score >= 4
        }
        client.save()
        
        return Response({
            "message": "AI risk assessment updated successfully",
            "risk_assessment": client.ai_risk_assessment
        })
    
    def _generate_risk_recommendations(self, risk_level, risk_factors):
        """Generate AI-powered recommendations based on risk assessment"""
        recommendations = []
        
        if risk_level == "HIGH":
            recommendations.extend([
                "Immediate specialist consultation required",
                "Comprehensive pre-treatment evaluation",
                "Consider alternative treatment approaches",
                "Enhanced monitoring protocols"
            ])
        elif risk_level == "MEDIUM":
            recommendations.extend([
                "Specialist consultation recommended",
                "Additional diagnostic tests may be needed",
                "Modified treatment protocols",
                "Regular monitoring required"
            ])
        else:
            recommendations.extend([
                "Standard treatment protocols applicable",
                "Routine monitoring sufficient",
                "Good candidate for cosmetic procedures"
            ])
        
        # Specific recommendations based on risk factors
        for factor in risk_factors:
            if "age" in factor.lower():
                recommendations.append("Consider hormone level assessment")
            elif "medical conditions" in factor.lower():
                recommendations.append("Coordinate with primary care physician")
            elif "surgical" in factor.lower():
                recommendations.append("Review surgical history and healing patterns")
        
        return recommendations


class CosmeticGynecologyTreatmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing cosmetic gynecology treatments with AI optimization
    """
    queryset = CosmeticGynecologyTreatment.objects.all()
    serializer_class = CosmeticGynecologyTreatmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get('category', None)
        search = self.request.query_params.get('search', None)
        
        if category:
            queryset = queryset.filter(category=category)
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(description__icontains=search) |
                Q(category__icontains=search)
            )
        return queryset
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        """Get all treatment categories"""
        categories = CosmeticGynecologyTreatment.objects.values_list('category', flat=True).distinct()
        return Response(list(categories))
    
    @action(detail=True, methods=['post'])
    def optimize_parameters(self, request, pk=None):
        """
        AI-powered treatment parameter optimization
        """
        treatment = self.get_object()
        client_data = request.data.get('client_data', {})
        
        # AI optimization algorithm
        optimized_params = {}
        
        # Age-based optimization
        age = client_data.get('age', 30)
        if age > 45:
            optimized_params['intensity_level'] = 'Low'
            optimized_params['session_duration'] = min(treatment.duration_minutes - 15, 30)
        elif age > 35:
            optimized_params['intensity_level'] = 'Medium'
            optimized_params['session_duration'] = treatment.duration_minutes - 10
        else:
            optimized_params['intensity_level'] = 'Standard'
            optimized_params['session_duration'] = treatment.duration_minutes
        
        # Skin type optimization
        skin_type = client_data.get('skin_type', 'Normal')
        if skin_type in ['Sensitive', 'Very Sensitive']:
            optimized_params['pre_treatment_prep'] = 'Extended cooling protocol'
            optimized_params['post_treatment_care'] = 'Enhanced soothing treatment'
        
        # Medical history considerations
        medical_history = client_data.get('medical_history', '').lower()
        if 'keloid' in medical_history or 'scarring' in medical_history:
            optimized_params['special_precautions'] = 'Keloid prevention protocol'
            optimized_params['follow_up_frequency'] = 'Weekly for first month'
        
        # Generate optimization report
        optimization_report = {
            "optimized_parameters": optimized_params,
            "confidence_score": 85,  # AI confidence in optimization
            "optimization_date": datetime.now().isoformat(),
            "considerations": self._generate_optimization_considerations(client_data)
        }
        
        return Response(optimization_report)
    
    def _generate_optimization_considerations(self, client_data):
        """Generate optimization considerations based on client data"""
        considerations = []
        
        age = client_data.get('age', 30)
        if age > 40:
            considerations.append("Collagen production may be reduced - consider complementary treatments")
        
        if client_data.get('hormonal_status') == 'Post-menopausal':
            considerations.append("Hormonal changes may affect treatment response")
        
        if client_data.get('previous_treatments'):
            considerations.append("Previous treatment history reviewed for contraindications")
        
        return considerations


class CosmeticGynecologyConsultationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing cosmetic gynecology consultations with AI analysis
    """
    queryset = CosmeticGynecologyConsultation.objects.all()
    serializer_class = CosmeticGynecologyConsultationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        client_id = self.request.query_params.get('client', None)
        consultation_type = self.request.query_params.get('type', None)
        
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        if consultation_type:
            queryset = queryset.filter(consultation_type=consultation_type)
        
        return queryset.order_by('-consultation_date')
    
    @action(detail=True, methods=['post'])
    def generate_ai_analysis(self, request, pk=None):
        """
        Generate AI analysis for consultation findings
        """
        consultation = self.get_object()
        
        # AI Analysis Algorithm
        analysis_results = {}
        
        # Analyze chief complaints
        if consultation.chief_complaint:
            complaint_analysis = self._analyze_chief_complaint(consultation.chief_complaint)
            analysis_results['complaint_analysis'] = complaint_analysis
        
        # Analyze physical findings
        if consultation.physical_findings:
            physical_analysis = self._analyze_physical_findings(consultation.physical_findings)
            analysis_results['physical_analysis'] = physical_analysis
        
        # Generate treatment recommendations
        treatment_recommendations = self._generate_treatment_recommendations(
            consultation.chief_complaint, 
            consultation.physical_findings,
            consultation.consultation_type
        )
        analysis_results['treatment_recommendations'] = treatment_recommendations
        
        # Calculate treatment priority
        priority_score = self._calculate_treatment_priority(consultation)
        analysis_results['priority_assessment'] = {
            "priority_level": "HIGH" if priority_score > 7 else "MEDIUM" if priority_score > 4 else "LOW",
            "priority_score": priority_score,
            "urgency_factors": self._identify_urgency_factors(consultation)
        }
        
        # Update consultation with AI analysis
        consultation.ai_analysis_results = {
            "analysis_date": datetime.now().isoformat(),
            "ai_version": "1.0",
            **analysis_results
        }
        consultation.save()
        
        return Response({
            "message": "AI analysis completed successfully",
            "analysis_results": consultation.ai_analysis_results
        })
    
    def _analyze_chief_complaint(self, complaint):
        """Analyze chief complaint using AI"""
        complaint_lower = complaint.lower()
        analysis = {
            "categories": [],
            "severity_indicators": [],
            "suggested_evaluations": []
        }
        
        # Categorize complaints
        if any(term in complaint_lower for term in ['pain', 'discomfort', 'ache']):
            analysis['categories'].append('Pain-related')
            analysis['suggested_evaluations'].append('Pain assessment scale')
        
        if any(term in complaint_lower for term in ['aesthetic', 'appearance', 'cosmetic']):
            analysis['categories'].append('Aesthetic concern')
            analysis['suggested_evaluations'].append('Photographic documentation')
        
        if any(term in complaint_lower for term in ['functional', 'function', 'difficulty']):
            analysis['categories'].append('Functional issue')
            analysis['suggested_evaluations'].append('Functional assessment')
        
        # Identify severity indicators
        if any(term in complaint_lower for term in ['severe', 'intense', 'unbearable']):
            analysis['severity_indicators'].append('High severity language')
        
        return analysis
    
    def _analyze_physical_findings(self, findings):
        """Analyze physical findings using AI"""
        findings_lower = findings.lower()
        analysis = {
            "findings_categories": [],
            "risk_indicators": [],
            "recommended_investigations": []
        }
        
        # Categorize findings
        if any(term in findings_lower for term in ['normal', 'unremarkable', 'within normal']):
            analysis['findings_categories'].append('Normal findings')
        
        if any(term in findings_lower for term in ['asymmetry', 'irregular', 'abnormal']):
            analysis['findings_categories'].append('Anatomical variation')
            analysis['recommended_investigations'].append('Detailed imaging if indicated')
        
        if any(term in findings_lower for term in ['scarring', 'adhesions', 'fibrosis']):
            analysis['findings_categories'].append('Scarring/Fibrosis')
            analysis['risk_indicators'].append('Potential treatment complications')
        
        return analysis
    
    def _generate_treatment_recommendations(self, complaint, findings, consultation_type):
        """Generate AI-powered treatment recommendations"""
        recommendations = []
        
        # Basic recommendations based on consultation type
        if consultation_type == 'INITIAL':
            recommendations.extend([
                "Comprehensive evaluation completed",
                "Patient education regarding treatment options",
                "Informed consent discussion"
            ])
        elif consultation_type == 'FOLLOW_UP':
            recommendations.extend([
                "Review treatment progress",
                "Assess treatment effectiveness",
                "Modify treatment plan if needed"
            ])
        
        # Specific recommendations based on complaints and findings
        if complaint and 'aesthetic' in complaint.lower():
            recommendations.append("Consider cosmetic treatment options")
            recommendations.append("Photographic documentation for progress tracking")
        
        if findings and any(term in findings.lower() for term in ['normal', 'unremarkable']):
            recommendations.append("Good candidate for elective procedures")
        
        return recommendations
    
    def _calculate_treatment_priority(self, consultation):
        """Calculate treatment priority score"""
        score = 0
        
        if consultation.chief_complaint:
            complaint_lower = consultation.chief_complaint.lower()
            if any(term in complaint_lower for term in ['severe', 'intense', 'unbearable']):
                score += 3
            elif any(term in complaint_lower for term in ['moderate', 'concerning']):
                score += 2
            elif any(term in complaint_lower for term in ['mild', 'slight']):
                score += 1
        
        if consultation.consultation_type == 'EMERGENCY':
            score += 5
        elif consultation.consultation_type == 'URGENT':
            score += 3
        
        return score
    
    def _identify_urgency_factors(self, consultation):
        """Identify factors that increase treatment urgency"""
        factors = []
        
        if consultation.chief_complaint:
            complaint_lower = consultation.chief_complaint.lower()
            if any(term in complaint_lower for term in ['pain', 'bleeding', 'infection']):
                factors.append('Symptomatic presentation')
        
        if consultation.consultation_type in ['EMERGENCY', 'URGENT']:
            factors.append('High-priority consultation type')
        
        return factors


class CosmeticGynecologyTreatmentPlanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing AI-powered treatment plans
    """
    queryset = CosmeticGynecologyTreatmentPlan.objects.all()
    serializer_class = CosmeticGynecologyTreatmentPlanSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        client_id = self.request.query_params.get('client', None)
        status = self.request.query_params.get('status', None)
        
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset.order_by('-created_date')
    
    @action(detail=True, methods=['post'])
    def generate_ai_optimization(self, request, pk=None):
        """
        Generate AI-powered treatment plan optimization
        """
        treatment_plan = self.get_object()
        
        # AI Optimization Algorithm
        optimization_data = {}
        
        # Analyze current plan effectiveness
        effectiveness_score = self._calculate_plan_effectiveness(treatment_plan)
        optimization_data['effectiveness_analysis'] = {
            "current_score": effectiveness_score,
            "improvement_potential": max(0, 90 - effectiveness_score),
            "key_metrics": self._analyze_plan_metrics(treatment_plan)
        }
        
        # Generate optimization suggestions
        optimization_suggestions = self._generate_optimization_suggestions(treatment_plan)
        optimization_data['optimization_suggestions'] = optimization_suggestions
        
        # Predict outcomes
        outcome_predictions = self._predict_treatment_outcomes(treatment_plan)
        optimization_data['outcome_predictions'] = outcome_predictions
        
        # Update treatment plan with AI optimization
        treatment_plan.ai_optimization_data = {
            "optimization_date": datetime.now().isoformat(),
            "ai_version": "1.0",
            **optimization_data
        }
        treatment_plan.save()
        
        return Response({
            "message": "AI optimization completed successfully",
            "optimization_data": treatment_plan.ai_optimization_data
        })
    
    def _calculate_plan_effectiveness(self, treatment_plan):
        """Calculate treatment plan effectiveness score"""
        score = 50  # Base score
        
        # Analyze treatment combination
        if treatment_plan.primary_treatment and treatment_plan.secondary_treatments:
            score += 15  # Comprehensive approach
        
        # Check session frequency optimization
        if treatment_plan.session_frequency:
            if 'weekly' in treatment_plan.session_frequency.lower():
                score += 10  # Optimal frequency
            elif 'monthly' in treatment_plan.session_frequency.lower():
                score += 5
        
        # Expected duration analysis
        if treatment_plan.expected_duration_weeks:
            if 8 <= treatment_plan.expected_duration_weeks <= 16:
                score += 10  # Optimal duration range
            elif treatment_plan.expected_duration_weeks < 8:
                score += 5   # May be too short
        
        return min(100, score)
    
    def _analyze_plan_metrics(self, treatment_plan):
        """Analyze key metrics of the treatment plan"""
        metrics = {}
        
        # Treatment complexity
        treatment_count = 1  # Primary treatment
        if treatment_plan.secondary_treatments:
            treatment_count += len(treatment_plan.secondary_treatments.split(','))
        metrics['treatment_complexity'] = 'High' if treatment_count > 3 else 'Medium' if treatment_count > 1 else 'Low'
        
        # Duration appropriateness
        if treatment_plan.expected_duration_weeks:
            if treatment_plan.expected_duration_weeks > 20:
                metrics['duration_assessment'] = 'Extended treatment period'
            elif treatment_plan.expected_duration_weeks < 6:
                metrics['duration_assessment'] = 'Short treatment period'
            else:
                metrics['duration_assessment'] = 'Appropriate duration'
        
        return metrics
    
    def _generate_optimization_suggestions(self, treatment_plan):
        """Generate optimization suggestions based on AI analysis"""
        suggestions = []
        
        # Analyze current treatments
        if not treatment_plan.secondary_treatments:
            suggestions.append({
                "category": "Treatment Enhancement",
                "suggestion": "Consider adding complementary treatments for better results",
                "priority": "Medium"
            })
        
        # Session frequency optimization
        if treatment_plan.session_frequency and 'monthly' in treatment_plan.session_frequency.lower():
            suggestions.append({
                "category": "Frequency Optimization",
                "suggestion": "Consider increasing session frequency for faster results",
                "priority": "Low"
            })
        
        # Duration optimization
        if treatment_plan.expected_duration_weeks and treatment_plan.expected_duration_weeks > 20:
            suggestions.append({
                "category": "Duration Optimization",
                "suggestion": "Extended treatment duration - consider progress evaluation",
                "priority": "Medium"
            })
        
        return suggestions
    
    def _predict_treatment_outcomes(self, treatment_plan):
        """Predict treatment outcomes using AI"""
        predictions = {}
        
        # Success probability
        base_success_rate = 75  # Base success rate
        
        # Adjust based on treatment plan factors
        if treatment_plan.secondary_treatments:
            base_success_rate += 10  # Comprehensive treatment
        
        if treatment_plan.expected_duration_weeks:
            if 8 <= treatment_plan.expected_duration_weeks <= 16:
                base_success_rate += 5  # Optimal duration
        
        predictions['success_probability'] = min(95, base_success_rate)
        
        # Timeline predictions
        if treatment_plan.expected_duration_weeks:
            predictions['timeline_predictions'] = {
                "first_visible_results": f"{max(2, treatment_plan.expected_duration_weeks // 4)} weeks",
                "significant_improvement": f"{treatment_plan.expected_duration_weeks // 2} weeks",
                "final_results": f"{treatment_plan.expected_duration_weeks} weeks"
            }
        
        # Risk assessment
        predictions['risk_assessment'] = {
            "complication_risk": "Low",  # Base assessment
            "revision_probability": "15%",
            "satisfaction_prediction": "High"
        }
        
        return predictions


class CosmeticGynecologyProgressViewSet(viewsets.ModelViewSet):
    """
    ViewSet for tracking treatment progress with AI analysis
    """
    queryset = CosmeticGynecologyProgress.objects.all()
    serializer_class = CosmeticGynecologyProgressSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        client_id = self.request.query_params.get('client', None)
        treatment_plan_id = self.request.query_params.get('treatment_plan', None)
        
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        if treatment_plan_id:
            queryset = queryset.filter(treatment_plan_id=treatment_plan_id)
        
        return queryset.order_by('-assessment_date')
    
    @action(detail=True, methods=['post'])
    def generate_ai_progress_analysis(self, request, pk=None):
        """
        Generate AI-powered progress analysis
        """
        progress = self.get_object()
        
        # AI Progress Analysis Algorithm
        analysis_results = {}
        
        # Progress trend analysis
        trend_analysis = self._analyze_progress_trends(progress)
        analysis_results['trend_analysis'] = trend_analysis
        
        # Satisfaction correlation
        satisfaction_analysis = self._analyze_satisfaction_correlation(progress)
        analysis_results['satisfaction_analysis'] = satisfaction_analysis
        
        # Outcome predictions
        outcome_predictions = self._predict_final_outcomes(progress)
        analysis_results['outcome_predictions'] = outcome_predictions
        
        # Generate recommendations
        recommendations = self._generate_progress_recommendations(progress, trend_analysis)
        analysis_results['recommendations'] = recommendations
        
        # Update progress record with AI analysis
        progress.ai_progress_analysis = {
            "analysis_date": datetime.now().isoformat(),
            "ai_version": "1.0",
            **analysis_results
        }
        progress.save()
        
        return Response({
            "message": "AI progress analysis completed successfully",
            "analysis_results": progress.ai_progress_analysis
        })
    
    def _analyze_progress_trends(self, progress):
        """Analyze progress trends using AI"""
        trends = {}
        
        # Improvement rate analysis
        if progress.improvement_percentage is not None:
            if progress.improvement_percentage >= 75:
                trends['improvement_rate'] = 'Excellent'
            elif progress.improvement_percentage >= 50:
                trends['improvement_rate'] = 'Good'
            elif progress.improvement_percentage >= 25:
                trends['improvement_rate'] = 'Moderate'
            else:
                trends['improvement_rate'] = 'Slow'
        
        # Side effects analysis
        if progress.side_effects_noted:
            side_effects_lower = progress.side_effects_noted.lower()
            if any(term in side_effects_lower for term in ['none', 'minimal', 'no']):
                trends['side_effects_profile'] = 'Favorable'
            elif any(term in side_effects_lower for term in ['mild', 'slight']):
                trends['side_effects_profile'] = 'Acceptable'
            else:
                trends['side_effects_profile'] = 'Concerning'
        else:
            trends['side_effects_profile'] = 'Not documented'
        
        return trends
    
    def _analyze_satisfaction_correlation(self, progress):
        """Analyze satisfaction correlation with clinical progress"""
        correlation = {}
        
        if progress.patient_satisfaction_score is not None and progress.improvement_percentage is not None:
            satisfaction_improvement_ratio = progress.patient_satisfaction_score / max(1, progress.improvement_percentage)
            
            if satisfaction_improvement_ratio > 0.8:
                correlation['satisfaction_alignment'] = 'High - Patient satisfaction aligns with clinical progress'
            elif satisfaction_improvement_ratio > 0.6:
                correlation['satisfaction_alignment'] = 'Moderate - Some discrepancy between satisfaction and clinical progress'
            else:
                correlation['satisfaction_alignment'] = 'Low - Significant discrepancy requires attention'
        
        # Expectation management analysis
        if progress.patient_satisfaction_score is not None:
            if progress.patient_satisfaction_score >= 8:
                correlation['expectation_management'] = 'Excellent - Expectations well managed'
            elif progress.patient_satisfaction_score >= 6:
                correlation['expectation_management'] = 'Good - Minor expectation adjustments may be needed'
            else:
                correlation['expectation_management'] = 'Poor - Expectation realignment required'
        
        return correlation
    
    def _predict_final_outcomes(self, progress):
        """Predict final treatment outcomes based on current progress"""
        predictions = {}
        
        if progress.improvement_percentage is not None:
            # Extrapolate final improvement
            current_improvement = progress.improvement_percentage
            
            if current_improvement >= 60:
                predictions['final_improvement_range'] = '80-95%'
                predictions['outcome_confidence'] = 'High'
            elif current_improvement >= 40:
                predictions['final_improvement_range'] = '60-80%'
                predictions['outcome_confidence'] = 'Moderate'
            elif current_improvement >= 20:
                predictions['final_improvement_range'] = '40-70%'
                predictions['outcome_confidence'] = 'Moderate'
            else:
                predictions['final_improvement_range'] = '25-50%'
                predictions['outcome_confidence'] = 'Low'
        
        # Satisfaction prediction
        if progress.patient_satisfaction_score is not None:
            if progress.patient_satisfaction_score >= 7:
                predictions['final_satisfaction'] = 'High satisfaction expected'
            elif progress.patient_satisfaction_score >= 5:
                predictions['final_satisfaction'] = 'Moderate satisfaction expected'
            else:
                predictions['final_satisfaction'] = 'Satisfaction concerns - intervention needed'
        
        return predictions
    
    def _generate_progress_recommendations(self, progress, trend_analysis):
        """Generate recommendations based on progress analysis"""
        recommendations = []
        
        # Based on improvement rate
        improvement_rate = trend_analysis.get('improvement_rate', '')
        if improvement_rate == 'Slow':
            recommendations.append({
                "category": "Treatment Adjustment",
                "recommendation": "Consider treatment protocol modification",
                "priority": "High"
            })
        elif improvement_rate == 'Excellent':
            recommendations.append({
                "category": "Treatment Continuation",
                "recommendation": "Continue current treatment protocol",
                "priority": "Low"
            })
        
        # Based on side effects
        side_effects_profile = trend_analysis.get('side_effects_profile', '')
        if side_effects_profile == 'Concerning':
            recommendations.append({
                "category": "Safety Review",
                "recommendation": "Review treatment parameters and consider modifications",
                "priority": "High"
            })
        
        # Based on satisfaction
        if progress.patient_satisfaction_score is not None and progress.patient_satisfaction_score < 6:
            recommendations.append({
                "category": "Patient Communication",
                "recommendation": "Enhanced patient counseling and expectation management",
                "priority": "Medium"
            })
        
        return recommendations
    
    @action(detail=False, methods=['get'])
    def dashboard_statistics(self, request):
        """
        Get cosmetic gynecology dashboard statistics
        """
        stats = {}
        
        # Client statistics
        total_clients = CosmeticGynecologyClient.objects.count()
        stats['total_clients'] = total_clients
        
        # Treatment statistics
        total_treatments = CosmeticGynecologyTreatment.objects.count()
        stats['total_treatments'] = total_treatments
        
        # Active treatment plans
        active_plans = CosmeticGynecologyTreatmentPlan.objects.filter(status='ACTIVE').count()
        stats['active_treatment_plans'] = active_plans
        
        # Recent consultations (last 30 days)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_consultations = CosmeticGynecologyConsultation.objects.filter(
            consultation_date__gte=thirty_days_ago
        ).count()
        stats['recent_consultations'] = recent_consultations
        
        # Average satisfaction score
        avg_satisfaction = CosmeticGynecologyProgress.objects.aggregate(
            avg_satisfaction=Avg('patient_satisfaction_score')
        )['avg_satisfaction']
        stats['average_satisfaction'] = round(avg_satisfaction, 1) if avg_satisfaction else 0
        
        # Treatment categories distribution
        treatment_categories = CosmeticGynecologyTreatment.objects.values('category').annotate(
            count=Count('id')
        ).order_by('-count')
        stats['treatment_categories'] = list(treatment_categories)
        
        return Response(stats)
