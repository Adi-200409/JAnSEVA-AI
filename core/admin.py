from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import SmartUser, UserProfile, GovernmentScheme, ChatMessage, JobRecommendation


@admin.register(SmartUser)
class SmartUserAdmin(UserAdmin):
    model         = SmartUser
    list_display  = ['email', 'full_name', 'is_active', 'is_staff', 'date_joined']
    ordering      = ['email']
    search_fields = ['email', 'full_name']

    fieldsets = (
        (None,          {'fields': ('email', 'password')}),
        ('Personal',    {'fields': ('full_name',)}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'full_name', 'password1', 'password2'),
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ['user', 'age', 'education', 'location', 'updated_at']
    search_fields = ['user__email', 'user__full_name', 'location']


@admin.register(GovernmentScheme)
class GovernmentSchemeAdmin(admin.ModelAdmin):
    list_display  = ['name', 'category', 'is_active', 'created_at']
    list_filter   = ['category', 'is_active']
    search_fields = ['name', 'description']


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display  = ['user', 'sender', 'message', 'created_at']
    list_filter   = ['sender']
    search_fields = ['user__email', 'message']


@admin.register(JobRecommendation)
class JobRecommendationAdmin(admin.ModelAdmin):
    list_display  = ['user', 'title', 'match_score', 'created_at']
    search_fields = ['user__email', 'title']