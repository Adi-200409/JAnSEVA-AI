import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smart_community.settings')
django.setup()

from core.models import GovernmentScheme

mapping = {
    'health': 'Health & Wellness',
    'education': 'Education & Learning', 
    'employment': 'Skills & Employment',
    'welfare': 'Social Welfare & Empowerment',
    'agriculture': 'Agriculture',
}

for old, new in mapping.items():
    count = GovernmentScheme.objects.filter(category__iexact=old).update(category=new)
    print(f"Updated {count} schemes from {old} to {new}")

print("Current Distinct Categories in DB:")
for c in GovernmentScheme.objects.values('category').distinct():
    print(c['category'])
