"""
🎤 Voice Recognition API URLs
===========================

URL routing for AI-powered voice recognition and reporting system
"""

from django.urls import path
from . import voice_recognition_views

app_name = 'voice_recognition'

urlpatterns = [
    # Voice Recognition Processing
    path('api/voice/process/', 
         voice_recognition_views.VoiceRecognitionAPI.as_view(), 
         name='voice_process'),
    
    # Report Templates
    path('api/voice/templates/', 
         voice_recognition_views.ReportTemplateAPI.as_view(), 
         name='voice_templates'),
    
    # Save Voice Reports
    path('api/voice/save/', 
         voice_recognition_views.save_voice_report, 
         name='save_voice_report'),
    
    # Voice Commands
    path('api/voice/commands/', 
         voice_recognition_views.get_voice_commands, 
         name='voice_commands'),
]
