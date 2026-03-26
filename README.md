# 🏙️ Smart Community Hub

An AI-powered, meticulously designed web platform built to empower citizens by providing highly personalized access to Government Schemes, Job Opportunities, and Health Guidance. Built with a stunning **Obsidian Black & Emerald Green** aesthetic, the platform leverages the Groq LLaMA engine to offer real-time, context-aware artificial intelligence.

## ✨ Core Features
- **🛡️ Secure Civic Access:** A robust Custom User Authentication system featuring link-based password recovery.
- **🏛️ The Scheme Vault:** A massive, searchable catalog of National and State-level government policies. Easily hit `🔖 Save` to effortlessly bookmark specific schemes to your personalized vault.
- **💬 SmartAssist Chatbot (Multilingual):** Engage with our built-in civic AI that natively understands English, Hindi, Marathi, and Kannada. Let the AI safely guide you through education and agricultural grants.
- **💼 AI Job Recommender:** Fusing your uploaded resumes or profile skills (Education, Location, Age), the platform instantly queries a LLaMA model to map out perfect career tracks. 
- **🩺 Clinical Health Engine:** The Hub actively detects your physical constraints and allergies, generating personalized safe-diets, bounded exercises, and government insurance programs you qualify for.
- **🚨 Fake Scheme Detector:** Fraud-prevention dashboard actively neutralizing phishing domains. Paste any URL or scheme name, and the AI will violently flag it as `Crimson DANGER` or verify it as `Emerald SAFE`.
- **📊 Admin God-Mode:** Powerful, sleek admin panel to monitor active logins, scheme query traffic, and effortlessly push new Government Programs directly into the SQLite Engine.

## 🛠️ Technology Stack
- **Backend:** Python + Django (SQLite)
- **Frontend Engine:** Native HTML5, CSS3, ES6 JavaScript
- **AI Brain:** `llama-3.3-70b-versatile` via Groq API
- **Design System:** Custom Physics-based CSS Animations, Frosted Glass UI (Backdrop-filter)

## 🚀 Local Deployment

### 1. Requirements
- Python 3.9+
- A valid [Groq API Key](https://console.groq.com)

### 2. Installation
Clone this repository and build the virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt
```

### 3. Environment Variables
Create a `.env` file natively in the root directory alongside `manage.py`:
```env
# Smart Community Configuration
SECRET_KEY='your-django-secure-key'
DEBUG=True

# AI Engine
GROQ_API_KEY='gsk_your_groq_api_token_here'

# Recovery
EMAIL_HOST_USER='your-app-email@gmail.com'
EMAIL_HOST_PASSWORD='your-app-password'
```

### 4. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser  # Optional: For Django Admin access
```

### 5. Launch the Hub
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/` safely from any modern browser. 

---
*Built intricately with AI, focusing deeply on hyper-personalization, striking visuals, and government-grade safety protocols.*
# JAnSEVA-AI
