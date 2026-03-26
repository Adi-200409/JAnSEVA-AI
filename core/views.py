import json
import urllib.error
import urllib.request

from django.conf                    import settings
from django.contrib.auth            import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models               import Q
from django.http                    import JsonResponse
from django.shortcuts               import render, redirect
from django.views.decorators.http   import require_POST, require_http_methods
from django.core.mail               import send_mail

from .models import SmartUser, UserProfile, GovernmentScheme, ChatMessage, JobRecommendation, UserFeedback, PasswordResetToken, SavedScheme


# ── Pages ─────────────────────────────────────────────────────────────
def index(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'index.html')


@login_required
def dashboard(request):
    # Real statistics from the official MyScheme portal (https://www.myscheme.gov.in/)
    total_count = '4660+'
    central_count = '640+'
    state_count = '4020+'
    
    return render(request, 'dashboard.html', {
        'user': request.user,
        'central_count': central_count,
        'state_count': state_count,
        'total_count': total_count
    })


# ── Auth APIs ─────────────────────────────────────────────────────────
@require_POST
def api_signup(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid data.'}, status=400)

    full_name = data.get('full_name', '').strip()
    email     = data.get('email', '').strip().lower()
    password  = data.get('password', '')

    if not full_name or len(full_name) < 2:
        return JsonResponse({'success': False, 'error': 'Full name is required.'}, status=400)
    if not email or '@' not in email:
        return JsonResponse({'success': False, 'error': 'A valid email is required.'}, status=400)
    if len(password) < 8:
        return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters.'}, status=400)
    if SmartUser.objects.filter(email=email).exists():
        return JsonResponse({'success': False, 'error': 'Account already exists.'}, status=409)

    user = SmartUser.objects.create_user(email=email, full_name=full_name, password=password)
    UserProfile.objects.create(user=user)
    return JsonResponse({'success': True})


@require_POST
def api_login(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid data.'}, status=400)

    email    = data.get('email', '').strip().lower()
    password = data.get('password', '')

    user = authenticate(request, username=email, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Incorrect email or password.'}, status=401)


@require_POST
@login_required
def api_logout(request):
    logout(request)
    return redirect('index')


# ── Profile APIs ──────────────────────────────────────────────────────
@require_POST
@login_required
def api_submit_feedback(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid data.'}, status=400)
        
    text = data.get('feedback', '').strip()
    if not text:
        return JsonResponse({'success': False, 'error': 'Feedback is empty.'}, status=400)
        
    UserFeedback.objects.create(user=request.user, feedback_text=text)
    return JsonResponse({'success': True})


@login_required
def api_get_profile(request):
    profile = request.user.profile
    return JsonResponse({
        'success':        True,
        'full_name':      request.user.full_name,
        'email':          request.user.email,
        'age':            profile.age,
        'education':      profile.education,
        'skills':         profile.skills,
        'health_concern': profile.health_concern,
        'location':       profile.location,
    })


@require_POST
@login_required
def api_update_profile(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid data.'}, status=400)

    profile                = request.user.profile
    profile.age            = data.get('age',            profile.age)
    profile.education      = data.get('education',      profile.education)
    profile.skills         = data.get('skills',         profile.skills)
    profile.health_concern = data.get('health_concern', profile.health_concern)
    profile.location       = data.get('location',       profile.location)
    profile.save()
    return JsonResponse({'success': True})


# ── Jobs API ──────────────────────────────────────────────────────────
@login_required
def api_get_jobs(request):
    jobs = JobRecommendation.objects.filter(user=request.user).order_by('-created_at')[:9]
    data = []
    for j in jobs:
        data.append({
            'id': j.id,
            'title': j.title,
            'description': j.description,
            'match_score': j.match_score,
            'created_at': j.created_at.strftime("%b %d, %Y")
        })
    return JsonResponse({'success': True, 'jobs': data})


@require_POST
@login_required
def api_generate_jobs(request):
    profile = request.user.profile
    system_prompt = "You are an expert AI Career Counselor. Output ONLY valid raw JSON array out, with no markdown code blocks around it. The user will provide their profile, and you must return exactly 3 highly personalized, specific job opportunities."
    
    prompt = f"""
    Analyze this user profile and output 3 distinct job roles that fit perfectly.
    OUTPUT EXACTLY A LIST OF 3 JSON OBJECTS IN THIS FORMAT, NO EXTRA TEXT:
    [
      {{"title": "Job Title", "description": "1 sentence describing the role, 1 sentence on estimated salary, 1 sentence on why it fits the user.", "match_score": 95.5}}
    ]

    USER PROFILE:
    Age: {profile.age}
    Location: {profile.location}
    Education: {profile.education}
    Skills: {profile.skills}
    Health Constraints: {profile.health_concern}
    """
    
    groc_api_key = getattr(settings, 'GROQ_API_KEY', '') or getattr(settings, 'GROC_API_KEY', '')
    if not groc_api_key:
         return JsonResponse({'success': False, 'error': 'API key not configured.'}, status=500)
         
    reply = _get_groc_reply(prompt, system_prompt, groc_api_key)
    if not reply:
         return JsonResponse({'success': False, 'error': 'Failed to reach AI service.'}, status=500)
         
    try:
         reply_clean = reply.strip()
         if reply_clean.startswith('```json'): reply_clean = reply_clean[7:]
         elif reply_clean.startswith('```'): reply_clean = reply_clean[3:]
         if reply_clean.endswith('```'): reply_clean = reply_clean[:-3]
         reply_clean = reply_clean.strip()
         
         jobs_data = json.loads(reply_clean)
         saved_jobs = []
         
         # Optionally limit total saved jobs per user so DB doesn't explode
         JobRecommendation.objects.filter(user=request.user).order_by('-created_at')[15:].delete()

         for j in jobs_data:
              new_job = JobRecommendation.objects.create(
                  user=request.user,
                  title=j.get('title', 'Unknown Role'),
                  description=j.get('description', ''),
                  match_score=float(j.get('match_score', 80.0))
              )
              saved_jobs.append({
                  'id': new_job.id,
                  'title': new_job.title,
                  'description': new_job.description,
                  'match_score': new_job.match_score,
                  'created_at': new_job.created_at.strftime("%b %d, %Y")
              })
         return JsonResponse({'success': True, 'jobs': saved_jobs})
    except Exception as e:
         return JsonResponse({'success': False, 'error': f'Failed to parse AI output. AI output was: {reply[:100]}... Error: {str(e)}'}, status=500)


# ── Jobs API ──────────────────────────────────────────────────────────
@login_required
def jobs_page(request):
    return render(request, 'jobs.html')


@login_required
def api_get_jobs(request):
    jobs = JobRecommendation.objects.filter(user=request.user).order_by('-created_at')[:9]
    data = []
    for j in jobs:
        data.append({
            'id': j.id,
            'title': j.title,
            'description': j.description,
            'match_score': j.match_score,
            'created_at': j.created_at.strftime("%b %d, %Y")
        })
    return JsonResponse({'success': True, 'jobs': data})


@require_POST
@login_required
def api_generate_jobs(request):
    profile = request.user.profile
    system_prompt = "You are an expert AI Career Counselor. Output ONLY valid raw JSON array out, with no markdown code blocks around it. The user will provide their profile, and you must return exactly 3 highly personalized, specific job opportunities."
    
    prompt = f"""
    Analyze this user profile and output 3 distinct job roles that fit perfectly.
    OUTPUT EXACTLY A LIST OF 3 JSON OBJECTS IN THIS FORMAT, NO EXTRA TEXT:
    [
      {{"title": "Job Title", "description": "1 sentence describing the role, 1 sentence on estimated salary, 1 sentence on why it fits the user.", "match_score": 95.5}}
    ]

    USER PROFILE:
    Age: {profile.age}
    Location: {profile.location}
    Education: {profile.education}
    Skills: {profile.skills}
    Health Constraints: {profile.health_concern}
    """
    
    groc_api_key = getattr(settings, 'GROQ_API_KEY', '') or getattr(settings, 'GROC_API_KEY', '')
    if not groc_api_key:
         return JsonResponse({'success': False, 'error': 'API key not configured.'}, status=500)
         
    reply = _get_groc_reply(prompt, system_prompt, groc_api_key)
    if not reply:
         return JsonResponse({'success': False, 'error': 'Failed to reach AI service.'}, status=500)
         
    try:
         reply_clean = reply.strip()
         if reply_clean.startswith('```json'): reply_clean = reply_clean[7:]
         elif reply_clean.startswith('```'): reply_clean = reply_clean[3:]
         if reply_clean.endswith('```'): reply_clean = reply_clean[:-3]
         reply_clean = reply_clean.strip()
         
         jobs_data = json.loads(reply_clean)
         saved_jobs = []
         
         old_jobs = list(JobRecommendation.objects.filter(user=request.user).order_by('-created_at')[15:])
         if old_jobs:
              JobRecommendation.objects.filter(id__in=[j.id for j in old_jobs]).delete()

         for j in jobs_data:
              new_job = JobRecommendation.objects.create(
                  user=request.user,
                  title=j.get('title', 'Unknown Role'),
                  description=j.get('description', ''),
                  match_score=float(j.get('match_score', 80.0))
              )
              saved_jobs.append({
                  'id': new_job.id,
                  'title': new_job.title,
                  'description': new_job.description,
                  'match_score': new_job.match_score,
                  'created_at': new_job.created_at.strftime("%b %d, %Y")
              })
         return JsonResponse({'success': True, 'jobs': saved_jobs})
    except Exception as e:
         return JsonResponse({'success': False, 'error': f'Failed to parse AI output. Error: {str(e)}'}, status=500)


# ── Schemes API ───────────────────────────────────────────────────────
@login_required
def api_get_schemes(request):
    category = request.GET.get('category', None)
    saved_only = request.GET.get('saved_only', 'false') == 'true'
    
    schemes  = GovernmentScheme.objects.filter(is_active=True)
    if category:
        schemes = schemes.filter(category=category)
        
    saved_ids = set()
    if request.user.is_authenticated:
        saved_ids = set(SavedScheme.objects.filter(user=request.user).values_list('scheme_id', flat=True))
        
    if saved_only:
        schemes = schemes.filter(id__in=saved_ids)
        
    data = list(schemes.values('id', 'name', 'description', 'category', 'level', 'ministry', 'state_name', 'target_gender', 'target_caste', 'target_income', 'target_occupation', 'eligibility', 'application_process', 'link'))
    
    for item in data:
        item['is_saved'] = item['id'] in saved_ids
        
    return JsonResponse({'success': True, 'schemes': data})


@login_required
def api_discover_schemes(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse({'success': True, 'schemes': []})
        
    local_matches = GovernmentScheme.objects.filter(is_active=True).filter(
        Q(name__icontains=q) | Q(description__icontains=q) | Q(category__icontains=q)
    )
    
    if local_matches.count() < 4:
        groc_api_key = getattr(settings, 'GROQ_API_KEY', '') or getattr(settings, 'GROC_API_KEY', '')
        if groc_api_key:
            system_prompt = "You are a precise data extraction AI for the Indian Government."
            prompt = f"""Discover up to 5 actual, real-world Indian Government Schemes (Central OR State level) directly related to the search query: "{q}".
                        Return strict JSON format, NOTHING ELSE. Format exactly:
                        {{
                            "schemes": [
                                {{
                                    "name": "Exact Scheme Name",
                                    "description": "Short description (2 sentences max)",
                                    "category": "Choose exactly ONE: Social Welfare & Empowerment, Education & Learning, Agriculture, Health & Wellness, Business & Entrepreneurship, Banking, Skills & Employment, Other",
                                    "level": "Central" or "State",
                                    "ministry": "Ministry of X (if Central, else blank)",
                                    "state_name": "State Name (if State, else blank)",
                                    "target_gender": "All" or "Male" or "Female",
                                    "target_caste": "General" or "SC/ST" or "OBC" or "All",
                                    "target_income": "BPL" or "APL" or "Any",
                                    "target_occupation": "Student" or "Farmer" or "Entrepreneur" or "None",
                                    "eligibility": "Who is eligible?",
                                    "link": "https://official-link.gov.in"
                                }}
                            ]
                        }}"""
            try:
                reply = _get_groc_reply(prompt, system_prompt, groc_api_key)
                if reply:
                    start = reply.find('{')
                    end = reply.rfind('}') + 1
                    json_str = reply[start:end]
                    data = json.loads(json_str)
                    
                    for item in data.get('schemes', []):
                        if not GovernmentScheme.objects.filter(name__iexact=item.get('name')).exists():
                            GovernmentScheme.objects.create(
                                name=item.get('name')[:200],
                                description=item.get('description'),
                                category=item.get('category', 'Other')[:50],
                                level=item.get('level', 'Central')[:50],
                                ministry=item.get('ministry', '')[:200],
                                state_name=item.get('state_name', '')[:100],
                                target_gender=item.get('target_gender', 'All')[:50],
                                target_caste=item.get('target_caste', 'All')[:50],
                                target_income=item.get('target_income', 'Any')[:50],
                                target_occupation=item.get('target_occupation', 'None')[:50],
                                eligibility=item.get('eligibility'),
                                link=item.get('link', ''),
                                is_active=True
                            )
            except Exception as e:
                print("Error AI Discovery:", str(e))
                pass
                
    final_matches = GovernmentScheme.objects.filter(is_active=True).filter(
        Q(name__icontains=q) | Q(description__icontains=q) | Q(category__icontains=q)
    ).order_by('-id')[:20]
    
    data = list(final_matches.values('id', 'name', 'description', 'category', 'level', 'ministry', 'state_name', 'target_gender', 'target_caste', 'target_income', 'target_occupation', 'eligibility', 'application_process', 'link'))
    
    saved_ids = set()
    if request.user.is_authenticated:
        saved_ids = set(SavedScheme.objects.filter(user=request.user).values_list('scheme_id', flat=True))
        
    for item in data:
        item['is_saved'] = item['id'] in saved_ids
        
    return JsonResponse({'success': True, 'schemes': data})


@login_required
def api_scheme_process(request, scheme_id):
    try:
        scheme = GovernmentScheme.objects.get(id=scheme_id, is_active=True)
        scheme.visits += 1
        scheme.save()
    except GovernmentScheme.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Scheme not found.'}, status=404)
        
    groc_api_key = getattr(settings, 'GROQ_API_KEY', '') or getattr(settings, 'GROC_API_KEY', '')
    if not groc_api_key:
        fallback = scheme.application_process or "No API key available to generate detailed steps."
        return JsonResponse({'success': True, 'process': fallback, 'link': scheme.link})
        
    system_prompt = "You are an expert government scheme advisor for the SmartCity Hub in India. Your goal is to provide highly detailed, accurate, and real-world application processes."
    prompt = f"Please provide a comprehensive, real-world, step-by-step guide on EXACTLY how citizens can apply for this Indian government scheme: {scheme.name}.\nDescription: {scheme.description}\nEligibility: {scheme.eligibility}\nProvide around 8 to 10 highly detailed bullet points explaining the actual real-world application process (e.g. required documents, official portals, offline centers to visit, verification steps). Format it using HTML tags like <ul>, <li>, <strong> so we can render it beautifully. Do not use Markdown characters, just raw HTML."
    
    reply = _get_groc_reply(prompt, system_prompt, groc_api_key)
    if not reply:
        reply = scheme.application_process or "We could not generate the steps right now."
        
        
    return JsonResponse({'success': True, 'process': reply, 'link': scheme.link})


@require_POST
@login_required
def api_toggle_save_scheme(request, scheme_id):
    from django.shortcuts import get_object_or_404
    scheme = get_object_or_404(GovernmentScheme, id=scheme_id)
    saved, created = SavedScheme.objects.get_or_create(user=request.user, scheme=scheme)
    if not created:
        saved.delete()
        is_saved = False
    else:
        is_saved = True
    return JsonResponse({'success': True, 'is_saved': is_saved})


@login_required
def saved_schemes_page(request):
    return render(request, 'saved_schemes.html')


# ── Fake Scheme Verifier ──────────────────────────────────────────────
@login_required
def verify_scheme_page(request):
    return render(request, 'verify_scheme.html')

@require_POST
@login_required
def api_verify_fake_scheme(request):
    try:
        data = json.loads(request.body)
        scheme_name = data.get('name', '').strip()
        scheme_url = data.get('url', '').strip()
        
        if not scheme_name and not scheme_url:
            return JsonResponse({'success': False, 'error': 'Please provide a scheme name or URL to verify.'})
            
        system_prompt = 'You are an expert Indian Government Fraud Scheme Detector. Your job is to protect citizens from scams. Evaluate the given scheme name and URL. Real government URLs must strictly end in ".gov.in" or ".nic.in". If the URL does not end in these extensions, aggressively flag it as SUSPICIOUS or FAKE. If no URL is provided, judge by the name (e.g., does it sound like a known real scheme like Pradhan Mantri Awas Yojana, or is it a common scam like "Free Laptop Scheme 2026"). Output ONLY a raw JSON object with no markdown: {"verdict": "SAFE" | "SUSPICIOUS" | "FAKE", "reason": "3 sentence strict explanation"}'
        
        prompt = f"Scheme Name: {scheme_name}\nScheme URL: {scheme_url}\nEvaluate if this is real or fake."
        
        groc_api_key = getattr(settings, 'GROQ_API_KEY', '') or getattr(settings, 'GROC_API_KEY', '')
        if not groc_api_key:
             return JsonResponse({'success': False, 'error': 'API key not configured.'}, status=500)
             
        reply = _get_groc_reply(prompt, system_prompt, groc_api_key)
        if not reply:
             return JsonResponse({'success': False, 'error': 'Failed to reach AI service.'}, status=500)
             
        reply_clean = reply.strip()
        if reply_clean.startswith('```json'): reply_clean = reply_clean[7:]
        elif reply_clean.startswith('```'): reply_clean = reply_clean[3:]
        if reply_clean.endswith('```'): reply_clean = reply_clean[:-3]
        reply_clean = reply_clean.strip()
        
        verdict_data = json.loads(reply_clean)
        return JsonResponse({'success': True, 'verdict': verdict_data.get('verdict', 'SUSPICIOUS'), 'reason': verdict_data.get('reason', 'Verification failed to produce reasoning.')})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Failed to parse AI output. Error: {str(e)}'}, status=500)


# ── Fake Scheme Verifier ──────────────────────────────────────────────
@login_required
def verify_scheme_page(request):
    return render(request, 'verify_scheme.html')

@require_POST
@login_required
def api_verify_fake_scheme(request):
    try:
        data = json.loads(request.body)
        scheme_name = data.get('name', '').strip()
        scheme_url = data.get('url', '').strip()
        
        if not scheme_name and not scheme_url:
            return JsonResponse({'success': False, 'error': 'Please provide a scheme name or URL to verify.'})
            
        system_prompt = 'You are an expert Indian Government Fraud Scheme Detector. Your job is to protect citizens from scams. Evaluate the given scheme name and URL. Real government URLs must strictly end in ".gov.in" or ".nic.in". If the URL does not end in these extensions, aggressively flag it as SUSPICIOUS or FAKE. If no URL is provided, judge by the name (e.g., does it sound like a known real scheme like Pradhan Mantri Awas Yojana, or is it a common scam like "Free Laptop Scheme 2026"). Output ONLY a raw JSON object with no markdown: {"verdict": "SAFE" | "SUSPICIOUS" | "FAKE", "reason": "3 sentence strict explanation"}'
        
        prompt = f"Scheme Name: {scheme_name}\nScheme URL: {scheme_url}\nEvaluate if this is real or fake."
        
        groc_api_key = getattr(settings, 'GROQ_API_KEY', '') or getattr(settings, 'GROC_API_KEY', '')
        if not groc_api_key:
             return JsonResponse({'success': False, 'error': 'API key not configured.'}, status=500)
             
        reply = _get_groc_reply(prompt, system_prompt, groc_api_key)
        if not reply:
             return JsonResponse({'success': False, 'error': 'Failed to reach AI service.'}, status=500)
             
        reply_clean = reply.strip()
        if reply_clean.startswith('```json'): reply_clean = reply_clean[7:]
        elif reply_clean.startswith('```'): reply_clean = reply_clean[3:]
        if reply_clean.endswith('```'): reply_clean = reply_clean[:-3]
        reply_clean = reply_clean.strip()
        
        verdict_data = json.loads(reply_clean)
        return JsonResponse({'success': True, 'verdict': verdict_data.get('verdict', 'SUSPICIOUS'), 'reason': verdict_data.get('reason', 'Verification failed to produce reasoning.')})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Failed to parse AI output. Error: {str(e)}'}, status=500)


# ── Health Guidance API ───────────────────────────────────────────────
@login_required
def health_page(request):
    return render(request, 'health.html')

@require_POST
@login_required
def api_generate_health(request):
    profile = request.user.profile
    system_prompt = "You are an expert Medical Advisor and Indian Government Health Scheme Specialist. Output ONLY valid raw JSON array out, with no markdown code blocks. The user will provide their profile, and you must return exactly 3 highly personalized health recommendations: 1 Diet plan, 1 Exercise routine, and 1 Government Health Scheme they qualify for."
    
    prompt = f"""
    Analyze this user profile and output exactly 3 JSON objects.
    OUTPUT FORMAT:
    [
      {{"category": "Diet", "title": "Specific Diet Plan", "advice": "2 sentences describing what to eat and avoid."}},
      {{"category": "Exercise", "title": "Safe Exercise Routine", "advice": "2 sentences of safe daily exercises."}},
      {{"category": "Govt Scheme", "title": "Applicable Health Scheme", "advice": "1 practical Govt scheme like Ayushman Bharat they can use."}}
    ]

    USER PROFILE:
    Age: {profile.age}
    Location: {profile.location}
    Health Constraints / Medical Conditions: {profile.health_concern}
    """
    
    groc_api_key = getattr(settings, 'GROQ_API_KEY', '') or getattr(settings, 'GROC_API_KEY', '')
    if not groc_api_key:
         return JsonResponse({'success': False, 'error': 'API key not configured.'}, status=500)
         
    reply = _get_groc_reply(prompt, system_prompt, groc_api_key)
    if not reply:
         return JsonResponse({'success': False, 'error': 'Failed to reach AI service.'}, status=500)
         
    try:
         reply_clean = reply.strip()
         if reply_clean.startswith('```json'): reply_clean = reply_clean[7:]
         elif reply_clean.startswith('```'): reply_clean = reply_clean[3:]
         if reply_clean.endswith('```'): reply_clean = reply_clean[:-3]
         reply_clean = reply_clean.strip()
         
         health_data = json.loads(reply_clean)
         return JsonResponse({'success': True, 'recommendations': health_data})
    except Exception as e:
         return JsonResponse({'success': False, 'error': f'Failed to parse AI output. Error: {str(e)}'}, status=500)


# ── Chatbot API ───────────────────────────────────────────────────────
@require_POST
@login_required
def api_chat(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid data.'}, status=400)

    user_message = data.get('message', '').strip()
    language = data.get('language', 'english').strip().lower()

    if not user_message:
        return JsonResponse({'success': False, 'error': 'Message is empty.'}, status=400)

    ChatMessage.objects.create(user=request.user, sender='user', message=user_message)
    bot_reply = get_bot_reply(user_message, request.user, language)
    mode = 'limited' if 'SmartBot is in limited mode right now.' in bot_reply else 'live'

    ChatMessage.objects.create(user=request.user, sender='bot', message=bot_reply)
    return JsonResponse({'success': True, 'reply': bot_reply, 'mode': mode})


def get_bot_reply(message, user, language='english'):
    # Get user profile for personalized responses
    try:
        profile = user.profile
        user_context = f"""
        User Profile:
        - Name: {user.full_name}
        - Age: {profile.age or 'Not specified'}
        - Education: {profile.education or 'Not specified'}
        - Skills: {profile.skills or 'Not specified'}
        - Location: {profile.location or 'Not specified'}
        - Health Concerns: {profile.health_concern or 'None'}
        """
    except Exception:
        user_context = f"User: {user.full_name}"

    try:
        feedbacks = user.feedbacks.order_by('-created_at')[:5]
        feedback_context = ""
        if feedbacks.exists():
            fb_texts = "\n- ".join([f.feedback_text for f in feedbacks])
            feedback_context = f"\n\nCRITICAL USER FEEDBACK (LEARN FROM THIS):\n- {fb_texts}\nYou MUST adjust your recommendations and communication to conform strictly to this feedback."
    except Exception:
        feedback_context = ""

    system_prompt = f"""You are SmartBot, the official Voice AI Assistant for SmartCity Hub.

CRITICAL RULE: You MUST ONLY answer questions related to:
1. Government Schemes, Grants, and Policies
2. Civic Issues, Health Care, and Education
3. Job Recommendations & Career Advice
4. The Smart Community Platform Features

If the user asks ANY question outside of these topics (e.g., programming, jokes, movies, "silly" questions, or general AI trivia), you MUST refuse to answer and clearly state: "I am a dedicated Civic AI Assistant. I can only help you with Government Schemes, Jobs, Education, and Health topics."

Your job is to give short, helpful, personalized answers based on the user's profile.
Always respond in exactly {language.capitalize()}.
Keep responses under 80 words and use simple language, as your answers will be spoken aloud to the user by a voice engine.
If recommending schemes, mention specific Indian government schemes by name.

{user_context}{feedback_context}"""

    groc_api_key = getattr(settings, 'GROQ_API_KEY', '') or getattr(settings, 'GROC_API_KEY', '')
    if not groc_api_key:
        return _fallback_bot_reply(message, user, reason='missing_key')

    groc_reply = _get_groc_reply(message, system_prompt, groc_api_key)
    if groc_reply:
        return groc_reply

    return _fallback_bot_reply(message, user, reason='groc_unavailable')


def _get_groc_reply(message, system_prompt, api_key):
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        "temperature": 0.4,
        "max_tokens": 300,
    }

    request = urllib.request.Request(
        url="https://api.groq.com/openai/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            body = json.loads(response.read().decode("utf-8"))
            content = body.get("choices", [{}])[0].get("message", {}).get("content", "")
            return content.strip()
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError, KeyError, IndexError):
        return ''


def _fallback_bot_reply(message, user, reason=''):
    intent = _detect_intent(message)
    category_map = {
        'health': 'health',
        'education': 'education',
        'job': 'employment',
        'scheme': 'welfare',
    }

    first_name = (user.full_name or 'there').split(' ')[0]
    schemes_qs = GovernmentScheme.objects.filter(is_active=True)

    if intent in category_map:
        schemes_qs = schemes_qs.filter(category=category_map[intent])

    words = [w for w in message.lower().split() if len(w) >= 4]
    if words:
        query = Q()
        for word in words[:6]:
            query |= Q(name__icontains=word) | Q(description__icontains=word) | Q(eligibility__icontains=word)
        keyword_matches = schemes_qs.filter(query)
        if keyword_matches.exists():
            schemes_qs = keyword_matches

    schemes = list(schemes_qs.values('name', 'link')[:3])
    reason_note = {
        'missing_key': 'Groq API key is not configured in the server environment. ',
        'groc_unavailable': 'Groq service did not return a response (key invalid, quota, or network issue). ',
    }.get(reason, '')

    if schemes:
        scheme_text = '; '.join(f"{s['name']}: {s['link']}" for s in schemes)
        intent_hint = {
            'job': 'I picked employment-focused options for you. ',
            'health': 'I picked health-focused options for you. ',
            'education': 'I picked education-focused options for you. ',
            'scheme': 'I picked general welfare options for you. ',
        }.get(intent, '')
        return (
            f"Hi {first_name}, SmartBot is in limited mode right now. "
            f"{reason_note}"
            f"{intent_hint}"
            f"Here are useful schemes you can check: {scheme_text}. "
            "Tell me your goal (job, health, or education) and I will guide you step-by-step."
        )
    return (
        f"Hi {first_name}, SmartBot is in limited mode right now. "
        f"{reason_note}"
        "Please tell me whether you need help with jobs, health, education, or schemes, and I will suggest the next steps."
    )


def _detect_intent(message):
    text = message.lower()
    if any(token in text for token in ['job', 'work', 'employment', 'career', 'interview']):
        return 'job'
    if any(token in text for token in ['health', 'hospital', 'treatment', 'medicine', 'insurance']):
        return 'health'
    if any(token in text for token in ['education', 'college', 'school', 'scholarship', 'study']):
        return 'education'
    if any(token in text for token in ['scheme', 'yojana', 'benefit', 'subsidy', 'government']):
        return 'scheme'
    return 'general'

@login_required
def api_chat_history(request):
    messages = ChatMessage.objects.filter(user=request.user).values(
        'sender', 'message', 'created_at'
    )
    history = list(messages)
    for item in history:
        item['mode'] = 'limited' if 'SmartBot is in limited mode right now.' in item['message'] else 'live'
    return JsonResponse({'success': True, 'messages': history})


@require_POST
@login_required
def api_chat_clear(request):
    ChatMessage.objects.filter(user=request.user).delete()
    return JsonResponse({'success': True})

@login_required
def profile(request):
    return render(request, 'profile.html', {'user': request.user})

@login_required
def schemes(request):
    return render(request, 'schemes.html', {'user': request.user})

@login_required
def chatbot(request):
    return render(request, 'chatbot.html', {'user': request.user})


# ── Admin APIs ────────────────────────────────────────────────────────
@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('dashboard')
    return render(request, 'admin_dashboard.html', {'user': request.user})


@login_required
def api_admin_stats(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    total_users = SmartUser.objects.count()
    total_schemes = GovernmentScheme.objects.count()
    total_chats = ChatMessage.objects.count()
    
    top_scheme_obj = GovernmentScheme.objects.order_by('-visits').first()
    top_scheme = {
        'name': top_scheme_obj.name if top_scheme_obj else 'No data',
        'visits': top_scheme_obj.visits if top_scheme_obj else 0
    }
    
    # Get active users
    users = list(SmartUser.objects.values('id', 'full_name', 'email', 'date_joined', 'is_active').order_by('-date_joined'))
    
    # Get schemes
    schemes_data = list(GovernmentScheme.objects.values('id', 'name', 'category', 'level', 'visits').order_by('-id'))
    
    return JsonResponse({
        'success': True,
        'stats': {
            'total_users': total_users,
            'total_schemes': total_schemes,
            'total_chats': total_chats,
            'top_scheme': top_scheme
        },
        'users': users,
        'schemes': schemes_data
    })


@require_POST
@login_required
def api_add_scheme(request):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid data.'}, status=400)
        
    name = data.get('name', '').strip()
    description = data.get('description', '').strip()
    category = data.get('category', '').strip()
    eligibility = data.get('eligibility', '').strip()
    application_process = data.get('application_process', '').strip()
    link = data.get('link', '').strip()
    
    if not name or not description or not category or not eligibility:
        return JsonResponse({'success': False, 'error': 'Missing required fields.'}, status=400)
        
    scheme = GovernmentScheme.objects.create(
        name=name,
        description=description,
        category=category,
        eligibility=eligibility,
        application_process=application_process,
        link=link
    )
    
    return JsonResponse({'success': True, 'scheme_id': scheme.id})


@require_POST
@login_required
def api_delete_scheme(request, scheme_id):
    if not request.user.is_staff:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)
        
    try:
        scheme = GovernmentScheme.objects.get(id=scheme_id)
        scheme.delete()
        return JsonResponse({'success': True})
    except GovernmentScheme.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Scheme not found'}, status=404)

# ── Password Recovery API ──────────────────────────────────────────────────
from django.urls import reverse

@require_http_methods(["POST"])
def api_forgot_password(request):
    try:
        data = json.loads(request.body)
        email = data.get('email', '').strip()
        user = SmartUser.objects.filter(email=email).first()
        
        if not user:
            # For security, we still return true so we don't leak registered emails
            return JsonResponse({'success': True, 'message': 'If this email exists, a password reset link has been sent.'})
            
        # Invalidate old Tokens
        PasswordResetToken.objects.filter(user=user).delete()
        
        # Create new Token
        token_obj = PasswordResetToken.objects.create(user=user)
        
        # Build the exact fully qualified link
        reset_link = request.build_absolute_uri(f'/reset-password/{token_obj.token}/')
        
        # Send Email
        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <p>Hello {user.full_name},</p>
            <p>We received a request to reset your password. Please click the button below to choose a new password:</p>
            <a href="{reset_link}" style="display:inline-block; padding: 12px 24px; background-color: #10b981; color: #fff; text-decoration: none; border-radius: 8px; font-weight: bold;">Reset Your Password</a>
            <p><br>If the button doesn't work, copy and paste this link into your browser:<br>{reset_link}</p>
            <p>This link will expire in 1 hour.</p>
            <p>Thanks,<br>JANSEVA AI Team</p>
        </body>
        </html>
        """
        
        send_mail(
            subject='JANSEVA AI - Reset Your Password',
            message=f'Hello {user.full_name},\n\nPlease use this link to reset your password:\n{reset_link}',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        return JsonResponse({'success': True, 'message': 'Recovery link sent via email!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def reset_password_page(request, token):
    # This is not an API, this renders the HTML page
    try:
        token_obj = PasswordResetToken.objects.get(token=token)
        if not token_obj.is_valid():
            return render(request, 'reset_password.html', {'error': 'This password reset link is invalid or has expired.'})
        return render(request, 'reset_password.html', {'token': token_obj.token, 'email': token_obj.user.email})
    except (PasswordResetToken.DoesNotExist, ValueError):
        return render(request, 'reset_password.html', {'error': 'This password reset link is invalid or has expired.'})


@require_http_methods(["POST"])
def api_reset_password(request):
    try:
        data = json.loads(request.body)
        token = data.get('token', '').strip()
        new_password = data.get('new_password', '')
        
        if len(new_password) < 8:
            return JsonResponse({'success': False, 'error': 'Password must be at least 8 characters long.'})
            
        token_obj = PasswordResetToken.objects.filter(token=token).last()
        if not token_obj or not token_obj.is_valid():
            return JsonResponse({'success': False, 'error': 'Invalid or expired password reset link. Please request a new one.'})
            
        user = token_obj.user
        user.set_password(new_password)
        user.save()
        
        # Delete token so it can't be reused
        token_obj.delete()
        
        return JsonResponse({'success': True, 'message': 'Password has been reset successfully!'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})