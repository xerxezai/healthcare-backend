"""
Seed the database with comprehensive patient admission data
"""
import os
import sys
import django
from datetime import datetime, timedelta
from django.utils import timezone

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from patients.models import Patient
from patients.advanced_models import PatientAdmission, PatientJourney, AIPatientInsights, PatientMetrics
from patients.serializers import PatientSerializer

User = get_user_model()

def create_sample_data():
    print("🏥 Creating comprehensive patient management sample data...")
    
    # Create sample users (doctors, nurses)
    try:
        doctor1 = User.objects.get(email='doctor1@hospital.com')
    except User.DoesNotExist:
        doctor1 = User.objects.create_user(
            email='doctor1@hospital.com',
            password='password123',
            first_name='Dr. Michael',
            last_name='Chen',
            role='doctor'
        )
    
    try:
        doctor2 = User.objects.get(email='doctor2@hospital.com')
    except User.DoesNotExist:
        doctor2 = User.objects.create_user(
            email='doctor2@hospital.com',
            password='password123',
            first_name='Dr. Sarah',
            last_name='Johnson',
            role='doctor'
        )
    
    try:
        nurse1 = User.objects.get(email='nurse1@hospital.com')
    except User.DoesNotExist:
        nurse1 = User.objects.create_user(
            email='nurse1@hospital.com',
            password='password123',
            first_name='Nurse Patricia',
            last_name='Wilson',
            role='nurse'
        )
    
    # Create sample patients
    patients_data = [
        {
            'first_name': 'John',
            'last_name': 'Smith',
            'date_of_birth': datetime(1978, 5, 15).date(),
            'gender': 'M',
            'phone_number': '+15550123456',
            'email': 'john.smith@email.com',
            'address_line1': '123 Main St',
            'city': 'Springfield',
            'state': 'IL',
            'postal_code': '62701',
            'emergency_contact_name': 'Jane Smith',
            'emergency_contact_relationship': 'Spouse',
            'emergency_contact_phone': '+15550124567'
        },
        {
            'first_name': 'Maria',
            'last_name': 'Garcia',
            'date_of_birth': datetime(1990, 8, 22).date(),
            'gender': 'F',
            'phone_number': '+15550125678',
            'email': 'maria.garcia@email.com',
            'address_line1': '456 Oak Ave',
            'city': 'Springfield',
            'state': 'IL',
            'postal_code': '62702',
            'emergency_contact_name': 'Carlos Garcia',
            'emergency_contact_relationship': 'Brother',
            'emergency_contact_phone': '+15550126789'
        },
        {
            'first_name': 'Robert',
            'last_name': 'Brown',
            'date_of_birth': datetime(1965, 12, 3).date(),
            'gender': 'M',
            'phone_number': '+15550127890',
            'email': 'robert.brown@email.com',
            'address_line1': '789 Pine St',
            'city': 'Springfield',
            'state': 'IL',
            'postal_code': '62703',
            'emergency_contact_name': 'Mary Brown',
            'emergency_contact_relationship': 'Wife',
            'emergency_contact_phone': '+15550128901'
        },
        {
            'first_name': 'Lisa',
            'last_name': 'Anderson',
            'date_of_birth': datetime(1985, 3, 10).date(),
            'gender': 'F',
            'phone_number': '+15550129012',
            'email': 'lisa.anderson@email.com',
            'address_line1': '321 Elm St',
            'city': 'Springfield',
            'state': 'IL',
            'postal_code': '62704',
            'emergency_contact_name': 'David Anderson',
            'emergency_contact_relationship': 'Husband',
            'emergency_contact_phone': '+15550130123'
        }
    ]
    
    patients = []
    for patient_data in patients_data:
        try:
            # Try to get existing patient first
            patient = Patient.objects.get(email=patient_data['email'])
            print(f"📝 Found existing patient: {patient.first_name} {patient.last_name}")
        except Patient.DoesNotExist:
            # Create new patient using serializer (patient_id will be auto-generated)
            serializer = PatientSerializer(data=patient_data)
            if serializer.is_valid():
                patient = serializer.save()
                print(f"✅ Created patient: {patient.first_name} {patient.last_name}")
            else:
                print(f"❌ Error creating patient: {serializer.errors}")
                continue
        
        patients.append(patient)
    
    # Create patient admissions
    admissions_data = [
        {
            'patient': patients[0],
            'attending_physician': doctor1,
            'admission_type': 'emergency',
            'department': 'Emergency',
            'room_number': 'ER-101',
            'bed_number': 'A1',
            'chief_complaint': 'Chest pain and shortness of breath',
            'initial_diagnosis': 'Possible myocardial infarction',
            'medical_history': 'Hypertension, diabetes mellitus type 2',
            'allergies': 'Penicillin',
            'current_medications': 'Metformin 500mg BID, Lisinopril 10mg daily',
            'current_status': 'in_treatment',
            'priority_level': 'high',
            'insurance_provider': 'Blue Cross Blue Shield',
            'insurance_policy_number': 'BC123456789',
            'estimated_cost': 8500.00,
            'ai_risk_score': 7.5
        },
        {
            'patient': patients[1],
            'attending_physician': doctor2,
            'admission_type': 'elective',
            'department': 'Cardiology',
            'room_number': 'C-204',
            'bed_number': 'B2',
            'chief_complaint': 'Routine cardiac catheterization',
            'initial_diagnosis': 'Stable angina pectoris',
            'medical_history': 'Previous MI 2019, hyperlipidemia',
            'allergies': 'None known',
            'current_medications': 'Aspirin 81mg daily, Atorvastatin 40mg daily',
            'current_status': 'stable',
            'priority_level': 'medium',
            'insurance_provider': 'Aetna',
            'insurance_policy_number': 'AET987654321',
            'estimated_cost': 12000.00,
            'ai_risk_score': 4.2
        },
        {
            'patient': patients[2],
            'attending_physician': doctor1,
            'admission_type': 'emergency',
            'department': 'Emergency',
            'room_number': 'ER-102',
            'bed_number': 'A3',
            'chief_complaint': 'Acute abdominal pain',
            'initial_diagnosis': 'Possible appendicitis',
            'medical_history': 'Hypertension, previous cholecystectomy',
            'allergies': 'Sulfa drugs',
            'current_medications': 'Amlodipine 5mg daily',
            'current_status': 'critical',
            'priority_level': 'critical',
            'insurance_provider': 'Medicare',
            'insurance_policy_number': 'MED555666777',
            'estimated_cost': 15000.00,
            'ai_risk_score': 8.3
        },
        {
            'patient': patients[3],
            'attending_physician': doctor2,
            'admission_type': 'observation',
            'department': 'Internal Medicine',
            'room_number': 'IM-301',
            'bed_number': 'C1',
            'chief_complaint': 'Chronic fatigue and weakness',
            'initial_diagnosis': 'Anemia workup',
            'medical_history': 'Iron deficiency anemia, hypothyroidism',
            'allergies': 'None known',
            'current_medications': 'Levothyroxine 75mcg daily, Iron sulfate 325mg TID',
            'current_status': 'stable',
            'priority_level': 'low',
            'insurance_provider': 'Cigna',
            'insurance_policy_number': 'CIG111222333',
            'estimated_cost': 3500.00,
            'ai_risk_score': 2.1
        }
    ]
    
    admissions = []
    for i, admission_data in enumerate(admissions_data):
        # Generate unique admission ID
        admission_id = f"ADM-{timezone.now().strftime('%Y%m%d')}-{1000 + i}"
        
        admission, created = PatientAdmission.objects.get_or_create(
            admission_id=admission_id,
            defaults={
                **admission_data,
                'admission_id': admission_id,
                'admission_date': timezone.now() - timedelta(hours=i*6),  # Stagger admission times
                'created_by': doctor1
            }
        )
        admissions.append(admission)
        if created:
            print(f"✅ Created admission: {admission.admission_id} for {admission.patient.first_name} {admission.patient.last_name}")
    
    # Create patient journey events
    for admission in admissions:
        journey_events = [
            {
                'stage': 'admission',
                'location': 'Registration Desk',
                'action': 'Patient registration and insurance verification',
                'staff_member': nurse1,
                'notes': f'Patient {admission.patient.first_name} {admission.patient.last_name} registered for {admission.admission_type} admission',
                'timestamp': admission.admission_date
            },
            {
                'stage': 'triage',
                'location': f'{admission.department} Triage',
                'action': 'Initial assessment and vital signs',
                'staff_member': nurse1,
                'vital_signs': {
                    'blood_pressure': '140/90',
                    'heart_rate': 95,
                    'temperature': 98.6,
                    'oxygen_saturation': 97,
                    'respiratory_rate': 18,
                    'pain_score': 7
                },
                'notes': f'Priority: {admission.priority_level}, Complaint: {admission.chief_complaint}',
                'timestamp': admission.admission_date + timedelta(minutes=15)
            },
            {
                'stage': 'initial_assessment',
                'location': admission.room_number or admission.department,
                'action': 'Medical evaluation by attending physician',
                'staff_member': admission.attending_physician,
                'notes': f'Initial diagnosis: {admission.initial_diagnosis}',
                'timestamp': admission.admission_date + timedelta(minutes=45)
            },
            {
                'stage': 'treatment',
                'location': admission.room_number or admission.department,
                'action': 'Treatment plan initiated',
                'staff_member': admission.attending_physician,
                'notes': 'Treatment commenced as per clinical guidelines',
                'timestamp': admission.admission_date + timedelta(hours=2)
            }
        ]
        
        for event_data in journey_events:
            # Fix field mapping for model compatibility
            event_data_fixed = event_data.copy()
            if 'action' in event_data_fixed:
                event_data_fixed['action_taken'] = event_data_fixed.pop('action')
            
            journey_event, created = PatientJourney.objects.get_or_create(
                admission=admission,
                stage=event_data['stage'],
                timestamp=event_data['timestamp'],
                defaults={
                    **event_data_fixed,
                    'patient': admission.patient
                }
            )
            if created:
                print(f"  ➕ Journey event: {journey_event.stage} for {admission.admission_id}")
    
    # Create AI insights
    for admission in admissions:
        # Risk assessment insight
        risk_insight, created = AIPatientInsights.objects.get_or_create(
            admission=admission,
            insight_type='risk_assessment',
            defaults={
                'patient': admission.patient,
                'confidence_level': 'high' if admission.ai_risk_score > 7 else 'medium',
                'prediction_data': {
                    'length_of_stay_days': 3 if admission.current_status == 'critical' else 2,
                    'complication_probability': 0.15 if admission.ai_risk_score > 7 else 0.08,
                    'readmission_risk_30_days': 0.12,
                    'estimated_cost_range': {
                        'minimum': float(admission.estimated_cost) * 0.8,
                        'maximum': float(admission.estimated_cost) * 1.2,
                        'expected': float(admission.estimated_cost)
                    }
                },
                'recommendations': [
                    {
                        'type': 'monitoring',
                        'priority': 'high' if admission.current_status == 'critical' else 'medium',
                        'action': 'Continuous vital signs monitoring',
                        'rationale': f'Patient has {admission.current_status} status with risk score {admission.ai_risk_score}'
                    },
                    {
                        'type': 'assessment',
                        'priority': 'medium',
                        'action': 'Regular pain assessment',
                        'rationale': 'Ensure patient comfort and proper pain management'
                    }
                ],
                'risk_factors': [
                    f'Age: {2024 - admission.patient.date_of_birth.year} years',
                    f'Medical history: {admission.medical_history}',
                    f'Presenting complaint: {admission.chief_complaint}',
                    f'Admission type: {admission.admission_type}'
                ],
                'risk_score': admission.ai_risk_score,
                'accuracy_score': 0.85,
                'model_version': 'v1.0'
            }
        )
        if created:
            print(f"  🤖 AI insight: Risk assessment for {admission.admission_id}")
    
    # Create patient metrics
    for admission in admissions:
        metrics, created = PatientMetrics.objects.get_or_create(
            admission=admission,
            defaults={
                'patient': admission.patient,
                'registration_to_triage_minutes': 10,
                'triage_to_doctor_minutes': 30,
                'door_to_doctor_minutes': 45,
                'diagnosis_time_minutes': 60,
                'treatment_start_minutes': 120,
                'vital_signs_frequency': 8,
                'medication_adherence_score': 0.95,
                'pain_scores': [7, 6, 5, 4, 3],
                'satisfaction_score': 8.5,
                'total_cost': admission.estimated_cost,
                'insurance_coverage_amount': float(admission.estimated_cost) * 0.8,
                'patient_responsibility': float(admission.estimated_cost) * 0.2,
                'treatment_successful': True,
                'readmission_30_days': False,
                'complications_occurred': False
            }
        )
        if created:
            print(f"  📊 Metrics created for {admission.admission_id}")
    
    print(f"\n🎉 Sample data creation completed!")
    print(f"   - Created {len(patients)} patients")
    print(f"   - Created {len(admissions)} admissions")
    print(f"   - Created journey events for all admissions")
    print(f"   - Created AI insights for all admissions")
    print(f"   - Created metrics for all admissions")
    print(f"\n✅ Advanced Patient Management System is ready for testing!")
    print(f"   Backend: http://localhost:8000/patients/api/v2/")
    print(f"   Frontend: http://localhost:5173/dashboard-pages/dashboard-1")

if __name__ == '__main__':
    create_sample_data()
