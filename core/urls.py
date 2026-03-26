from django.urls import path
from . import views

urlpatterns = [
    # Pages
    path('',           views.index,     name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Auth
    path('api/auth/signup/', views.api_signup, name='api_signup'),
    path('api/auth/login/',  views.api_login,  name='api_login'),
    path('api/auth/logout/', views.api_logout, name='api_logout'),
    path('api/auth/forgot-password/', views.api_forgot_password, name='api_forgot_password'),
    path('reset-password/<uuid:token>/', views.reset_password_page, name='reset_password_page'),
    path('api/auth/reset-password/', views.api_reset_password, name='api_reset_password'),

    # Profile
    path('api/profile/',        views.api_get_profile,    name='api_get_profile'),
    path('api/profile/update/', views.api_update_profile, name='api_update_profile'),
    path('api/feedback/submit/',views.api_submit_feedback,name='api_submit_feedback'),

    # Jobs
    path('jobs/', views.jobs_page, name='jobs_page'),
    path('api/jobs/', views.api_get_jobs, name='api_get_jobs'),
    path('api/jobs/generate/', views.api_generate_jobs, name='api_generate_jobs'),

    # Schemes
    path('api/schemes/', views.api_get_schemes, name='api_get_schemes'),
    path('api/schemes/discover/', views.api_discover_schemes, name='api_discover_schemes'),
    path('api/scheme/<int:scheme_id>/process/', views.api_scheme_process, name='api_scheme_process'),
    path('api/scheme/<int:scheme_id>/toggle-save/', views.api_toggle_save_scheme, name='api_toggle_save_scheme'),
    path('saved-schemes/', views.saved_schemes_page, name='saved_schemes_page'),

    # Tools
    path('verify-scheme/', views.verify_scheme_page, name='verify_scheme_page'),
    path('api/schemes/verify/', views.api_verify_fake_scheme, name='api_verify_fake_scheme'),
    path('health/', views.health_page, name='health_page'),
    path('api/health/generate/', views.api_generate_health, name='api_generate_health'),

    # Chatbot
    path('api/chat/',         views.api_chat,         name='api_chat'),
    path('api/chat/history/', views.api_chat_history, name='api_chat_history'),
    path('api/chat/clear/',   views.api_chat_clear,   name='api_chat_clear'),
    
    path('profile/', views.profile, name='profile'),
    path('schemes/', views.schemes, name='schemes'),
    path('chatbot/', views.chatbot, name='chatbot'),
    
    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('api/admin/stats/', views.api_admin_stats, name='api_admin_stats'),
    path('api/admin/schemes/add/', views.api_add_scheme, name='api_add_scheme'),
    path('api/admin/schemes/<int:scheme_id>/delete/', views.api_delete_scheme, name='api_delete_scheme'),
]