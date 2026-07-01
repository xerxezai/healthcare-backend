"""
🧬 DNA Sequencing URLs
====================

Main URL routing for DNA sequencing application
"""

from django.urls import path, include
from . import views
from .ai_report_generator import generate_ai_genomic_report, get_ai_report_templates

app_name = 'dna_sequencing'

urlpatterns = [
    # Main DNA Sequencing endpoints
    path('api/dashboard/', views.get_dna_sequencing_dashboard, name='dashboard'),
    path('api/analysis/', views.get_genome_analysis, name='analysis'),
    path('api/start-analysis/', views.start_dna_analysis, name='start_analysis'),
    
    # Export endpoints (soft-coded)
    path('api/export/pdf/', views.export_pdf_report, name='export_pdf'),
    path('api/export/excel/', views.export_excel_report, name='export_excel'),
    path('api/export/csv/', views.export_csv_report, name='export_csv'),
    path('api/export/vcf/', views.export_vcf_report, name='export_vcf'),
    path('api/export/json/', views.export_json_report, name='export_json'),
    
    # AI-Powered Report Generation
    path('api/reports/ai-generate/', generate_ai_genomic_report, name='ai_generate_report'),
    path('api/reports/templates/', get_ai_report_templates, name='ai_report_templates'),
    
    # AI Genomics Laboratory endpoints
    path('', include('dna_sequencing.ai_genomics_urls')),
]
