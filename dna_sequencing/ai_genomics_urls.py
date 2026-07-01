"""
🧬 AI Genomics Laboratory URLs
============================

URL routing for advanced AI-powered genomic analysis endpoints
"""

from django.urls import path
from . import ai_genomics_views

app_name = 'ai_genomics'

urlpatterns = [
    # Main AI Genomics API
    path('api/ai-genomics/', 
         ai_genomics_views.AIGenomicsAPI.as_view(), 
         name='ai_genomics'),
    
    # Model Comparison
    path('api/ai-genomics/comparison/', 
         ai_genomics_views.get_ai_model_comparison, 
         name='ai_model_comparison'),
    
    # Batch Analysis
    path('api/ai-genomics/batch/', 
         ai_genomics_views.batch_ai_analysis, 
         name='batch_ai_analysis'),
    
    # Dashboard Data
    path('api/ai-genomics/dashboard/', 
         ai_genomics_views.get_ai_genomics_dashboard, 
         name='ai_genomics_dashboard'),
]
