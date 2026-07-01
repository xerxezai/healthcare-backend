from rest_framework import generics, status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Count, Q
from datetime import datetime, timedelta
from .models import Patient, MedicalHistory, Appointment, VitalSigns, LabResult
from .serializers import (
    PatientSerializer, PatientSummarySerializer, MedicalHistorySerializer,
    AppointmentSerializer, VitalSignsSerializer, LabResultSerializer,
    PatientStatsSerializer, DoctorSerializer
)
from django.contrib.auth import get_user_model

User = get_user_model()

# Patient Views
class PatientListCreateView(generics.ListCreateAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Patient.objects.filter(is_active=True)
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(patient_id__icontains=search) |
                Q(email__icontains=search)
            )
        return queryset.order_by('-created_at')

class PatientDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [permissions.IsAuthenticated]

class PatientSummaryListView(generics.ListAPIView):
    """Lightweight endpoint for patient selection dropdowns"""
    queryset = Patient.objects.filter(is_active=True)
    serializer_class = PatientSummarySerializer
    permission_classes = [permissions.IsAuthenticated]

# Medical History Views
class MedicalHistoryListCreateView(generics.ListCreateAPIView):
    serializer_class = MedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            return MedicalHistory.objects.filter(patient_id=patient_id)
        return MedicalHistory.objects.all()

class MedicalHistoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MedicalHistory.objects.all()
    serializer_class = MedicalHistorySerializer
    permission_classes = [permissions.IsAuthenticated]

# Appointment Views
class AppointmentListCreateView(generics.ListCreateAPIView):
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = Appointment.objects.all()
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(appointment_date__gte=start_date)
        if end_date:
            queryset = queryset.filter(appointment_date__lte=end_date)
        
        # Filter by doctor
        doctor_id = self.request.query_params.get('doctor_id')
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        
        # Filter by patient
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('appointment_date', 'appointment_time')

class AppointmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]

class TodayAppointmentsView(generics.ListAPIView):
    """Get today's appointments"""
    serializer_class = AppointmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        today = timezone.now().date()
        return Appointment.objects.filter(
            appointment_date=today
        ).order_by('appointment_time')

# Vital Signs Views
class VitalSignsListCreateView(generics.ListCreateAPIView):
    serializer_class = VitalSignsSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            return VitalSigns.objects.filter(patient_id=patient_id)
        return VitalSigns.objects.all()

class VitalSignsDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = VitalSigns.objects.all()
    serializer_class = VitalSignsSerializer
    permission_classes = [permissions.IsAuthenticated]

# Lab Results Views
class LabResultListCreateView(generics.ListCreateAPIView):
    serializer_class = LabResultSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = LabResult.objects.all()
        
        patient_id = self.request.query_params.get('patient_id')
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-ordered_date')

class LabResultDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = LabResult.objects.all()
    serializer_class = LabResultSerializer
    permission_classes = [permissions.IsAuthenticated]

# Dashboard and Statistics Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def patient_dashboard_stats(request):
    """Get dashboard statistics for patient management"""
    today = timezone.now().date()
    this_month_start = today.replace(day=1)
    
    stats = {
        'total_patients': Patient.objects.filter(is_active=True).count(),
        'new_patients_this_month': Patient.objects.filter(
            created_at__gte=this_month_start,
            is_active=True
        ).count(),
        'active_patients': Patient.objects.filter(is_active=True).count(),
        'appointments_today': Appointment.objects.filter(appointment_date=today).count(),
        'pending_lab_results': LabResult.objects.filter(status='pending').count(),
    }
    
    serializer = PatientStatsSerializer(stats)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def doctors_list(request):
    """Get list of doctors for assignment"""
    doctors = User.objects.filter(
        Q(role='doctor') | Q(is_staff=True)
    ).order_by('first_name', 'last_name')
    
    serializer = DoctorSerializer(doctors, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def patient_search(request):
    """Advanced patient search"""
    query = request.GET.get('q', '')
    
    if len(query) < 2:
        return Response({'results': []})
    
    patients = Patient.objects.filter(
        Q(first_name__icontains=query) |
        Q(last_name__icontains=query) |
        Q(patient_id__icontains=query) |
        Q(email__icontains=query) |
        Q(phone_number__icontains=query),
        is_active=True
    )[:10]  # Limit to 10 results
    
    serializer = PatientSummarySerializer(patients, many=True)
    return Response({'results': serializer.data})

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bulk_appointment_update(request):
    """Bulk update appointment statuses"""
    appointment_ids = request.data.get('appointment_ids', [])
    new_status = request.data.get('status', '')
    
    if not appointment_ids or not new_status:
        return Response(
            {'error': 'appointment_ids and status are required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    updated_count = Appointment.objects.filter(
        id__in=appointment_ids
    ).update(status=new_status, updated_at=timezone.now())
    
    return Response({
        'message': f'Updated {updated_count} appointments',
        'updated_count': updated_count
    })

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def appointment_calendar_data(request):
    """Get appointment data formatted for calendar display"""
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    
    appointments = Appointment.objects.filter(
        appointment_date__range=[start_date, end_date]
    ).select_related('patient', 'doctor')
    
    calendar_events = []
    for apt in appointments:
        calendar_events.append({
            'id': apt.id,
            'title': f"{apt.patient.full_name} - {apt.appointment_type}",
            'start': f"{apt.appointment_date}T{apt.appointment_time}",
            'end': f"{apt.appointment_date}T{apt.appointment_time}",  # Add duration calculation if needed
            'backgroundColor': {
                'scheduled': '#007bff',
                'confirmed': '#28a745',
                'in_progress': '#ffc107',
                'completed': '#6c757d',
                'cancelled': '#dc3545',
                'no_show': '#fd7e14'
            }.get(apt.status, '#007bff'),
            'extendedProps': {
                'patient_id': apt.patient.id,
                'doctor_id': apt.doctor.id,
                'status': apt.status,
                'type': apt.appointment_type,
                'chief_complaint': apt.chief_complaint
            }
        })
    
    return Response(calendar_events)
