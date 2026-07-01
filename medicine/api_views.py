"""
Medicine S3 API Views

Comprehensive API endpoints for managing medical data with S3 storage integration.
Provides endpoints for institutions, patients, medical records, consultations,
treatment plans, and lab results with full audit logging.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.contrib.auth.models import User
from django.utils import timezone

from .models import (
    MedicalInstitution, MedicinePatient, MedicalRecord, 
    Consultation, TreatmentPlan, LabResult, MedicineAuditLog,
    DoctorWorkspace
)
from .serializers import (
    MedicalInstitutionSerializer, MedicinePatientSerializer,
    MedicalRecordSerializer, ConsultationSerializer,
    TreatmentPlanSerializer, LabResultSerializer,
    DoctorWorkspaceSerializer
)
from .services.medicine_s3_manager import medicine_s3_manager

logger = logging.getLogger(__name__)


def log_audit_action(user, institution, action, resource_type, resource_id, request, details=None):
    """Log audit action for compliance tracking."""
    try:
        user_ip = request.META.get('REMOTE_ADDR') if request else None
        MedicineAuditLog.objects.create(
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id),
            user=user,
            user_ip=user_ip,
            institution=institution,
            details=details or {}
        )
    except Exception as e:
        logger.error(f"Failed to log audit action: {e}")


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_institution(request):
    """
    Create a new medical institution with S3 structure.
    
    Expected payload:
    {
        "name": "Hospital Name",
        "code": "HOSP001",
        "address": "Full address",
        "phone": "+1234567890",
        "email": "contact@hospital.com",
        "website": "https://hospital.com",
        "license_number": "LIC12345",
        "storage_quota_gb": 1000.0
    }
    """
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['name', 'code', 'address', 'phone', 'email', 'license_number']
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {'error': f'Field {field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Check if institution code already exists
        if MedicalInstitution.objects.filter(code=data['code']).exists():
            return Response(
                {'error': 'Institution with this code already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Create institution
            institution = MedicalInstitution.objects.create(
                name=data['name'],
                code=data['code'],
                address=data['address'],
                phone=data['phone'],
                email=data['email'],
                website=data.get('website', ''),
                license_number=data['license_number'],
                accreditation=data.get('accreditation', ''),
                storage_quota_gb=data.get('storage_quota_gb', 1000.0)
            )
            
            # Create S3 structure
            s3_result = medicine_s3_manager.create_institution_structure(
                str(institution.id),
                institution.name
            )
            
            if s3_result['success']:
                # Log audit action
                log_audit_action(
                    request.user, institution, 'create_institution', 'institution',
                    institution.id, request, {
                        'institution_name': institution.name,
                        'storage_quota_gb': institution.storage_quota_gb,
                        's3_folders_created': len(s3_result.get('folders_created', []))
                    }
                )
                
                serializer = MedicalInstitutionSerializer(institution)
                return Response({
                    'success': True,
                    'institution': serializer.data,
                    's3_structure': s3_result
                }, status=status.HTTP_201_CREATED)
            else:
                # Rollback institution creation if S3 setup fails
                institution.delete()
                return Response(
                    {'error': f'Failed to create S3 structure: {s3_result.get("error")}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
    except Exception as e:
        logger.error(f"Error creating institution: {e}")
        return Response(
            {'error': 'Failed to create institution'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_patient(request):
    """
    Create a new patient with S3 directory structure.
    
    Expected payload:
    {
        "institution_id": "uuid",
        "patient_code": "PAT001",
        "first_name": "John",
        "last_name": "Doe",
        "date_of_birth": "1990-01-01",
        "gender": "M",
        "blood_type": "O+",
        "phone": "+1234567890",
        "email": "john@email.com",
        "address": "Full address",
        "emergency_contact_name": "Jane Doe",
        "emergency_contact_phone": "+1234567891",
        "allergies": "None known",
        "chronic_conditions": "",
        "current_medications": "",
        "insurance_provider": "Insurance Co",
        "insurance_number": "INS12345",
        "height_cm": 175.0,
        "weight_kg": 70.0
    }
    """
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['institution_id', 'patient_code', 'first_name', 'last_name', 'date_of_birth', 'gender']
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {'error': f'Field {field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get institution
        institution = get_object_or_404(MedicalInstitution, id=data['institution_id'])
        
        # Check if patient code already exists in this institution
        if MedicinePatient.objects.filter(
            institution=institution, 
            patient_code=data['patient_code']
        ).exists():
            return Response(
                {'error': 'Patient with this code already exists in this institution'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        with transaction.atomic():
            # Create patient
            patient = MedicinePatient.objects.create(
                institution=institution,
                patient_code=data['patient_code'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                date_of_birth=data['date_of_birth'],
                gender=data['gender'],
                blood_type=data.get('blood_type', ''),
                phone=data.get('phone', ''),
                email=data.get('email', ''),
                address=data.get('address', ''),
                emergency_contact_name=data.get('emergency_contact_name', ''),
                emergency_contact_phone=data.get('emergency_contact_phone', ''),
                allergies=data.get('allergies', ''),
                chronic_conditions=data.get('chronic_conditions', ''),
                current_medications=data.get('current_medications', ''),
                insurance_provider=data.get('insurance_provider', ''),
                insurance_number=data.get('insurance_number', ''),
                height_cm=data.get('height_cm'),
                weight_kg=data.get('weight_kg'),
                created_by=request.user
            )
            
            # Create S3 directory structure
            patient_info = {
                'patient_id': str(patient.id),
                'patient_code': patient.patient_code,
                'full_name': patient.full_name,
                'date_of_birth': patient.date_of_birth.isoformat(),
                'gender': patient.gender,
                'phone': patient.phone,
                'address': patient.address,
                'emergency_contact': patient.emergency_contact_name,
                'insurance_number': patient.insurance_number
            }
            
            s3_result = medicine_s3_manager.create_patient_directory(
                str(institution.id),
                str(patient.id),
                patient_info
            )
            
            if s3_result['success']:
                # Log audit action
                log_audit_action(
                    request.user, institution, 'create_patient', 'patient',
                    patient.id, request, {
                        'patient_code': patient.patient_code,
                        'patient_name': patient.full_name,
                        's3_folders_created': len(s3_result.get('folders_created', [])),
                        'encrypted_fields': s3_result.get('encrypted_fields', 0)
                    }
                )
                
                serializer = MedicinePatientSerializer(patient)
                return Response({
                    'success': True,
                    'patient': serializer.data,
                    's3_structure': s3_result
                }, status=status.HTTP_201_CREATED)
            else:
                # Rollback patient creation if S3 setup fails
                patient.delete()
                return Response(
                    {'error': f'Failed to create S3 directory: {s3_result.get("error")}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
    except Exception as e:
        logger.error(f"Error creating patient: {e}")
        return Response(
            {'error': 'Failed to create patient'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_medical_record(request):
    """
    Upload a medical record to patient's S3 directory.
    
    Expected multipart form data:
    - file: Medical record file
    - patient_id: UUID of the patient
    - record_type: Type of medical record
    - title: Record title
    - description: Record description (optional)
    - consultation_id: Related consultation ID (optional)
    """
    try:
        # Validate required fields
        if 'file' not in request.FILES:
            return Response(
                {'error': 'File is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        patient_id = request.data.get('patient_id')
        record_type = request.data.get('record_type')
        title = request.data.get('title')
        
        if not all([patient_id, record_type, title]):
            return Response(
                {'error': 'patient_id, record_type, and title are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get patient
        patient = get_object_or_404(MedicinePatient, id=patient_id)
        
        # Get uploaded file
        uploaded_file = request.FILES['file']
        file_content = uploaded_file.read()
        
        # Prepare metadata
        metadata = {
            'doctor_id': str(request.user.id),
            'consultation_id': request.data.get('consultation_id'),
            'upload_timestamp': timezone.now().isoformat()
        }
        
        with transaction.atomic():
            # Upload to S3
            s3_result = medicine_s3_manager.upload_medical_record(
                str(patient.institution.id),
                str(patient.id),
                file_content,
                uploaded_file.name,
                record_type,
                metadata
            )
            
            if s3_result['success']:
                # Create database record
                consultation = None
                if request.data.get('consultation_id'):
                    consultation = get_object_or_404(Consultation, id=request.data.get('consultation_id'))
                
                medical_record = MedicalRecord.objects.create(
                    patient=patient,
                    record_type=record_type,
                    title=title,
                    description=request.data.get('description', ''),
                    s3_key=s3_result['s3_key'],
                    file_size_mb=s3_result['file_size_mb'],
                    is_encrypted=s3_result['encrypted'],
                    created_by=request.user,
                    consultation=consultation
                )
                
                # Log audit action
                log_audit_action(
                    request.user, patient.institution, 'upload_record', 'medical_record',
                    medical_record.id, request, {
                        'patient_id': str(patient.id),
                        'record_type': record_type,
                        'file_size_mb': s3_result['file_size_mb'],
                        'encrypted': s3_result['encrypted']
                    }
                )
                
                serializer = MedicalRecordSerializer(medical_record)
                return Response({
                    'success': True,
                    'medical_record': serializer.data,
                    's3_info': s3_result
                }, status=status.HTTP_201_CREATED)
            else:
                return Response(
                    {'error': f'Failed to upload file: {s3_result.get("error")}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
    except Exception as e:
        logger.error(f"Error uploading medical record: {e}")
        return Response(
            {'error': 'Failed to upload medical record'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_consultation(request):
    """
    Create a new consultation with S3 notes storage.
    
    Expected payload:
    {
        "patient_id": "uuid",
        "consultation_type": "routine",
        "consultation_date": "2024-12-01T10:00:00Z",
        "duration_minutes": 30,
        "chief_complaint": "Patient's main complaint",
        "history_present_illness": "Detailed history",
        "examination_findings": "Physical examination findings",
        "assessment": "Clinical assessment",
        "plan": "Treatment plan",
        "blood_pressure_systolic": 120,
        "blood_pressure_diastolic": 80,
        "heart_rate": 72,
        "temperature": 36.5,
        "respiratory_rate": 16,
        "oxygen_saturation": 98
    }
    """
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['patient_id', 'consultation_type', 'consultation_date', 'chief_complaint']
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {'error': f'Field {field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get patient
        patient = get_object_or_404(MedicinePatient, id=data['patient_id'])
        
        with transaction.atomic():
            # Create consultation
            consultation = Consultation.objects.create(
                patient=patient,
                doctor=request.user,
                consultation_type=data['consultation_type'],
                consultation_date=data['consultation_date'],
                duration_minutes=data.get('duration_minutes', 30),
                chief_complaint=data['chief_complaint'],
                history_present_illness=data.get('history_present_illness', ''),
                examination_findings=data.get('examination_findings', ''),
                assessment=data.get('assessment', ''),
                plan=data.get('plan', ''),
                blood_pressure_systolic=data.get('blood_pressure_systolic'),
                blood_pressure_diastolic=data.get('blood_pressure_diastolic'),
                heart_rate=data.get('heart_rate'),
                temperature=data.get('temperature'),
                respiratory_rate=data.get('respiratory_rate'),
                oxygen_saturation=data.get('oxygen_saturation'),
                status='completed'
            )
            
            # Create detailed notes for S3 storage
            consultation_notes = {
                'consultation_id': str(consultation.id),
                'patient_id': str(patient.id),
                'doctor_id': str(request.user.id),
                'consultation_date': consultation.consultation_date.isoformat(),
                'detailed_notes': {
                    'chief_complaint': consultation.chief_complaint,
                    'history_present_illness': consultation.history_present_illness,
                    'examination_findings': consultation.examination_findings,
                    'assessment': consultation.assessment,
                    'plan': consultation.plan,
                    'vital_signs': {
                        'blood_pressure': consultation.blood_pressure,
                        'heart_rate': consultation.heart_rate,
                        'temperature': consultation.temperature,
                        'respiratory_rate': consultation.respiratory_rate,
                        'oxygen_saturation': consultation.oxygen_saturation
                    }
                },
                'additional_notes': data.get('additional_notes', ''),
                'follow_up_instructions': data.get('follow_up_instructions', ''),
                'created_at': timezone.now().isoformat()
            }
            
            # Upload consultation notes to S3
            import json
            notes_content = json.dumps(consultation_notes, indent=2).encode()
            
            s3_result = medicine_s3_manager.upload_medical_record(
                str(patient.institution.id),
                str(patient.id),
                notes_content,
                f"consultation_notes_{consultation.id}.json",
                'consultation_note',
                {'consultation_id': str(consultation.id)}
            )
            
            if s3_result['success']:
                consultation.s3_notes_key = s3_result['s3_key']
                consultation.save()
                
                # Log audit action
                log_audit_action(
                    request.user, patient.institution, 'create_consultation', 'consultation',
                    consultation.id, request, {
                        'patient_id': str(patient.id),
                        'consultation_type': consultation.consultation_type,
                        'duration_minutes': consultation.duration_minutes,
                        's3_notes_uploaded': True
                    }
                )
                
                serializer = ConsultationSerializer(consultation)
                return Response({
                    'success': True,
                    'consultation': serializer.data,
                    's3_notes': s3_result
                }, status=status.HTTP_201_CREATED)
            else:
                # Keep consultation but log S3 failure
                logger.warning(f"Failed to upload consultation notes to S3: {s3_result.get('error')}")
                
                serializer = ConsultationSerializer(consultation)
                return Response({
                    'success': True,
                    'consultation': serializer.data,
                    'warning': 'Consultation created but notes not uploaded to S3'
                }, status=status.HTTP_201_CREATED)
                
    except Exception as e:
        logger.error(f"Error creating consultation: {e}")
        return Response(
            {'error': 'Failed to create consultation'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_treatment_plan(request):
    """
    Create a comprehensive treatment plan with S3 storage.
    
    Expected payload:
    {
        "consultation_id": "uuid",
        "title": "Treatment plan title",
        "diagnosis": "Primary diagnosis",
        "treatment_goals": "Treatment objectives",
        "start_date": "2024-12-01",
        "expected_end_date": "2024-12-31",
        "priority": "medium",
        "medications": [...],
        "procedures": [...],
        "follow_up_schedule": [...],
        "dietary_recommendations": "Diet instructions",
        "lifestyle_modifications": "Lifestyle changes",
        "expected_duration": "30 days",
        "progress_indicators": [...],
        "emergency_protocols": "Emergency instructions"
    }
    """
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['consultation_id', 'title', 'diagnosis', 'start_date']
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {'error': f'Field {field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get consultation
        consultation = get_object_or_404(Consultation, id=data['consultation_id'])
        patient = consultation.patient
        
        with transaction.atomic():
            # Create treatment plan
            treatment_plan = TreatmentPlan.objects.create(
                patient=patient,
                consultation=consultation,
                created_by=request.user,
                title=data['title'],
                diagnosis=data['diagnosis'],
                treatment_goals=data['treatment_goals'],
                start_date=data['start_date'],
                expected_end_date=data.get('expected_end_date'),
                priority=data.get('priority', 'medium')
            )
            
            # Create comprehensive treatment plan data for S3
            treatment_data = {
                'treatment_id': str(treatment_plan.id),
                'consultation_id': str(consultation.id),
                'patient_id': str(patient.id),
                'doctor_id': str(request.user.id),
                'diagnosis': data['diagnosis'],
                'treatment_goals': data['treatment_goals'],
                'medications': data.get('medications', []),
                'procedures': data.get('procedures', []),
                'follow_up_schedule': data.get('follow_up_schedule', []),
                'dietary_recommendations': data.get('dietary_recommendations', ''),
                'lifestyle_modifications': data.get('lifestyle_modifications', ''),
                'expected_duration': data.get('expected_duration', ''),
                'progress_indicators': data.get('progress_indicators', []),
                'emergency_protocols': data.get('emergency_protocols', ''),
                'created_at': timezone.now().isoformat()
            }
            
            # Create treatment plan in S3
            s3_result = medicine_s3_manager.create_treatment_plan(
                str(patient.institution.id),
                str(patient.id),
                treatment_data
            )
            
            if s3_result['success']:
                treatment_plan.s3_plan_key = s3_result['s3_key']
                treatment_plan.status = 'active'
                treatment_plan.save()
                
                # Log audit action
                log_audit_action(
                    request.user, patient.institution, 'create_treatment_plan', 'treatment_plan',
                    treatment_plan.id, request, {
                        'patient_id': str(patient.id),
                        'consultation_id': str(consultation.id),
                        'diagnosis': data['diagnosis'][:100],  # Truncate for logging
                        'priority': treatment_plan.priority
                    }
                )
                
                serializer = TreatmentPlanSerializer(treatment_plan)
                return Response({
                    'success': True,
                    'treatment_plan': serializer.data,
                    's3_plan': s3_result
                }, status=status.HTTP_201_CREATED)
            else:
                # Rollback treatment plan creation if S3 fails
                treatment_plan.delete()
                return Response(
                    {'error': f'Failed to create treatment plan in S3: {s3_result.get("error")}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
    except Exception as e:
        logger.error(f"Error creating treatment plan: {e}")
        return Response(
            {'error': 'Failed to create treatment plan'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def store_lab_results(request):
    """
    Store lab results with S3 integration.
    
    Expected payload:
    {
        "patient_id": "uuid",
        "consultation_id": "uuid",
        "test_name": "Complete Blood Count",
        "test_category": "blood",
        "lab_facility": "Central Lab",
        "ordered_date": "2024-12-01T08:00:00Z",
        "collection_date": "2024-12-01T09:00:00Z",
        "result_date": "2024-12-01T16:00:00Z",
        "test_results": {...},
        "reference_ranges": {...},
        "abnormal_flags": [...],
        "critical_values": [...],
        "interpretation": "Results interpretation",
        "recommendations": "Follow-up recommendations",
        "fasting_status": true,
        "specimen_type": "venous blood",
        "collection_method": "venipuncture"
    }
    """
    try:
        data = request.data
        
        # Validate required fields
        required_fields = ['patient_id', 'test_name', 'test_category', 'lab_facility', 'ordered_date']
        for field in required_fields:
            if not data.get(field):
                return Response(
                    {'error': f'Field {field} is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get patient
        patient = get_object_or_404(MedicinePatient, id=data['patient_id'])
        
        # Get consultation if provided
        consultation = None
        if data.get('consultation_id'):
            consultation = get_object_or_404(Consultation, id=data['consultation_id'])
        
        with transaction.atomic():
            # Create lab result record
            lab_result = LabResult.objects.create(
                patient=patient,
                consultation=consultation,
                ordered_by=request.user,
                test_name=data['test_name'],
                test_category=data['test_category'],
                lab_facility=data['lab_facility'],
                ordered_date=data['ordered_date'],
                collection_date=data.get('collection_date'),
                result_date=data.get('result_date'),
                has_abnormal_values=bool(data.get('abnormal_flags')),
                has_critical_values=bool(data.get('critical_values')),
                status=data.get('status', 'completed')
            )
            
            # Prepare lab data for S3 storage
            lab_data = {
                'lab_id': str(lab_result.id),
                'patient_id': str(patient.id),
                'test_name': data['test_name'],
                'test_category': data['test_category'],
                'lab_facility': data['lab_facility'],
                'test_date': data.get('result_date', data['ordered_date']),
                'doctor_id': str(request.user.id),
                'test_results': data.get('test_results', {}),
                'reference_ranges': data.get('reference_ranges', {}),
                'abnormal_flags': data.get('abnormal_flags', []),
                'critical_values': data.get('critical_values', []),
                'interpretation': data.get('interpretation', ''),
                'recommendations': data.get('recommendations', ''),
                'fasting_status': data.get('fasting_status'),
                'specimen_type': data.get('specimen_type', ''),
                'collection_method': data.get('collection_method', ''),
                'verified_by': str(request.user.id),
                'created_at': timezone.now().isoformat()
            }
            
            # Store lab results in S3
            s3_result = medicine_s3_manager.store_lab_results(
                str(patient.institution.id),
                str(patient.id),
                lab_data
            )
            
            if s3_result['success']:
                lab_result.s3_result_key = s3_result['s3_key']
                lab_result.save()
                
                # Log audit action
                log_audit_action(
                    request.user, patient.institution, 'upload_lab_result', 'lab_result',
                    lab_result.id, request, {
                        'patient_id': str(patient.id),
                        'test_name': data['test_name'],
                        'test_category': data['test_category'],
                        'has_abnormal_values': lab_result.has_abnormal_values,
                        'has_critical_values': lab_result.has_critical_values
                    }
                )
                
                serializer = LabResultSerializer(lab_result)
                return Response({
                    'success': True,
                    'lab_result': serializer.data,
                    's3_data': s3_result
                }, status=status.HTTP_201_CREATED)
            else:
                # Rollback lab result creation if S3 fails
                lab_result.delete()
                return Response(
                    {'error': f'Failed to store lab results in S3: {s3_result.get("error")}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
                
    except Exception as e:
        logger.error(f"Error storing lab results: {e}")
        return Response(
            {'error': 'Failed to store lab results'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_patient_medical_summary(request, patient_id):
    """Get comprehensive medical summary for a patient."""
    try:
        patient = get_object_or_404(MedicinePatient, id=patient_id)
        
        # Get S3 summary
        s3_summary = medicine_s3_manager.get_patient_medical_summary(
            str(patient.institution.id),
            str(patient.id)
        )
        
        if s3_summary['success']:
            # Get database summary
            db_summary = {
                'total_consultations': patient.consultations.count(),
                'total_treatment_plans': patient.treatment_plans.count(),
                'total_lab_results': patient.lab_results.count(),
                'recent_consultations': ConsultationSerializer(
                    patient.consultations.order_by('-consultation_date')[:5], many=True
                ).data,
                'active_treatment_plans': TreatmentPlanSerializer(
                    patient.treatment_plans.filter(status='active'), many=True
                ).data
            }
            
            combined_summary = {
                'patient_info': MedicinePatientSerializer(patient).data,
                's3_summary': s3_summary['summary'],
                'database_summary': db_summary
            }
            
            # Log audit action
            log_audit_action(
                request.user, patient.institution, 'access_record', 'patient_summary',
                patient.id, request, {'summary_type': 'comprehensive'}
            )
            
            return Response({
                'success': True,
                'summary': combined_summary
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': f'Failed to get patient summary: {s3_summary.get("error")}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Error getting patient medical summary: {e}")
        return Response(
            {'error': 'Failed to get patient medical summary'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_medicine_analytics(request, institution_id):
    """Get comprehensive analytics for medicine department."""
    try:
        institution = get_object_or_404(MedicalInstitution, id=institution_id)
        
        # Get S3 analytics
        s3_analytics = medicine_s3_manager.get_medicine_analytics(str(institution.id))
        
        if s3_analytics['success']:
            # Get database analytics
            db_analytics = {
                'total_patients': institution.medicine_patients.filter(is_active=True).count(),
                'total_doctors': institution.doctor_workspaces.filter(is_active=True).count(),
                'total_consultations': Consultation.objects.filter(patient__institution=institution).count(),
                'total_treatment_plans': TreatmentPlan.objects.filter(patient__institution=institution).count(),
                'total_lab_results': LabResult.objects.filter(patient__institution=institution).count(),
                'active_treatment_plans': TreatmentPlan.objects.filter(
                    patient__institution=institution, status='active'
                ).count(),
                'recent_activity': MedicineAuditLog.objects.filter(
                    institution=institution
                ).order_by('-timestamp')[:20].values(
                    'action', 'resource_type', 'timestamp', 'user__username'
                )
            }
            
            combined_analytics = {
                'institution_info': MedicalInstitutionSerializer(institution).data,
                's3_analytics': s3_analytics['analytics'],
                'database_analytics': db_analytics
            }
            
            # Log audit action
            log_audit_action(
                request.user, institution, 'access_record', 'analytics',
                institution.id, request, {'analytics_type': 'comprehensive'}
            )
            
            return Response({
                'success': True,
                'analytics': combined_analytics
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': f'Failed to get analytics: {s3_analytics.get("error")}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
    except Exception as e:
        logger.error(f"Error getting medicine analytics: {e}")
        return Response(
            {'error': 'Failed to get medicine analytics'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ViewSets for standard CRUD operations
class MedicalInstitutionViewSet(viewsets.ModelViewSet):
    """ViewSet for MedicalInstitution model."""
    
    queryset = MedicalInstitution.objects.all()
    serializer_class = MedicalInstitutionSerializer
    permission_classes = [IsAuthenticated]


class MedicinePatientViewSet(viewsets.ModelViewSet):
    """ViewSet for MedicinePatient model."""
    
    queryset = MedicinePatient.objects.all()
    serializer_class = MedicinePatientSerializer
    permission_classes = [IsAuthenticated]


class MedicalRecordViewSet(viewsets.ModelViewSet):
    """ViewSet for MedicalRecord model."""
    
    queryset = MedicalRecord.objects.all()
    serializer_class = MedicalRecordSerializer
    permission_classes = [IsAuthenticated]


class ConsultationViewSet(viewsets.ModelViewSet):
    """ViewSet for Consultation model."""
    
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer
    permission_classes = [IsAuthenticated]


class TreatmentPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for TreatmentPlan model."""
    
    queryset = TreatmentPlan.objects.all()
    serializer_class = TreatmentPlanSerializer
    permission_classes = [IsAuthenticated]


class LabResultViewSet(viewsets.ModelViewSet):
    """ViewSet for LabResult model."""
    
    queryset = LabResult.objects.all()
    serializer_class = LabResultSerializer
    permission_classes = [IsAuthenticated]


class DoctorWorkspaceViewSet(viewsets.ModelViewSet):
    """ViewSet for DoctorWorkspace model."""
    
    queryset = DoctorWorkspace.objects.all()
    serializer_class = DoctorWorkspaceSerializer
    permission_classes = [IsAuthenticated]
