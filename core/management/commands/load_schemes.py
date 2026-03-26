from django.core.management.base import BaseCommand
from core.models import GovernmentScheme

class Command(BaseCommand):
    help = 'Load sample government schemes'

    def handle(self, *args, **kwargs):
        schemes = [
            # Health
            {'name': 'Ayushman Bharat PM-JAY', 'category': 'health',
             'description': 'Health insurance coverage up to ₹5 lakh per family per year for secondary and tertiary care hospitalization.',
             'eligibility': 'Low income families. Must be listed in SECC database.',
             'link': 'https://pmjay.gov.in'},
            {'name': 'Pradhan Mantri Suraksha Bima Yojana', 'category': 'health',
             'description': 'Accidental death and disability insurance cover of ₹2 lakh at just ₹12/year premium.',
             'eligibility': 'Age 18–70 years with a bank account.',
             'link': 'https://financialservices.gov.in'},
            {'name': 'Janani Suraksha Yojana', 'category': 'health',
             'description': 'Cash assistance to pregnant women for institutional delivery to reduce maternal and infant mortality.',
             'eligibility': 'Pregnant women from BPL households.',
             'link': 'https://nhm.gov.in'},

            # Education
            {'name': 'PM Scholarship Scheme', 'category': 'education',
             'description': 'Scholarships for wards of ex-servicemen and ex-coast guard personnel for professional degree courses.',
             'eligibility': 'Wards of ex-servicemen. Minimum 60% in 12th standard.',
             'link': 'https://ksb.gov.in'},
            {'name': 'National Means-cum-Merit Scholarship', 'category': 'education',
             'description': '₹12,000 per year scholarship for meritorious students from economically weaker sections.',
             'eligibility': 'Class 9–12 students. Family income below ₹3.5 lakh/year.',
             'link': 'https://scholarships.gov.in'},
            {'name': 'Beti Bachao Beti Padhao', 'category': 'education',
             'description': 'Scheme to promote welfare of the girl child, prevent gender-biased sex selection and promote education.',
             'eligibility': 'Girl child education support. All families with girl children.',
             'link': 'https://wcd.nic.in'},

            # Employment
            {'name': 'PM Kaushal Vikas Yojana', 'category': 'employment',
             'description': 'Free skill training in various sectors to improve employability of youth across India.',
             'eligibility': 'Indian citizens aged 15–45 years seeking skill development.',
             'link': 'https://pmkvyofficial.org'},
            {'name': 'Mahatma Gandhi NREGA', 'category': 'employment',
             'description': 'Guarantees 100 days of wage employment per year to rural households whose adult members volunteer for unskilled manual work.',
             'eligibility': 'Rural households. Adult members willing to do manual work.',
             'link': 'https://nrega.nic.in'},
            {'name': 'PM Employment Generation Programme', 'category': 'employment',
             'description': 'Credit-linked subsidy scheme to set up new enterprises in non-farm sector. Subsidy up to 35%.',
             'eligibility': 'Individuals above 18 years with project cost up to ₹50 lakh.',
             'link': 'https://kviconline.gov.in'},

            # Welfare
            {'name': 'PM Awas Yojana', 'category': 'welfare',
             'description': 'Housing for all by providing financial assistance to construct pucca houses in rural and urban areas.',
             'eligibility': 'Families without pucca house. Priority to SC/ST and minorities.',
             'link': 'https://pmayg.nic.in'},
            {'name': 'National Social Assistance Programme', 'category': 'welfare',
             'description': 'Social pension for old age, widows, disabled persons and bereaved families below poverty line.',
             'eligibility': 'BPL households. Age above 60 for old age pension.',
             'link': 'https://nsap.nic.in'},
            {'name': 'PM Ujjwala Yojana', 'category': 'welfare',
             'description': 'Free LPG connections to women from BPL households to replace unclean cooking fuels.',
             'eligibility': 'Women from BPL households not having LPG connection.',
             'link': 'https://pmuy.gov.in'},

            # Agriculture
            {'name': 'PM Kisan Samman Nidhi', 'category': 'agriculture',
             'description': '₹6,000 per year direct income support to farmer families in three equal installments.',
             'eligibility': 'Small and marginal farmers owning up to 2 hectares of land.',
             'link': 'https://pmkisan.gov.in'},
            {'name': 'Pradhan Mantri Fasal Bima Yojana', 'category': 'agriculture',
             'description': 'Crop insurance scheme providing financial support to farmers suffering crop loss due to natural calamities.',
             'eligibility': 'All farmers growing notified crops in notified areas.',
             'link': 'https://pmfby.gov.in'},
            {'name': 'Kisan Credit Card', 'category': 'agriculture',
             'description': 'Short-term credit for agricultural operations at subsidized interest rate of 4% per annum.',
             'eligibility': 'Farmers, sharecroppers, oral lessees and tenant farmers.',
             'link': 'https://nabard.org'},
        ]

        count = 0
        for s in schemes:
            obj, created = GovernmentScheme.objects.get_or_create(
                name=s['name'],
                defaults={
                    'category':    s['category'],
                    'description': s['description'],
                    'eligibility': s['eligibility'],
                    'link':        s['link'],
                    'is_active':   True,
                }
            )
            if created:
                count += 1

        self.stdout.write(self.style.SUCCESS(f'✓ Loaded {count} schemes successfully!'))