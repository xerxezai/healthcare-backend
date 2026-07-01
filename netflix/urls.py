# Netflix app URL configuration
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'netflix'

# API URL patterns
urlpatterns = [
    # Content Management
    path('genres/', views.GenreListCreateView.as_view(), name='genre-list'),
    path('titles/', views.TitleListCreateView.as_view(), name='title-list'),
    path('titles/<int:pk>/', views.TitleDetailView.as_view(), name='title-detail'),
    path('titles/<int:title_id>/seasons/', views.SeasonListCreateView.as_view(), name='season-list'),
    path('seasons/<int:season_id>/episodes/', views.EpisodeListCreateView.as_view(), name='episode-list'),
    path('assets/', views.AssetListCreateView.as_view(), name='asset-list'),
    
    # User Profile Management
    path('profiles/', views.UserProfileListCreateView.as_view(), name='profile-list'),
    path('entitlements/', views.UserEntitlementsView.as_view(), name='user-entitlements'),
    path('entitlements/<int:user_id>/', views.UserEntitlementsView.as_view(), name='user-entitlements-detail'),
    path('devices/', views.DeviceListCreateView.as_view(), name='device-list'),
    
    # User Activity
    path('profiles/<int:profile_id>/watchlist/', views.WatchlistView.as_view(), name='watchlist'),
    path('profiles/<int:profile_id>/history/', views.PlaybackHistoryView.as_view(), name='playback-history'),
    path('profiles/<int:profile_id>/ratings/', views.RatingListCreateView.as_view(), name='rating-list'),
    path('playback/progress/', views.update_playback_progress, name='update-progress'),
    
    # Finance Management
    path('payments/', views.ManualPaymentListCreateView.as_view(), name='payment-list'),
    path('invoices/', views.InvoiceListCreateView.as_view(), name='invoice-list'),
    
    # Audit and Reporting
    path('audit-logs/', views.ContentAuditLogView.as_view(), name='audit-logs'),
    path('dashboard/stats/', views.dashboard_stats, name='dashboard-stats'),
    
    # Role Management
    path('roles/', views.EnhancedRoleListCreateView.as_view(), name='role-list'),
    path('role-assignments/', views.UserRoleAssignmentView.as_view(), name='role-assignment-list'),
    path('users/<int:user_id>/roles/', views.UserRoleAssignmentView.as_view(), name='user-role-assignments'),
    
    # Utility Endpoints
    path('bulk-operations/titles/', views.bulk_title_operations, name='bulk-title-operations'),
    path('recommendations/', views.content_recommendations, name='content-recommendations'),
]
