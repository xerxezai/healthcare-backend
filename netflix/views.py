# Netflix app API views
from rest_framework import generics, status, permissions, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from django.db.models import Q, Avg, Count, Sum
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from .models import (
    Genre, Title, Season, Episode, Asset, UserProfile, UserEntitlements,
    Device, Watchlist, PlaybackHistory, Rating, ManualPayment, Invoice,
    ContentAuditLog, EnhancedRole, UserRoleAssignment
)
from .serializers import (
    GenreSerializer, TitleListSerializer, TitleDetailSerializer,
    TitleCreateUpdateSerializer, SeasonSerializer, EpisodeSerializer,
    AssetSerializer, UserProfileSerializer, UserEntitlementsSerializer,
    DeviceSerializer, WatchlistSerializer, PlaybackHistorySerializer,
    PlaybackProgressSerializer, RatingSerializer, ManualPaymentSerializer,
    InvoiceSerializer, ContentAuditLogSerializer, EnhancedRoleSerializer,
    UserRoleAssignmentSerializer, UserSerializer, BulkTitleUpdateSerializer
)
from .permissions import NetflixPermissionMixin

User = get_user_model()


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'page_size'
    max_page_size = 100


# Content Management Views
class GenreListCreateView(NetflixPermissionMixin, generics.ListCreateAPIView):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_scope = ('content', 'read')
    required_scope_write = ('content', 'write')


class TitleListCreateView(NetflixPermissionMixin, generics.ListCreateAPIView):
    serializer_class = TitleListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['type', 'rating', 'visibility', 'release_year']
    search_fields = ['name', 'synopsis']
    ordering_fields = ['name', 'release_year', 'created_at']
    ordering = ['-created_at']
    required_scope = ('content', 'read')
    required_scope_write = ('content', 'write')
    
    def get_queryset(self):
        queryset = Title.objects.select_related('created_by').prefetch_related('genres', 'assets')
        
        # Filter by genre
        genre_id = self.request.query_params.get('genre')
        if genre_id:
            queryset = queryset.filter(genres__id=genre_id)
        
        # Filter by region access
        region = self.request.query_params.get('region')
        if region:
            queryset = queryset.filter(regions__contains=[region])
        
        # Filter by tags
        tag = self.request.query_params.get('tag')
        if tag:
            queryset = queryset.filter(tags__contains=[tag])
        
        return queryset
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return TitleCreateUpdateSerializer
        return TitleListSerializer
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class TitleDetailView(NetflixPermissionMixin, generics.RetrieveUpdateDestroyAPIView):
    queryset = Title.objects.select_related('created_by', 'updated_by').prefetch_related(
        'genres', 'seasons__episodes', 'assets', 'ratings'
    )
    permission_classes = [permissions.IsAuthenticated]
    required_scope = ('content', 'read')
    required_scope_write = ('content', 'write')
    required_scope_delete = ('content', 'delete')
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TitleCreateUpdateSerializer
        return TitleDetailSerializer
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)


class SeasonListCreateView(NetflixPermissionMixin, generics.ListCreateAPIView):
    serializer_class = SeasonSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_scope = ('content', 'read')
    required_scope_write = ('content', 'write')
    
    def get_queryset(self):
        title_id = self.kwargs.get('title_id')
        return Season.objects.filter(title_id=title_id).prefetch_related('episodes')
    
    def perform_create(self, serializer):
        title_id = self.kwargs.get('title_id')
        title = get_object_or_404(Title, id=title_id)
        serializer.save(title=title)


class EpisodeListCreateView(NetflixPermissionMixin, generics.ListCreateAPIView):
    serializer_class = EpisodeSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_scope = ('content', 'read')
    required_scope_write = ('content', 'write')
    
    def get_queryset(self):
        season_id = self.kwargs.get('season_id')
        return Episode.objects.filter(season_id=season_id).prefetch_related('assets')
    
    def perform_create(self, serializer):
        season_id = self.kwargs.get('season_id')
        season = get_object_or_404(Season, id=season_id)
        serializer.save(season=season)


class AssetListCreateView(NetflixPermissionMixin, generics.ListCreateAPIView):
    serializer_class = AssetSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['kind', 'quality', 'language']
    required_scope = ('assets', 'read')
    required_scope_write = ('assets', 'write')
    
    def get_queryset(self):
        title_id = self.request.query_params.get('title_id')
        episode_id = self.request.query_params.get('episode_id')
        
        queryset = Asset.objects.all()
        if title_id:
            queryset = queryset.filter(title_id=title_id)
        if episode_id:
            queryset = queryset.filter(episode_id=episode_id)
        
        return queryset


# User Profile Management
class UserProfileListCreateView(NetflixPermissionMixin, generics.ListCreateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_scope = ('profiles', 'read')
    required_scope_write = ('profiles', 'write')
    
    def get_queryset(self):
        if self.request.user.is_staff:
            # Staff can see all profiles
            return UserProfile.objects.select_related('user')
        else:
            # Regular users see only their own profiles
            return UserProfile.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # Check profile limit
        entitlements = getattr(user, 'netflix_entitlements', None)
        if entitlements:
            current_profiles = user.viewing_profiles.count()
            if current_profiles >= entitlements.max_profiles:
                raise ValidationError(f"Maximum {entitlements.max_profiles} profiles allowed")
        
        serializer.save(user=user)


class UserEntitlementsView(NetflixPermissionMixin, generics.RetrieveUpdateAPIView):
    serializer_class = UserEntitlementsSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_scope = ('entitlements', 'read')
    required_scope_write = ('entitlements', 'write')
    
    def get_object(self):
        user_id = self.kwargs.get('user_id')
        if user_id:
            user = get_object_or_404(User, id=user_id)
        else:
            user = self.request.user
        
        entitlements, created = UserEntitlements.objects.get_or_create(user=user)
        return entitlements
    
    def perform_update(self, serializer):
        serializer.save(
            last_modified_by=self.request.user,
            modification_reason=self.request.data.get('modification_reason', '')
        )


class DeviceListCreateView(NetflixPermissionMixin, generics.ListCreateAPIView):
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_scope = ('devices', 'read')
    required_scope_write = ('devices', 'write')
    
    def get_queryset(self):
        if self.request.user.is_staff:
            return Device.objects.select_related('user')
        else:
            return Device.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        user = self.request.user
        
        # Check device limit
        entitlements = getattr(user, 'netflix_entitlements', None)
        if entitlements:
            current_devices = user.streaming_devices.filter(is_blocked=False).count()
            if current_devices >= entitlements.max_devices:
                # Check for admin override
                if not (self.request.user.is_staff and self.request.data.get('admin_override')):
                    raise ValidationError(f"Maximum {entitlements.max_devices} devices allowed")
        
        serializer.save(user=user)


# User Activity Views
class WatchlistView(NetflixPermissionMixin, generics.ListCreateAPIView):
    serializer_class = WatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_scope = ('watchlist', 'read')
    required_scope_write = ('watchlist', 'write')
    
    def get_queryset(self):
        profile_id = self.kwargs.get('profile_id')
        profile = get_object_or_404(UserProfile, id=profile_id, user=self.request.user)
        return Watchlist.objects.filter(profile=profile).select_related('title')
    
    def perform_create(self, serializer):
        profile_id = self.kwargs.get('profile_id')
        profile = get_object_or_404(UserProfile, id=profile_id, user=self.request.user)
        serializer.save(profile=profile)


class PlaybackHistoryView(NetflixPermissionMixin, generics.ListAPIView):
    serializer_class = PlaybackHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    required_scope = ('history', 'read')
    
    def get_queryset(self):
        profile_id = self.kwargs.get('profile_id')
        profile = get_object_or_404(UserProfile, id=profile_id, user=self.request.user)
        return PlaybackHistory.objects.filter(profile=profile).select_related(
            'title', 'episode__season', 'device'
        ).order_by('-updated_at')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_playback_progress(request):
    """Update playback progress for a title/episode"""
    serializer = PlaybackProgressSerializer(data=request.data)
    if serializer.is_valid():
        # Get or create playback history record
        data = serializer.validated_data
        profile = data['profile']
        
        # Verify profile belongs to user
        if profile.user != request.user:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
        
        history, created = PlaybackHistory.objects.get_or_create(
            profile=profile,
            title=data['title'],
            episode=data.get('episode'),
            defaults=data
        )
        
        if not created:
            # Update existing record
            for field, value in data.items():
                setattr(history, field, value)
            history.save()
        
        return Response(PlaybackHistorySerializer(history).data)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RatingListCreateView(NetflixPermissionMixin, generics.ListCreateAPIView):
    serializer_class = RatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_scope = ('ratings', 'read')
    required_scope_write = ('ratings', 'write')
    
    def get_queryset(self):
        profile_id = self.kwargs.get('profile_id')
        if profile_id:
            profile = get_object_or_404(UserProfile, id=profile_id, user=self.request.user)
            return Rating.objects.filter(profile=profile).select_related('title')
        else:
            # Return all ratings for admin users
            if self.request.user.is_staff:
                return Rating.objects.select_related('profile__user', 'title')
            return Rating.objects.none()
    
    def perform_create(self, serializer):
        profile_id = self.kwargs.get('profile_id')
        profile = get_object_or_404(UserProfile, id=profile_id, user=self.request.user)
        serializer.save(profile=profile)


# Finance Management Views
class ManualPaymentListCreateView(NetflixPermissionMixin, generics.ListCreateAPIView):
    serializer_class = ManualPaymentSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['method', 'currency', 'verified']
    search_fields = ['user__email', 'reference_no']
    required_scope = ('finance', 'read')
    required_scope_write = ('finance', 'write')
    
    def get_queryset(self):
        return ManualPayment.objects.select_related('user', 'recorded_by').order_by('-date_received')
    
    def perform_create(self, serializer):
        serializer.save(recorded_by=self.request.user)


class InvoiceListCreateView(NetflixPermissionMixin, generics.ListCreateAPIView):
    serializer_class = InvoiceSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'currency']
    search_fields = ['invoice_number', 'user__email']
    required_scope = ('finance', 'read')
    required_scope_write = ('finance', 'write')
    
    def get_queryset(self):
        return Invoice.objects.select_related('user', 'created_by').prefetch_related('payments')
    
    def perform_create(self, serializer):
        # Generate invoice number
        from datetime import datetime
        year = datetime.now().year
        count = Invoice.objects.filter(invoice_number__startswith=f'INV-{year}').count() + 1
        invoice_number = f'INV-{year}-{count:04d}'
        
        serializer.save(
            created_by=self.request.user,
            invoice_number=invoice_number
        )


# Audit and Reporting
class ContentAuditLogView(NetflixPermissionMixin, generics.ListAPIView):
    serializer_class = ContentAuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['action', 'entity_type']
    search_fields = ['actor_user__email', 'entity_name']
    required_scope = ('audit', 'read')
    
    def get_queryset(self):
        return ContentAuditLog.objects.select_related('actor_user').order_by('-timestamp')


# Role Management
class EnhancedRoleListCreateView(NetflixPermissionMixin, generics.ListCreateAPIView):
    queryset = EnhancedRole.objects.select_related('created_by').prefetch_related('user_assignments')
    serializer_class = EnhancedRoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_scope = ('roles', 'read')
    required_scope_write = ('roles', 'write')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class UserRoleAssignmentView(NetflixPermissionMixin, generics.ListCreateAPIView):
    serializer_class = UserRoleAssignmentSerializer
    permission_classes = [permissions.IsAuthenticated]
    required_scope = ('roles', 'read')
    required_scope_write = ('roles', 'write')
    
    def get_queryset(self):
        user_id = self.kwargs.get('user_id')
        if user_id:
            return UserRoleAssignment.objects.filter(user_id=user_id).select_related(
                'user', 'role', 'assigned_by'
            )
        return UserRoleAssignment.objects.select_related('user', 'role', 'assigned_by')
    
    def perform_create(self, serializer):
        serializer.save(assigned_by=self.request.user)


# Utility Views
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def dashboard_stats(request):
    """Get dashboard statistics"""
    if not request.user.is_staff:
        return Response({'error': 'Staff access required'}, status=status.HTTP_403_FORBIDDEN)
    
    stats = {
        'total_users': User.objects.count(),
        'active_users': User.objects.filter(is_active=True).count(),
        'total_titles': Title.objects.count(),
        'total_episodes': Episode.objects.count(),
        'total_assets': Asset.objects.count(),
        'pending_invoices': Invoice.objects.filter(status='SENT').count(),
        'monthly_revenue': ManualPayment.objects.filter(
            date_received__month=timezone.now().month,
            verified=True
        ).aggregate(total=Sum('amount'))['total'] or 0,
    }
    
    return Response(stats)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def bulk_title_operations(request):
    """Perform bulk operations on titles"""
    serializer = BulkTitleUpdateSerializer(data=request.data)
    if serializer.is_valid():
        title_ids = serializer.validated_data['title_ids']
        action = serializer.validated_data['action']
        
        titles = Title.objects.filter(id__in=title_ids)
        
        if action == 'publish':
            titles.update(visibility='PUBLIC', updated_by=request.user)
        elif action == 'unpublish':
            titles.update(visibility='PRIVATE', updated_by=request.user)
        elif action == 'delete':
            titles.delete()
        
        return Response({'message': f'{action} completed for {len(title_ids)} titles'})
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def content_recommendations(request):
    """Get content recommendations for user"""
    user = request.user
    profile_id = request.query_params.get('profile_id')
    
    if profile_id:
        try:
            profile = UserProfile.objects.get(id=profile_id, user=user)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Profile not found'}, status=status.HTTP_404_NOT_FOUND)
    else:
        # Use first profile or create one
        profile = user.viewing_profiles.first()
        if not profile:
            return Response({'recommendations': []})
    
    # Simple recommendation algorithm based on:
    # 1. User's ratings
    # 2. Popular content
    # 3. Recently added content
    
    # Get user's highly rated content genres
    user_genres = Rating.objects.filter(
        profile=profile, 
        stars__gte=4
    ).values_list('title__genres', flat=True)
    
    # Get popular content in those genres
    recommendations = Title.objects.filter(
        visibility='PUBLIC',
        genres__in=user_genres
    ).annotate(
        avg_rating=Avg('ratings__stars'),
        rating_count=Count('ratings')
    ).filter(
        rating_count__gte=5,  # At least 5 ratings
        avg_rating__gte=3.5   # Good average rating
    ).order_by('-avg_rating', '-rating_count')[:20]
    
    # Add recently added content
    recent_content = Title.objects.filter(
        visibility='PUBLIC'
    ).order_by('-created_at')[:10]
    
    # Combine and serialize
    all_recommendations = list(recommendations) + list(recent_content)
    # Remove duplicates while preserving order
    seen = set()
    unique_recommendations = []
    for title in all_recommendations:
        if title.id not in seen:
            unique_recommendations.append(title)
            seen.add(title.id)
    
    serializer = TitleListSerializer(unique_recommendations[:30], many=True)
    return Response({'recommendations': serializer.data})
