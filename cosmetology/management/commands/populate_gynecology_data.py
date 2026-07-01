from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
import json
from cosmetology.models import (
    CosmetologyClient,
    CosmeticGynecologyClient, CosmeticGynecologyTreatment,
    CosmeticGynecologyConsultation, CosmeticGynecologyTreatmentPlan,
    CosmeticGynecologyProgress
)

User = get_user_model()


class Command(BaseCommand):
    help = 'Populate cosmetic gynecology sample data with AI-powered features'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting cosmetic gynecology data population...')
        )

        # Create sample treatments first
        treatments = self._create_sample_treatments()
        
        # Create sample clients (we'll link to existing cosmetology clients if available)
        gynecology_clients = self._create_sample_gynecology_clients()
        
        # Create sample consultations
        consultations = self._create_sample_consultations(gynecology_clients, treatments)
        
        # Create sample treatment plans
        treatment_plans = self._create_sample_treatment_plans(gynecology_clients, treatments)
        
        # Create sample progress records
        self._create_sample_progress_records(gynecology_clients, treatment_plans)

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully populated cosmetic gynecology data:\n'
                f'- {len(treatments)} treatments\n'
                f'- {len(gynecology_clients)} specialized clients\n'
                f'- {len(consultations)} consultations\n'
                f'- {len(treatment_plans)} treatment plans\n'
                f'- Progress records created'
            )
        )

    def _create_sample_treatments(self):
        """Create sample cosmetic gynecology treatments"""
        treatments_data = [
            {
                'name': 'Vaginal Rejuvenation Laser Therapy',
                'category': 'non_invasive',
                'technology_used': 'laser_co2',
                'description': 'Non-invasive laser treatment for vaginal tissue tightening and rejuvenation using CO2 fractional laser technology',
                'indications': 'Vaginal laxity, decreased sensation, post-childbirth changes, mild incontinence',
                'contraindications': 'Pregnancy, active infections, bleeding disorders, certain medications',
                'duration_minutes': 45,
                'sessions_required': 3,
                'interval_between_sessions': 28,
                'downtime_days': 3,
                'recovery_instructions': 'Avoid sexual activity for 48 hours, use recommended lubricants, follow hygiene protocols',
                'follow_up_schedule': 'Follow-up at 2 weeks, 6 weeks, and 3 months post-treatment',
                'success_rate': 87.5,
                'side_effects': 'Mild discomfort, temporary swelling, rare risk of infection',
                'price_per_session': 2500.00,
                'package_pricing': {"3_sessions": 6750.00, "5_sessions": 10500.00},
                'ai_suitability_criteria': {
                    "min_age": 25,
                    "max_age": 65,
                    "contraindications": ["pregnancy", "active_infection"],
                    "ideal_candidates": ["post_childbirth", "mild_laxity"]
                },
                'is_active': True
            },
            {
                'name': 'MonaLisa Touch Treatment',
                'category': 'minimally_invasive',
                'technology_used': 'laser_co2',
                'description': 'CO2 laser therapy specifically designed for vaginal health and rejuvenation',
                'indications': 'Vaginal dryness, atrophy, post-menopausal changes, discomfort during intimacy',
                'contraindications': 'Active genital infections, pregnancy, cancer history in treatment area',
                'duration_minutes': 30,
                'sessions_required': 3,
                'interval_between_sessions': 21,
                'downtime_days': 2,
                'recovery_instructions': 'Minimal activity restrictions, avoid hot baths for 24 hours',
                'follow_up_schedule': 'Follow-up at 1 week, 4 weeks, and 12 weeks',
                'success_rate': 92.3,
                'side_effects': 'Minimal discomfort, slight discharge for 24-48 hours',
                'price_per_session': 1800.00,
                'package_pricing': {"3_sessions": 4860.00},
                'ai_suitability_criteria': {
                    "min_age": 30,
                    "max_age": 70,
                    "ideal_conditions": ["menopause", "vaginal_dryness"],
                    "contraindications": ["pregnancy", "cancer_history"]
                },
                'is_active': True
            },
            {
                'name': 'Cosmetic Labiaplasty',
                'category': 'surgical',
                'technology_used': 'surgical_procedure',
                'description': 'Surgical procedure to reshape and reduce labial size for aesthetic and functional purposes',
                'indications': 'Labial asymmetry, hypertrophy, discomfort with clothing or activities',
                'contraindications': 'Pregnancy, bleeding disorders, unrealistic expectations, active infections',
                'duration_minutes': 90,
                'sessions_required': 1,
                'interval_between_sessions': 0,
                'downtime_days': 14,
                'recovery_instructions': 'Complete rest for 48 hours, avoid strenuous activity for 2 weeks, follow wound care instructions',
                'follow_up_schedule': 'Follow-up at 1 week, 2 weeks, 6 weeks, and 3 months',
                'success_rate': 94.2,
                'side_effects': 'Swelling, bruising, temporary numbness, rare scarring',
                'price_per_session': 5500.00,
                'package_pricing': {},
                'ai_suitability_criteria': {
                    "min_age": 18,
                    "max_age": 55,
                    "psychological_evaluation": "required",
                    "realistic_expectations": "essential"
                },
                'is_active': True
            },
            {
                'name': 'O-Shot (Orgasm Shot)',
                'category': 'minimally_invasive',
                'technology_used': 'platelet_therapy',
                'description': 'PRP injection therapy for enhanced sexual function and vaginal rejuvenation',
                'indications': 'Decreased sexual sensation, difficulty achieving orgasm, mild incontinence',
                'contraindications': 'Blood disorders, active infections, anticoagulant medications',
                'duration_minutes': 75,
                'sessions_required': 1,
                'interval_between_sessions': 90,
                'downtime_days': 1,
                'recovery_instructions': 'Avoid sexual activity for 24 hours, minimal activity restrictions',
                'follow_up_schedule': 'Follow-up at 2 weeks, 6 weeks, and 3 months',
                'success_rate': 83.7,
                'side_effects': 'Mild swelling, temporary discomfort at injection site',
                'price_per_session': 3200.00,
                'package_pricing': {"2_sessions": 5760.00},
                'ai_suitability_criteria': {
                    "min_age": 25,
                    "max_age": 60,
                    "blood_work": "required",
                    "contraindications": ["blood_disorders", "anticoagulants"]
                },
                'is_active': True
            },
            {
                'name': 'Vaginal Tightening with Radiofrequency',
                'category': 'non_invasive',
                'technology_used': 'radiofrequency',
                'description': 'Non-surgical radiofrequency treatment for vaginal tightening and rejuvenation',
                'indications': 'Vaginal laxity, decreased sensation, post-pregnancy changes',
                'contraindications': 'Pregnancy, pacemaker, metal implants in treatment area',
                'duration_minutes': 40,
                'sessions_required': 4,
                'interval_between_sessions': 14,
                'downtime_days': 1,
                'recovery_instructions': 'Avoid sexual activity for 48 hours, normal activities can be resumed immediately',
                'follow_up_schedule': 'Follow-up at 2 weeks and 8 weeks',
                'success_rate': 79.8,
                'side_effects': 'Mild warmth sensation, temporary redness',
                'price_per_session': 2000.00,
                'package_pricing': {"4_sessions": 7200.00, "6_sessions": 10200.00},
                'ai_suitability_criteria': {
                    "min_age": 25,
                    "max_age": 60,
                    "contraindications": ["pacemaker", "metal_implants"],
                    "ideal_candidates": ["mild_to_moderate_laxity"]
                },
                'is_active': True
            },
            {
                'name': 'Intimate Area Aesthetic Enhancement',
                'category': 'combination',
                'technology_used': 'filler_injection',
                'description': 'Hyaluronic acid filler injections for vulvar area enhancement and rejuvenation',
                'indications': 'Volume loss, asymmetry, aesthetic enhancement of intimate areas',
                'contraindications': 'Active infections, autoimmune disorders, bleeding disorders',
                'duration_minutes': 60,
                'sessions_required': 1,
                'interval_between_sessions': 180,
                'downtime_days': 3,
                'recovery_instructions': 'Avoid pressure on treated area for 48 hours, ice application as needed',
                'follow_up_schedule': 'Follow-up at 2 weeks and 3 months',
                'success_rate': 88.4,
                'side_effects': 'Swelling, bruising, temporary asymmetry',
                'price_per_session': 2800.00,
                'package_pricing': {},
                'ai_suitability_criteria': {
                    "min_age": 21,
                    "max_age": 65,
                    "filler_tolerance": "required",
                    "realistic_expectations": "essential"
                },
                'is_active': True
            }
        ]

        treatments = []
        for treatment_data in treatments_data:
            treatment, created = CosmeticGynecologyTreatment.objects.get_or_create(
                name=treatment_data['name'],
                defaults=treatment_data
            )
            treatments.append(treatment)
            if created:
                self.stdout.write(f'Created treatment: {treatment.name}')

        return treatments

    def _create_sample_gynecology_clients(self):
        """Create sample cosmetic gynecology clients"""
        
        # First, try to get existing cosmetology clients
        cosmetology_clients = list(CosmetologyClient.objects.all()[:3])
        
        # If no cosmetology clients exist, create some basic ones
        if not cosmetology_clients:
            basic_clients_data = [
                {
                    'name': 'Sarah Johnson',
                    'age': 39,
                    'gender': 'female',
                    'email': 'sarah.johnson@email.com',
                    'phone': '+1-555-0101',
                    'address': '123 Wellness Ave, Health City, HC 12345',
                    'skin_type': 'normal',
                    'hair_type': 'wavy',
                    'allergies': 'No known allergies',
                    'skin_concerns': ['aging', 'fine_lines'],
                    'hair_concerns': ['dryness']
                },
                {
                    'name': 'Maria Rodriguez',
                    'age': 34,
                    'gender': 'female',
                    'email': 'maria.rodriguez@email.com',
                    'phone': '+1-555-0201',
                    'address': '456 Beauty Blvd, Aesthetic Town, AT 67890',
                    'skin_type': 'combination',
                    'hair_type': 'curly',
                    'allergies': 'Penicillin allergy',
                    'skin_concerns': ['acne', 'hyperpigmentation'],
                    'hair_concerns': ['frizz', 'damaged']
                },
                {
                    'name': 'Jennifer Chen',
                    'age': 42,
                    'gender': 'female',
                    'email': 'jennifer.chen@email.com',
                    'phone': '+1-555-0301',
                    'address': '789 Confidence St, Wellness Park, WP 54321',
                    'skin_type': 'dry',
                    'hair_type': 'straight',
                    'allergies': 'Latex allergy',
                    'skin_concerns': ['wrinkles', 'sun_damage'],
                    'hair_concerns': ['thinning']
                }
            ]
            
            for client_data in basic_clients_data:
                # Get or create a default user for created_by field
                default_user, _ = User.objects.get_or_create(
                    username='admin',
                    defaults={
                        'email': 'admin@healthcare.com',
                        'first_name': 'System',
                        'last_name': 'Administrator',
                        'role': 'admin'
                    }
                )
                client_data['created_by'] = default_user
                
                client, created = CosmetologyClient.objects.get_or_create(
                    email=client_data['email'],
                    defaults=client_data
                )
                cosmetology_clients.append(client)

        # Create gynecology specialization data for these clients
        gynecology_clients_data = [
            {
                'age_at_first_pregnancy': 28,
                'number_of_pregnancies': 2,
                'number_of_deliveries': 2,
                'c_section_history': False,
                'menopause_status': False,
                'hormonal_therapy': False,
                'primary_concerns': ['vaginal_laxity', 'decreased_sensation', 'confidence_issues'],
                'concern_severity': 6,
                'gynecological_conditions': 'History of two pregnancies, no complications. Regular gynecological checkups.',
                'current_medications': 'Multivitamin, Omega-3 supplements',
                'previous_treatments': 'none',
                'treatment_goals': 'Restore pre-pregnancy vaginal tightness and sensation. Improve overall confidence and comfort.',
                'lifestyle_factors': 'Regular exercise, healthy diet, moderate stress levels',
                'ai_risk_assessment': {
                    "risk_level": "LOW",
                    "risk_score": 1,
                    "risk_factors": ["Minimal risk factors identified"],
                    "recommendations": [
                        "Standard treatment protocols applicable",
                        "Routine monitoring sufficient",
                        "Good candidate for cosmetic procedures"
                    ],
                    "analysis_date": "2024-12-19T10:30:00",
                    "requires_specialist_consultation": False
                },
                'ai_treatment_recommendations': {
                    "primary_recommendations": ["Vaginal Rejuvenation Laser Therapy", "MonaLisa Touch Treatment"],
                    "alternative_options": ["Radiofrequency Treatment"],
                    "timeline": "12-16 weeks for complete treatment series"
                }
            },
            {
                'age_at_first_pregnancy': None,
                'number_of_pregnancies': 0,
                'number_of_deliveries': 0,
                'c_section_history': False,
                'menopause_status': False,
                'hormonal_therapy': True,
                'primary_concerns': ['labial_asymmetry', 'aesthetic_enhancement', 'clothing_discomfort'],
                'concern_severity': 7,
                'gynecological_conditions': 'Mild endometriosis managed with medication. History of irregular periods.',
                'current_medications': 'Birth control pills, Iron supplements',
                'previous_treatments': 'hormone_therapy',
                'treatment_satisfaction': 6,
                'treatment_goals': 'Achieve symmetrical labial appearance and eliminate discomfort with tight clothing.',
                'lifestyle_factors': 'Active lifestyle, planning pregnancy in future',
                'ai_risk_assessment': {
                    "risk_level": "MEDIUM",
                    "risk_score": 3,
                    "risk_factors": ["Chronic medical conditions", "Hormonal medication use"],
                    "recommendations": [
                        "Specialist consultation recommended",
                        "Additional diagnostic tests may be needed",
                        "Modified treatment protocols",
                        "Regular monitoring required",
                        "Coordinate with gynecologist regarding endometriosis"
                    ],
                    "analysis_date": "2024-12-19T10:30:00",
                    "requires_specialist_consultation": True
                },
                'ai_treatment_recommendations': {
                    "primary_recommendations": ["Cosmetic Labiaplasty"],
                    "considerations": ["Pre-operative endometriosis evaluation"],
                    "timeline": "6-8 weeks for complete recovery"
                }
            },
            {
                'age_at_first_pregnancy': 29,
                'number_of_pregnancies': 1,
                'number_of_deliveries': 1,
                'c_section_history': True,
                'menopause_status': False,
                'hormonal_therapy': False,
                'primary_concerns': ['vaginal_dryness', 'decreased_comfort', 'post_pregnancy_changes'],
                'concern_severity': 5,
                'gynecological_conditions': 'Hypertension controlled with medication. Previous C-section.',
                'current_medications': 'Lisinopril 10mg daily, Prenatal vitamins',
                'previous_treatments': 'topical_treatments',
                'treatment_satisfaction': 4,
                'treatment_goals': 'Improve vaginal comfort and moisture. Address post-pregnancy changes.',
                'lifestyle_factors': 'Planning second pregnancy, moderate exercise routine',
                'ai_risk_assessment': {
                    "risk_level": "MEDIUM",
                    "risk_score": 4,
                    "risk_factors": ["Chronic medical conditions", "Previous surgical history"],
                    "recommendations": [
                        "Specialist consultation recommended",
                        "Modified treatment protocols",
                        "Regular monitoring required",
                        "Coordinate with primary care physician",
                        "Review surgical history and healing patterns"
                    ],
                    "analysis_date": "2024-12-19T10:30:00",
                    "requires_specialist_consultation": True
                },
                'ai_treatment_recommendations': {
                    "primary_recommendations": ["MonaLisa Touch Treatment", "O-Shot Therapy"],
                    "considerations": ["Hypertension monitoring during treatment"],
                    "timeline": "8-12 weeks for optimal results"
                }
            }
        ]

        gynecology_clients = []
        for i, gyn_data in enumerate(gynecology_clients_data):
            if i < len(cosmetology_clients):
                cosmetology_client = cosmetology_clients[i]
                gyn_client, created = CosmeticGynecologyClient.objects.get_or_create(
                    cosmetology_client=cosmetology_client,
                    defaults=gyn_data
                )
                gynecology_clients.append(gyn_client)
                if created:
                    self.stdout.write(f'Created gynecology profile for: {cosmetology_client.name}')

        return gynecology_clients

    def _create_sample_consultations(self, gynecology_clients, treatments):
        """Create sample consultations"""
        consultations_data = [
            {
                'status': 'completed',
                'chief_complaints': 'Interested in vaginal rejuvenation after childbirth. Experiencing decreased sensation and confidence issues.',
                'physical_examination': 'Normal external genitalia. Mild vaginal laxity noted. No signs of infection or abnormalities.',
                'client_expectations': 'Patient hopes to regain pre-pregnancy sensation and comfort. Realistic expectations discussed.',
                'psychological_readiness': 8,
                'doctor_notes': 'Good candidate for vaginal rejuvenation procedures. Patient educated on options and timeline.',
                'consultation_notes': 'Recommend laser therapy treatment series. Discuss expectations and timeline.',
                'ai_analysis_complete': True,
                'ai_risk_score': 2.5,
                'ai_recommended_treatments': ['Vaginal Rejuvenation Laser Therapy', 'MonaLisa Touch Treatment'],
                'ai_treatment_timeline': {
                    "initial_consultation": "completed",
                    "treatment_start": "2-3 weeks",
                    "first_results": "4-6 weeks",
                    "completion": "12-16 weeks"
                },
                'ai_expected_outcomes': {
                    "success_probability": 87,
                    "satisfaction_prediction": "high",
                    "side_effects_risk": "low"
                },
                'ai_contraindications': []
            },
            {
                'status': 'completed',
                'chief_complaints': 'Seeking labiaplasty consultation due to aesthetic concerns and discomfort with tight clothing.',
                'physical_examination': 'Asymmetrical labia minora with mild hypertrophy. No signs of infection.',
                'client_expectations': 'Patient desires symmetrical appearance and elimination of discomfort. Realistic expectations.',
                'psychological_readiness': 9,
                'doctor_notes': 'Candidate for labiaplasty. Realistic expectations discussed. Surgical evaluation needed.',
                'consultation_notes': 'Surgical consultation scheduled. Pre-operative evaluation needed.',
                'ai_analysis_complete': True,
                'ai_risk_score': 3.2,
                'ai_recommended_treatments': ['Cosmetic Labiaplasty'],
                'ai_treatment_timeline': {
                    "pre_operative": "2-3 weeks",
                    "surgery_date": "4 weeks",
                    "initial_recovery": "2 weeks",
                    "full_recovery": "6-8 weeks"
                },
                'ai_expected_outcomes': {
                    "success_probability": 94,
                    "satisfaction_prediction": "very_high",
                    "complication_risk": "low"
                },
                'ai_contraindications': []
            },
            {
                'status': 'follow_up',
                'chief_complaints': 'Follow-up after MonaLisa Touch treatment. Experiencing mild improvement in symptoms.',
                'physical_examination': 'Improved vaginal tissue quality. No adverse effects noted.',
                'client_expectations': 'Patient pleased with initial results. Expectations being met.',
                'psychological_readiness': 9,
                'doctor_notes': 'Good response to treatment. Continue with planned series.',
                'consultation_notes': 'Complete remaining treatments in series. Monitor progress.',
                'ai_analysis_complete': True,
                'ai_risk_score': 1.8,
                'ai_recommended_treatments': ['Continue MonaLisa Touch series'],
                'ai_treatment_timeline': {
                    "current_status": "session_2_complete",
                    "next_session": "4 weeks",
                    "series_completion": "8-10 weeks"
                },
                'ai_expected_outcomes': {
                    "success_probability": 92,
                    "current_satisfaction": "good",
                    "final_satisfaction_prediction": "very_high"
                },
                'ai_contraindications': []
            }
        ]

        consultations = []
        for i, consultation_data in enumerate(consultations_data):
            if i < len(gynecology_clients):
                consultation_data['client'] = gynecology_clients[i]
                consultation_data['consultation_date'] = timezone.now() - timedelta(days=i*7)
                
                consultation = CosmeticGynecologyConsultation.objects.create(**consultation_data)
                consultations.append(consultation)
                self.stdout.write(f'Created consultation for: {gynecology_clients[i].cosmetology_client.name}')

        return consultations

    def _create_sample_treatment_plans(self, gynecology_clients, treatments):
        """Create sample treatment plans"""
        from datetime import date
        
        treatment_plans_data = [
            {
                'plan_name': 'Vaginal Rejuvenation Comprehensive Plan',
                'status': 'in_progress',
                'start_date': date.today(),
                'estimated_completion': date.today() + timedelta(weeks=12),
                'total_sessions': 3,
                'session_interval_days': 28,
                'total_estimated_cost': 7500.00,
                'ai_plan_optimization': {
                    "optimization_date": "2024-12-19T12:00:00",
                    "ai_version": "1.0",
                    "effectiveness_analysis": {
                        "current_score": 75,
                        "improvement_potential": 15,
                        "key_metrics": {
                            "treatment_complexity": "Medium",
                            "duration_assessment": "Appropriate duration"
                        }
                    },
                    "optimization_suggestions": [],
                    "outcome_predictions": {
                        "success_probability": 85,
                        "timeline_predictions": {
                            "first_visible_results": "3 weeks",
                            "significant_improvement": "6 weeks",
                            "final_results": "12 weeks"
                        },
                        "risk_assessment": {
                            "complication_risk": "Low",
                            "revision_probability": "15%",
                            "satisfaction_prediction": "High"
                        }
                    }
                },
                'ai_success_probability': 85.0,
                'informed_consent': True,
                'consent_date': timezone.now()
            },
            {
                'plan_name': 'Labiaplasty Surgical Plan',
                'status': 'approved',
                'start_date': date.today() + timedelta(weeks=2),
                'estimated_completion': date.today() + timedelta(weeks=8),
                'total_sessions': 1,
                'session_interval_days': 0,
                'total_estimated_cost': 6500.00,
                'ai_plan_optimization': {
                    "optimization_date": "2024-12-19T12:15:00",
                    "ai_version": "1.0",
                    "effectiveness_analysis": {
                        "current_score": 80,
                        "improvement_potential": 10,
                        "key_metrics": {
                            "treatment_complexity": "High",
                            "duration_assessment": "Short treatment period"
                        }
                    },
                    "optimization_suggestions": [
                        {
                            "category": "Duration Optimization",
                            "suggestion": "Extended recovery monitoring recommended",
                            "priority": "Medium"
                        }
                    ],
                    "outcome_predictions": {
                        "success_probability": 90,
                        "timeline_predictions": {
                            "first_visible_results": "2 weeks",
                            "significant_improvement": "3 weeks",
                            "final_results": "6 weeks"
                        },
                        "risk_assessment": {
                            "complication_risk": "Low",
                            "revision_probability": "10%",
                            "satisfaction_prediction": "High"
                        }
                    }
                },
                'ai_success_probability': 90.0,
                'informed_consent': True,
                'consent_date': timezone.now()
            },
            {
                'plan_name': 'MonaLisa Touch Series',
                'status': 'in_progress',
                'start_date': date.today() - timedelta(weeks=2),
                'estimated_completion': date.today() + timedelta(weeks=16),
                'total_sessions': 3,
                'session_interval_days': 42,
                'total_estimated_cost': 5400.00,
                'ai_plan_optimization': {
                    "optimization_date": "2024-12-19T12:30:00",
                    "ai_version": "1.0",
                    "effectiveness_analysis": {
                        "current_score": 70,
                        "improvement_potential": 20,
                        "key_metrics": {
                            "treatment_complexity": "Medium",
                            "duration_assessment": "Appropriate duration"
                        }
                    },
                    "optimization_suggestions": [
                        {
                            "category": "Frequency Optimization",
                            "suggestion": "Consider increasing session frequency for faster results",
                            "priority": "Low"
                        }
                    ],
                    "outcome_predictions": {
                        "success_probability": 80,
                        "timeline_predictions": {
                            "first_visible_results": "4 weeks",
                            "significant_improvement": "9 weeks",
                            "final_results": "18 weeks"
                        },
                        "risk_assessment": {
                            "complication_risk": "Low",
                            "revision_probability": "20%",
                            "satisfaction_prediction": "High"
                        }
                    }
                },
                'ai_success_probability': 80.0,
                'informed_consent': True,
                'consent_date': timezone.now()
            }
        ]

        treatment_plans = []
        for i, plan_data in enumerate(treatment_plans_data):
            if i < len(gynecology_clients) and i < len(treatments):
                plan_data['client'] = gynecology_clients[i]
                
                # Create consultation first for the plan
                consultation_data = {
                    'client': gynecology_clients[i],
                    'consultation_date': timezone.now() - timedelta(days=i*7),
                    'status': 'completed',
                    'chief_complaints': f'Initial consultation for {plan_data["plan_name"]}',
                    'physical_examination': 'Comprehensive examination completed',
                    'client_expectations': 'Realistic expectations discussed and documented',
                    'psychological_readiness': 8,
                    'ai_analysis_complete': True,
                    'ai_risk_score': 2.5
                }
                
                consultation = CosmeticGynecologyConsultation.objects.create(**consultation_data)
                plan_data['consultation'] = consultation
                
                treatment_plan = CosmeticGynecologyTreatmentPlan.objects.create(**plan_data)
                
                # Add treatments using ManyToMany relationship
                treatment_plan.primary_treatments.add(treatments[i])
                if len(treatments) > i + 1:
                    treatment_plan.supporting_treatments.add(treatments[i + 1])
                
                treatment_plans.append(treatment_plan)
                self.stdout.write(f'Created treatment plan for: {gynecology_clients[i].cosmetology_client.name}')

        return treatment_plans

    def _create_sample_progress_records(self, gynecology_clients, treatment_plans):
        """Create sample progress records"""
        progress_records_data = [
            {
                'session_number': 1,
                'session_notes': 'First session completed successfully. Patient tolerated treatment well.',
                'client_comfort_level': 8,
                'client_satisfaction': 8,
                'client_feedback': 'Patient reports significant improvement in comfort and confidence. Very satisfied with results so far.',
                'side_effects_reported': 'Mild discomfort for first 24 hours, resolved completely',
                'healing_progress': 9,
                'recovery_notes': 'Excellent healing response. No complications noted.',
                'next_session_date': timezone.now() + timedelta(weeks=4),
                'homecare_instructions': 'Continue with recommended skincare routine. Avoid sexual activity for 48 hours.',
                'follow_up_required': True,
                'ai_improvement_score': 65.0,
                'ai_progress_analysis': {
                    "analysis_date": "2024-12-19T13:00:00",
                    "ai_version": "1.0",
                    "trend_analysis": {
                        "improvement_rate": "Good",
                        "side_effects_profile": "Favorable"
                    },
                    "satisfaction_analysis": {
                        "satisfaction_alignment": "High - Patient satisfaction aligns with clinical progress",
                        "expectation_management": "Excellent - Expectations well managed"
                    },
                    "outcome_predictions": {
                        "final_improvement_range": "80-95%",
                        "outcome_confidence": "High",
                        "final_satisfaction": "High satisfaction expected"
                    },
                    "recommendations": [
                        {
                            "category": "Treatment Continuation",
                            "recommendation": "Continue current treatment protocol",
                            "priority": "Low"
                        }
                    ]
                }
            },
            {
                'session_number': 1,
                'session_notes': 'Initial consultation and assessment completed. Surgical planning discussed.',
                'client_comfort_level': 7,
                'client_satisfaction': 7,
                'client_feedback': 'Good progress noted. Patient adjusting well to treatment planning. Continue as planned.',
                'side_effects_reported': 'Some anxiety initially, mild pre-operative concerns. All within expected range.',
                'healing_progress': 8,
                'recovery_notes': 'Pre-operative assessment completed successfully.',
                'next_session_date': timezone.now() + timedelta(weeks=6),
                'homecare_instructions': 'Follow pre-operative instructions. Attend all scheduled appointments.',
                'follow_up_required': True,
                'ai_improvement_score': 45.0,
                'ai_progress_analysis': {
                    "analysis_date": "2024-12-19T13:15:00",
                    "ai_version": "1.0",
                    "trend_analysis": {
                        "improvement_rate": "Moderate",
                        "side_effects_profile": "Acceptable"
                    },
                    "satisfaction_analysis": {
                        "satisfaction_alignment": "High - Patient satisfaction aligns with clinical progress",
                        "expectation_management": "Good - Minor expectation adjustments may be needed"
                    },
                    "outcome_predictions": {
                        "final_improvement_range": "60-80%",
                        "outcome_confidence": "Moderate",
                        "final_satisfaction": "High satisfaction expected"
                    },
                    "recommendations": []
                }
            },
            {
                'session_number': 2,
                'session_notes': 'Second session of MonaLisa Touch completed. Excellent response noted.',
                'client_comfort_level': 9,
                'client_satisfaction': 9,
                'client_feedback': 'Excellent response to treatment. Patient extremely pleased with results. Continue current protocol.',
                'side_effects_reported': 'No significant side effects reported',
                'healing_progress': 9,
                'recovery_notes': 'Outstanding healing response. Patient exceeding expectations.',
                'next_session_date': timezone.now() + timedelta(weeks=6),
                'homecare_instructions': 'Continue current routine. Maintain good hygiene.',
                'follow_up_required': True,
                'ai_improvement_score': 75.0,
                'ai_progress_analysis': {
                    "analysis_date": "2024-12-19T13:30:00",
                    "ai_version": "1.0",
                    "trend_analysis": {
                        "improvement_rate": "Excellent",
                        "side_effects_profile": "Favorable"
                    },
                    "satisfaction_analysis": {
                        "satisfaction_alignment": "High - Patient satisfaction aligns with clinical progress",
                        "expectation_management": "Excellent - Expectations well managed"
                    },
                    "outcome_predictions": {
                        "final_improvement_range": "80-95%",
                        "outcome_confidence": "High",
                        "final_satisfaction": "High satisfaction expected"
                    },
                    "recommendations": [
                        {
                            "category": "Treatment Continuation",
                            "recommendation": "Continue current treatment protocol",
                            "priority": "Low"
                        }
                    ]
                }
            }
        ]

        for i, progress_data in enumerate(progress_records_data):
            if i < len(gynecology_clients) and i < len(treatment_plans):
                progress_data['treatment_plan'] = treatment_plans[i]
                progress_data['session_date'] = timezone.now() - timedelta(days=i*3)
                
                # Get the primary treatment for this plan
                primary_treatment = treatment_plans[i].primary_treatments.first()
                if primary_treatment:
                    progress_data['treatment_performed'] = primary_treatment
                
                progress_record = CosmeticGynecologyProgress.objects.create(**progress_data)
                self.stdout.write(f'Created progress record for: {gynecology_clients[i].cosmetology_client.name}')
