from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Patient, Dentist, DentalHistory, Appointment, Treatment,
    DentalXray, PeriodontalChart, DentalAIAnalysis, Prescription,
    DentalEmergency, TreatmentPlan, CancerDetection, CancerDetectionImage,
    CancerDetectionAcknowledgment, CancerRiskAssessment, CancerTreatmentPlan,
    CancerNotification
)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']

class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(write_only=True, required=False)
    age = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_age(self, obj):
        from datetime import date
        if obj.date_of_birth:
            return (date.today() - obj.date_of_birth).days // 365
        return None

    def create(self, validated_data):
        # Handle user_id if provided
        user_id = validated_data.pop('user_id', None)
        if user_id:
            validated_data['user_id'] = user_id
        
        # Generate patient_id if not provided
        if 'patient_id' not in validated_data:
            patient_count = Patient.objects.count() + 1
            validated_data['patient_id'] = f"DENT{patient_count:06d}"
        
        return super().create(validated_data)

class DentistSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    total_patients = serializers.SerializerMethodField()
    total_appointments = serializers.SerializerMethodField()

    class Meta:
        model = Dentist
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_total_patients(self, obj):
        return obj.appointments.values('patient').distinct().count()

    def get_total_appointments(self, obj):
        return obj.appointments.count()

class DentalHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = DentalHistory
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

class AppointmentSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    dentist = DentistSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    dentist_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Appointment
        fields = '__all__'
        read_only_fields = ['appointment_id', 'created_at', 'updated_at']

class TreatmentSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    dentist = DentistSerializer(read_only=True)
    appointment = AppointmentSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    dentist_id = serializers.IntegerField(write_only=True)
    appointment_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Treatment
        fields = '__all__'
        read_only_fields = ['treatment_id', 'created_at', 'updated_at']

class DentalXraySerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    dentist = DentistSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    dentist_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = DentalXray
        fields = '__all__'
        read_only_fields = ['xray_id', 'created_at', 'updated_at']

class PeriodontalChartSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    dentist = DentistSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    dentist_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = PeriodontalChart
        fields = '__all__'
        read_only_fields = ['chart_id', 'created_at', 'updated_at']

class DentalAIAnalysisSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    dentist = DentistSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    dentist_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = DentalAIAnalysis
        fields = '__all__'
        read_only_fields = ['analysis_id', 'ai_model_version', 'processing_time', 'created_at', 'updated_at']

class PrescriptionSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    dentist = DentistSerializer(read_only=True)
    appointment = AppointmentSerializer(read_only=True)
    treatment = TreatmentSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    dentist_id = serializers.IntegerField(write_only=True)

    class Meta:
        model = Prescription
        fields = '__all__'
        read_only_fields = ['prescription_id', 'created_at', 'updated_at']

class DentalEmergencySerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    attending_dentist = DentistSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    attending_dentist_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = DentalEmergency
        fields = '__all__'
        read_only_fields = ['emergency_id', 'created_at', 'updated_at']

class TreatmentPlanSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    primary_dentist = DentistSerializer(read_only=True)
    patient_id = serializers.IntegerField(write_only=True)
    primary_dentist_id = serializers.IntegerField(write_only=True)
    progress_percentage = serializers.SerializerMethodField()

    class Meta:
        model = TreatmentPlan
        fields = '__all__'
        read_only_fields = ['plan_id', 'created_at', 'updated_at']

    def get_progress_percentage(self, obj):
        if obj.status == 'completed':
            return 100
        elif obj.status == 'in_progress':
            # Calculate based on completed treatments
            total_treatments = obj.patient.treatments.filter(
                appointment__appointment_date__gte=obj.start_date
            ).count()
            completed_treatments = obj.patient.treatments.filter(
                appointment__appointment_date__gte=obj.start_date,
                status='completed'
            ).count()
            if total_treatments > 0:
                return (completed_treatments / total_treatments) * 100
            return 0
        else:
            return 0

# Dashboard and Statistics Serializers
class DashboardStatsSerializer(serializers.Serializer):
    total_patients = serializers.IntegerField()
    total_appointments = serializers.IntegerField()
    todays_appointments = serializers.IntegerField()
    pending_treatments = serializers.IntegerField()
    emergency_cases = serializers.IntegerField()
    ai_analyses_today = serializers.IntegerField()
    revenue_this_month = serializers.DecimalField(max_digits=10, decimal_places=2)
    patient_satisfaction = serializers.DecimalField(max_digits=3, decimal_places=2)

class AppointmentCalendarSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    dentist_name = serializers.CharField(source='dentist.user.get_full_name', read_only=True)

    class Meta:
        model = Appointment
        fields = ['id', 'appointment_id', 'patient_name', 'dentist_name', 
                 'appointment_date', 'duration', 'appointment_type', 'status']

class PatientSummarySerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    upcoming_appointment = serializers.SerializerMethodField()
    last_visit = serializers.SerializerMethodField()
    total_treatments = serializers.SerializerMethodField()
    outstanding_balance = serializers.SerializerMethodField()

    class Meta:
        model = Patient
        fields = ['id', 'patient_id', 'user', 'phone', 'upcoming_appointment', 
                 'last_visit', 'total_treatments', 'outstanding_balance']

    def get_upcoming_appointment(self, obj):
        from django.utils import timezone
        upcoming = obj.appointments.filter(
            appointment_date__gte=timezone.now(),
            status__in=['scheduled', 'confirmed']
        ).first()
        return AppointmentCalendarSerializer(upcoming).data if upcoming else None

    def get_last_visit(self, obj):
        from django.utils import timezone
        last_visit = obj.appointments.filter(
            appointment_date__lt=timezone.now(),
            status='completed'
        ).first()
        return last_visit.appointment_date if last_visit else None

    def get_total_treatments(self, obj):
        return obj.treatments.count()

    def get_outstanding_balance(self, obj):
        total_cost = sum(treatment.cost for treatment in obj.treatments.all())
        total_paid = sum(treatment.patient_payment for treatment in obj.treatments.all())
        return total_cost - total_paid


# Cancer Detection Serializers
class CancerDetectionImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = CancerDetectionImage
        fields = '__all__'
        read_only_fields = ['image_id', 'uploaded_at', 'analyzed_at']


class CancerDetectionAcknowledgmentSerializer(serializers.ModelSerializer):
    dentist = DentistSerializer(read_only=True)
    
    class Meta:
        model = CancerDetectionAcknowledgment
        fields = '__all__'
        read_only_fields = ['acknowledgment_id', 'acknowledged_at']


class CancerDetectionSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    dentist = DentistSerializer(read_only=True)
    reviewed_by = DentistSerializer(read_only=True)
    images = CancerDetectionImageSerializer(many=True, read_only=True)
    acknowledgments = CancerDetectionAcknowledgmentSerializer(
        source='cancerdetectionacknowledgment_set', many=True, read_only=True
    )
    
    class Meta:
        model = CancerDetection
        fields = '__all__'
        read_only_fields = ['detection_id', 'detected_at', 'updated_at']


class CancerRiskAssessmentSerializer(serializers.ModelSerializer):
    patient = PatientSerializer(read_only=True)
    dentist = DentistSerializer(read_only=True)
    
    class Meta:
        model = CancerRiskAssessment
        fields = '__all__'
        read_only_fields = ['assessment_id', 'assessment_date', 'updated_at']


class CancerTreatmentPlanSerializer(serializers.ModelSerializer):
    cancer_detection = CancerDetectionSerializer(read_only=True)
    primary_dentist = DentistSerializer(read_only=True)
    
    class Meta:
        model = CancerTreatmentPlan
        fields = '__all__'
        read_only_fields = ['plan_id', 'created_at', 'updated_at']


class CancerNotificationSerializer(serializers.ModelSerializer):
    cancer_detection = CancerDetectionSerializer(read_only=True)
    recipient_dentists = DentistSerializer(many=True, read_only=True)
    patient = PatientSerializer(read_only=True)
    
    class Meta:
        model = CancerNotification
        fields = '__all__'
        read_only_fields = ['notification_id', 'created_at']
