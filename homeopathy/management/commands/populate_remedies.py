from django.core.management.base import BaseCommand
from homeopathy.models import HomeopathyRemedy

class Command(BaseCommand):
    help = 'Populate the database with sample homeopathic remedies'

    def handle(self, *args, **options):
        remedies_data = [
            {
                'name': 'Aconitum Napellus',
                'latin_name': 'Aconitum napellus',
                'common_name': 'Monkshood',
                'keynotes': [
                    'Sudden onset of symptoms',
                    'Fear and anxiety',
                    'Worse from cold dry wind',
                    'Restlessness and panic',
                    'Fever with dry skin'
                ],
                'mental_symptoms': [
                    'Intense fear and anxiety',
                    'Fear of death',
                    'Panic attacks',
                    'Restlessness',
                    'Sudden emotional outbursts'
                ],
                'physical_symptoms': [
                    'Sudden high fever',
                    'Dry cough',
                    'Headache from cold wind',
                    'Red, hot face',
                    'Thirst for cold water'
                ],
                'indications': [
                    'Acute infections',
                    'Shock and trauma',
                    'Panic disorders',
                    'Early stages of inflammation',
                    'Cold and flu onset'
                ],
                'miasm': 'acute',
                'constitution_affinity': ['phosphoric', 'sulphuric'],
                'common_potencies': '6C, 30C, 200C'
            },
            {
                'name': 'Arnica Montana',
                'latin_name': 'Arnica montana',
                'common_name': 'Mountain Arnica',
                'keynotes': [
                    'Trauma and injury',
                    'Bruised soreness',
                    'Says nothing is wrong when ill',
                    'Bed feels too hard',
                    'Fear of being touched'
                ],
                'mental_symptoms': [
                    'Denial of illness',
                    'Irritable when approached',
                    'Mental shock from injury',
                    'Hopelessness',
                    'Fear of sudden death'
                ],
                'physical_symptoms': [
                    'Bruising and soreness',
                    'Muscle aches',
                    'Sprains and strains',
                    'Bleeding under skin',
                    'General body soreness'
                ],
                'indications': [
                    'Physical trauma',
                    'Post-surgical recovery',
                    'Muscle soreness',
                    'Bruising',
                    'Shock from injury'
                ],
                'miasm': 'acute',
                'constitution_affinity': ['carbonic', 'silica'],
                'common_potencies': '6C, 30C, 200C, 1M'
            },
            {
                'name': 'Arsenicum Album',
                'latin_name': 'Arsenicum album',
                'common_name': 'White Arsenic',
                'keynotes': [
                    'Anxiety and restlessness',
                    'Perfectionist tendencies',
                    'Worse after midnight',
                    'Burning pains relieved by heat',
                    'Fear of being alone'
                ],
                'mental_symptoms': [
                    'Extreme anxiety',
                    'Fear of death',
                    'Restlessness despite weakness',
                    'Fastidious and controlling',
                    'Despair of recovery'
                ],
                'physical_symptoms': [
                    'Burning pains',
                    'Extreme weakness',
                    'Vomiting and diarrhea',
                    'Dry cough',
                    'Skin eruptions'
                ],
                'indications': [
                    'Anxiety disorders',
                    'Digestive problems',
                    'Asthma',
                    'Skin conditions',
                    'Food poisoning'
                ],
                'miasm': 'psoric',
                'constitution_affinity': ['phosphoric', 'natrum'],
                'common_potencies': '6C, 30C, 200C'
            },
            {
                'name': 'Belladonna',
                'latin_name': 'Atropa belladonna',
                'common_name': 'Deadly Nightshade',
                'keynotes': [
                    'Sudden violent onset',
                    'Hot, red, burning',
                    'Throbbing headaches',
                    'Dilated pupils',
                    'Delirium with fever'
                ],
                'mental_symptoms': [
                    'Violent delirium',
                    'Sees frightful images',
                    'Biting and striking',
                    'Hallucinations',
                    'Rage and fury'
                ],
                'physical_symptoms': [
                    'High fever',
                    'Throbbing headache',
                    'Red hot skin',
                    'Sore throat',
                    'Convulsions'
                ],
                'indications': [
                    'High fever',
                    'Headaches',
                    'Sore throat',
                    'Inflammatory conditions',
                    'Acute infections'
                ],
                'miasm': 'acute',
                'constitution_affinity': ['sulphuric', 'phosphoric'],
                'common_potencies': '6C, 30C, 200C'
            },
            {
                'name': 'Bryonia Alba',
                'latin_name': 'Bryonia alba',
                'common_name': 'White Bryony',
                'keynotes': [
                    'Worse from any motion',
                    'Wants to be left alone',
                    'Extremely thirsty',
                    'Irritable and angry',
                    'Slow onset of symptoms'
                ],
                'mental_symptoms': [
                    'Irritability',
                    'Wants to be quiet',
                    'Talks about business',
                    'Fear of poverty',
                    'Morose and taciturn'
                ],
                'physical_symptoms': [
                    'Dry mucous membranes',
                    'Constipation',
                    'Dry cough',
                    'Joint pains',
                    'Headache from movement'
                ],
                'indications': [
                    'Respiratory infections',
                    'Joint inflammation',
                    'Digestive problems',
                    'Headaches',
                    'Pneumonia'
                ],
                'miasm': 'psoric',
                'constitution_affinity': ['carbonic', 'natrum'],
                'common_potencies': '6C, 30C, 200C'
            },
            {
                'name': 'Calcarea Carbonica',
                'latin_name': 'Calcarea carbonica',
                'common_name': 'Calcium Carbonate',
                'keynotes': [
                    'Slow development',
                    'Obesity tendency',
                    'Cold and damp',
                    'Head sweats during sleep',
                    'Fear of heights'
                ],
                'mental_symptoms': [
                    'Anxiety about health',
                    'Fear of going insane',
                    'Obstinate',
                    'Forgetful',
                    'Easily frightened'
                ],
                'physical_symptoms': [
                    'Profuse perspiration',
                    'Cold hands and feet',
                    'Slow healing',
                    'Weak bones',
                    'Chronic fatigue'
                ],
                'indications': [
                    'Constitutional treatment',
                    'Chronic fatigue',
                    'Bone problems',
                    'Anxiety disorders',
                    'Digestive weakness'
                ],
                'miasm': 'psoric',
                'constitution_affinity': ['carbonic'],
                'common_potencies': '30C, 200C, 1M'
            },
            {
                'name': 'Chamomilla',
                'latin_name': 'Matricaria chamomilla',
                'common_name': 'German Chamomile',
                'keynotes': [
                    'Extreme irritability',
                    'Cannot bear pain',
                    'One cheek red, one pale',
                    'Wants to be carried',
                    'Capricious and snappish'
                ],
                'mental_symptoms': [
                    'Extreme irritability',
                    'Impatient',
                    'Nothing pleases',
                    'Quarrelsome',
                    'Hypersensitive to pain'
                ],
                'physical_symptoms': [
                    'Teething problems',
                    'Colic',
                    'Diarrhea',
                    'Earache',
                    'Toothache'
                ],
                'indications': [
                    'Teething in children',
                    'Colic',
                    'Toothache',
                    'Earache',
                    'Irritable conditions'
                ],
                'miasm': 'psoric',
                'constitution_affinity': ['phosphoric', 'natrum'],
                'common_potencies': '6C, 30C, 200C'
            },
            {
                'name': 'Ignatia Amara',
                'latin_name': 'Ignatia amara',
                'common_name': 'St. Ignatius Bean',
                'keynotes': [
                    'Grief and emotional shock',
                    'Contradictory symptoms',
                    'Sighing and sobbing',
                    'Sensation of lump in throat',
                    'Hysterical tendencies'
                ],
                'mental_symptoms': [
                    'Silent grief',
                    'Mood swings',
                    'Hysterical behavior',
                    'Brooding',
                    'Emotional numbness'
                ],
                'physical_symptoms': [
                    'Globus sensation',
                    'Nervous headaches',
                    'Muscle spasms',
                    'Digestive upset from emotion',
                    'Insomnia from grief'
                ],
                'indications': [
                    'Grief and loss',
                    'Emotional trauma',
                    'Nervous conditions',
                    'Hysteria',
                    'Digestive problems from stress'
                ],
                'miasm': 'psoric',
                'constitution_affinity': ['phosphoric', 'natrum'],
                'common_potencies': '30C, 200C, 1M'
            },
            {
                'name': 'Lycopodium Clavatum',
                'latin_name': 'Lycopodium clavatum',
                'common_name': 'Club Moss',
                'keynotes': [
                    'Lack of confidence',
                    'Worse 4-8 PM',
                    'Right-sided symptoms',
                    'Digestive weakness',
                    'Bloating after eating'
                ],
                'mental_symptoms': [
                    'Lack of self-confidence',
                    'Fear of responsibility',
                    'Dictatorial at home',
                    'Anticipatory anxiety',
                    'Intellectual but lacks confidence'
                ],
                'physical_symptoms': [
                    'Digestive problems',
                    'Gas and bloating',
                    'Liver problems',
                    'Kidney stones',
                    'Hair loss'
                ],
                'indications': [
                    'Digestive disorders',
                    'Liver problems',
                    'Anxiety disorders',
                    'Male pattern baldness',
                    'Kidney problems'
                ],
                'miasm': 'psoric',
                'constitution_affinity': ['phosphoric'],
                'common_potencies': '30C, 200C, 1M'
            },
            {
                'name': 'Natrum Muriaticum',
                'latin_name': 'Natrum muriaticum',
                'common_name': 'Table Salt',
                'keynotes': [
                    'Reserved and closed',
                    'Worse from consolation',
                    'Craving for salt',
                    'Periodic headaches',
                    'Effects of grief'
                ],
                'mental_symptoms': [
                    'Introversion',
                    'Difficulty expressing emotions',
                    'Dwells on past hurts',
                    'Aversion to sympathy',
                    'Depression from suppressed grief'
                ],
                'physical_symptoms': [
                    'Migraine headaches',
                    'Dry skin and mucous membranes',
                    'Irregular menstruation',
                    'Chronic fatigue',
                    'Cold sores'
                ],
                'indications': [
                    'Chronic headaches',
                    'Depression',
                    'Skin conditions',
                    'Menstrual problems',
                    'Chronic fatigue'
                ],
                'miasm': 'psoric',
                'constitution_affinity': ['natrum'],
                'common_potencies': '30C, 200C, 1M'
            },
            {
                'name': 'Nux Vomica',
                'latin_name': 'Strychnos nux-vomica',
                'common_name': 'Poison Nut',
                'keynotes': [
                    'Type A personality',
                    'Oversensitive to stimuli',
                    'Worse from overeating',
                    'Irritable and impatient',
                    'Chilly constitution'
                ],
                'mental_symptoms': [
                    'Extreme irritability',
                    'Impatience',
                    'Fault-finding',
                    'Competitive nature',
                    'Workaholic tendencies'
                ],
                'physical_symptoms': [
                    'Digestive problems',
                    'Constipation',
                    'Insomnia',
                    'Hangover symptoms',
                    'Back pain'
                ],
                'indications': [
                    'Digestive disorders',
                    'Insomnia',
                    'Stress-related conditions',
                    'Hangover',
                    'Constipation'
                ],
                'miasm': 'psoric',
                'constitution_affinity': ['sulphuric'],
                'common_potencies': '6C, 30C, 200C'
            },
            {
                'name': 'Phosphorus',
                'latin_name': 'Phosphorus',
                'common_name': 'Phosphorus',
                'keynotes': [
                    'Open and sympathetic',
                    'Bleeding tendency',
                    'Craving for cold drinks',
                    'Fears and anxieties',
                    'Tall and lean build'
                ],
                'mental_symptoms': [
                    'Open and communicative',
                    'Sympathetic nature',
                    'Fears of being alone',
                    'Fear of thunderstorms',
                    'Intuitive and psychic'
                ],
                'physical_symptoms': [
                    'Easy bleeding',
                    'Respiratory problems',
                    'Burning pains',
                    'Weak circulation',
                    'Nervous exhaustion'
                ],
                'indications': [
                    'Respiratory conditions',
                    'Bleeding disorders',
                    'Nervous exhaustion',
                    'Digestive problems',
                    'Anxiety disorders'
                ],
                'miasm': 'tubercular',
                'constitution_affinity': ['phosphoric'],
                'common_potencies': '30C, 200C, 1M'
            },
            {
                'name': 'Pulsatilla Nigricans',
                'latin_name': 'Pulsatilla nigricans',
                'common_name': 'Wind Flower',
                'keynotes': [
                    'Gentle and yielding',
                    'Changeable symptoms',
                    'Better in open air',
                    'Thirstless with fever',
                    'Weeps easily'
                ],
                'mental_symptoms': [
                    'Mild and gentle',
                    'Weeps easily',
                    'Seeks consolation',
                    'Changeable moods',
                    'Fear of abandonment'
                ],
                'physical_symptoms': [
                    'Changeable symptoms',
                    'Thick yellow discharge',
                    'Menstrual irregularities',
                    'Digestive problems',
                    'Varicose veins'
                ],
                'indications': [
                    'Hormonal problems',
                    'Respiratory infections',
                    'Digestive disorders',
                    'Emotional problems',
                    'Pregnancy-related issues'
                ],
                'miasm': 'psoric',
                'constitution_affinity': ['phosphoric', 'natrum'],
                'common_potencies': '30C, 200C, 1M'
            },
            {
                'name': 'Rhus Toxicodendron',
                'latin_name': 'Rhus toxicodendron',
                'common_name': 'Poison Ivy',
                'keynotes': [
                    'Better from motion',
                    'Worse from rest',
                    'Restlessness',
                    'Skin eruptions',
                    'Joint stiffness'
                ],
                'mental_symptoms': [
                    'Restlessness',
                    'Anxiety at night',
                    'Suspicious nature',
                    'Depression in evening',
                    'Desire to change position'
                ],
                'physical_symptoms': [
                    'Joint stiffness',
                    'Skin eruptions',
                    'Muscle aches',
                    'Back pain',
                    'Rheumatic pains'
                ],
                'indications': [
                    'Arthritis',
                    'Skin conditions',
                    'Muscle strains',
                    'Back pain',
                    'Restless leg syndrome'
                ],
                'miasm': 'psoric',
                'constitution_affinity': ['phosphoric', 'sulphuric'],
                'common_potencies': '6C, 30C, 200C'
            },
            {
                'name': 'Sepia Officinalis',
                'latin_name': 'Sepia officinalis',
                'common_name': 'Cuttlefish Ink',
                'keynotes': [
                    'Hormonal imbalances',
                    'Indifference to loved ones',
                    'Bearing down sensations',
                    'Better from exercise',
                    'Yellow-brown skin discoloration'
                ],
                'mental_symptoms': [
                    'Indifferent to family',
                    'Irritable with loved ones',
                    'Aversion to sympathy',
                    'Emotional exhaustion',
                    'Depression'
                ],
                'physical_symptoms': [
                    'Menstrual problems',
                    'Prolapse',
                    'Hot flashes',
                    'Chronic fatigue',
                    'Digestive problems'
                ],
                'indications': [
                    'Hormonal disorders',
                    'Menopause',
                    'Menstrual problems',
                    'Depression',
                    'Chronic fatigue'
                ],
                'miasm': 'psoric',
                'constitution_affinity': ['natrum'],
                'common_potencies': '30C, 200C, 1M'
            },
            {
                'name': 'Sulphur',
                'latin_name': 'Sulphur',
                'common_name': 'Sulphur',
                'keynotes': [
                    'Philosophical nature',
                    'Untidy appearance',
                    'Burning sensations',
                    'Worse from heat',
                    'Skin problems'
                ],
                'mental_symptoms': [
                    'Philosophical',
                    'Critical of others',
                    'Lazy and untidy',
                    'Theorizing',
                    'Selfish tendencies'
                ],
                'physical_symptoms': [
                    'Burning skin eruptions',
                    'Hot feet',
                    'Offensive discharges',
                    'Chronic conditions',
                    'Digestive problems'
                ],
                'indications': [
                    'Chronic skin conditions',
                    'Digestive disorders',
                    'Constitutional treatment',
                    'Chronic conditions',
                    'Mental disorders'
                ],
                'miasm': 'psoric',
                'constitution_affinity': ['sulphuric'],
                'common_potencies': '30C, 200C, 1M'
            }
        ]

        created_count = 0
        for remedy_data in remedies_data:
            remedy, created = HomeopathyRemedy.objects.get_or_create(
                name=remedy_data['name'],
                defaults=remedy_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created remedy: {remedy.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Remedy already exists: {remedy.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully processed {len(remedies_data)} remedies. '
                f'Created {created_count} new remedies.'
            )
        )
