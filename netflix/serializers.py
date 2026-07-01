# Netflix app serializers
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Genre, Title, Season, Episode, Asset, UserProfile, UserEntitlements,
    Device, Watchlist, PlaybackHistory, Rating, ManualPayment, Invoice,
    ContentAuditLog, EnhancedRole, UserRoleAssignment
)

User = get_user_model()


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ['id', 'name', 'description', 'created_at']


class AssetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Asset
        fields = [
            'id', 'kind', 'file_name', 'file_url', 'file_size',
            'codec', 'quality', 'bitrate', 'duration_seconds',
            'language', 'drm_protected', 'created_at'
        ]


class EpisodeSerializer(serializers.ModelSerializer):
    assets = AssetSerializer(many=True, read_only=True)
    
    class Meta:
        model = Episode
        fields = [
            'id', 'number', 'name', 'synopsis', 'runtime_minutes',
            'air_date', 'assets', 'created_at'
        ]


class SeasonSerializer(serializers.ModelSerializer):
    episodes = EpisodeSerializer(many=True, read_only=True)
    episode_count = serializers.IntegerField(source='episodes.count', read_only=True)
    
    class Meta:
        model = Season
        fields = [
            'id', 'number', 'name', 'overview', 'air_date',
            'episodes', 'episode_count', 'created_at'
        ]


class TitleListSerializer(serializers.ModelSerializer):
    """Simplified serializer for title lists"""
    genres = GenreSerializer(many=True, read_only=True)
    poster_url = serializers.SerializerMethodField()
    backdrop_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Title
        fields = [
            'id', 'type', 'name', 'synopsis', 'release_year', 'rating',
            'genres', 'tags', 'regions', 'visibility', 'duration_minutes',
            'poster_url', 'backdrop_url', 'created_at'
        ]
    
    def get_poster_url(self, obj):
        poster = obj.assets.filter(kind='POSTER').first()
        return poster.file_url if poster else None
    
    def get_backdrop_url(self, obj):
        backdrop = obj.assets.filter(kind='BACKDROP').first()
        return backdrop.file_url if backdrop else None


class TitleDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual title views"""
    genres = GenreSerializer(many=True, read_only=True)
    seasons = SeasonSerializer(many=True, read_only=True)
    assets = AssetSerializer(many=True, read_only=True)
    season_count = serializers.IntegerField(source='seasons.count', read_only=True)
    episode_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    
    class Meta:
        model = Title
        fields = [
            'id', 'type', 'name', 'synopsis', 'release_year', 'rating',
            'genres', 'tags', 'regions', 'visibility', 'duration_minutes',
            'imdb_id', 'tmdb_id', 'seasons', 'assets', 'season_count',
            'episode_count', 'average_rating', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
    
    def get_episode_count(self, obj):
        return sum(season.episodes.count() for season in obj.seasons.all())
    
    def get_average_rating(self, obj):
        ratings = obj.ratings.all()
        if ratings:
            return sum(r.stars for r in ratings) / len(ratings)
        return None


class TitleCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating titles"""
    genre_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Title
        fields = [
            'type', 'name', 'synopsis', 'release_year', 'rating',
            'tags', 'regions', 'visibility', 'duration_minutes',
            'imdb_id', 'tmdb_id', 'genre_ids'
        ]
    
    def create(self, validated_data):
        genre_ids = validated_data.pop('genre_ids', [])
        title = Title.objects.create(**validated_data)
        if genre_ids:
            title.genres.set(Genre.objects.filter(id__in=genre_ids))
        return title
    
    def update(self, instance, validated_data):
        genre_ids = validated_data.pop('genre_ids', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if genre_ids is not None:
            instance.genres.set(Genre.objects.filter(id__in=genre_ids))
        
        return instance


class UserProfileSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = UserProfile
        fields = [
            'id', 'user', 'user_email', 'name', 'avatar_url',
            'maturity_rating', 'pin', 'is_kid', 'language_preference',
            'created_at'
        ]
        extra_kwargs = {
            'pin': {'write_only': True}
        }


class UserEntitlementsSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    last_modified_by_name = serializers.CharField(source='last_modified_by.full_name', read_only=True)
    
    class Meta:
        model = UserEntitlements
        fields = [
            'user', 'user_email', 'account_status', 'stream_access',
            'max_profiles', 'max_devices', 'hd_enabled', 'uhd_enabled',
            'download_enabled', 'region_access', 'expiry_date',
            'is_active', 'last_modified_by', 'last_modified_by_name',
            'modification_reason', 'created_at', 'updated_at'
        ]


class DeviceSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    
    class Meta:
        model = Device
        fields = [
            'id', 'user', 'user_email', 'device_type', 'device_name',
            'device_id', 'os', 'browser', 'app_version', 'last_seen_at',
            'is_blocked', 'created_at'
        ]


class WatchlistSerializer(serializers.ModelSerializer):
    title = TitleListSerializer(read_only=True)
    title_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Watchlist
        fields = ['id', 'profile', 'title', 'title_id', 'added_at']
    
    def create(self, validated_data):
        title_id = validated_data.pop('title_id')
        title = Title.objects.get(id=title_id)
        return Watchlist.objects.create(title=title, **validated_data)


class PlaybackHistorySerializer(serializers.ModelSerializer):
    title = TitleListSerializer(read_only=True)
    episode = EpisodeSerializer(read_only=True)
    content_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PlaybackHistory
        fields = [
            'id', 'profile', 'title', 'episode', 'content_name',
            'position_seconds', 'duration_seconds', 'completed_percent',
            'completed', 'device', 'created_at', 'updated_at'
        ]
    
    def get_content_name(self, obj):
        if obj.episode:
            return f"{obj.title.name} S{obj.episode.season.number}E{obj.episode.number}: {obj.episode.name}"
        return obj.title.name


class PlaybackProgressSerializer(serializers.ModelSerializer):
    """Serializer for updating playback progress"""
    class Meta:
        model = PlaybackHistory
        fields = [
            'profile', 'title', 'episode', 'position_seconds',
            'duration_seconds', 'completed_percent', 'completed'
        ]


class RatingSerializer(serializers.ModelSerializer):
    title = TitleListSerializer(read_only=True)
    title_id = serializers.UUIDField(write_only=True)
    profile_name = serializers.CharField(source='profile.name', read_only=True)
    
    class Meta:
        model = Rating
        fields = [
            'id', 'profile', 'profile_name', 'title', 'title_id',
            'stars', 'review_text', 'created_at', 'updated_at'
        ]
    
    def create(self, validated_data):
        title_id = validated_data.pop('title_id')
        title = Title.objects.get(id=title_id)
        return Rating.objects.create(title=title, **validated_data)


class ManualPaymentSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    recorded_by_name = serializers.CharField(source='recorded_by.full_name', read_only=True)
    
    class Meta:
        model = ManualPayment
        fields = [
            'id', 'user', 'user_email', 'method', 'reference_no',
            'amount', 'currency', 'date_received', 'notes',
            'receipt_file', 'verified', 'verification_notes',
            'recorded_by', 'recorded_by_name', 'created_at', 'updated_at'
        ]


class InvoiceSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    payments = ManualPaymentSerializer(many=True, read_only=True)
    paid_amount = serializers.DecimalField(
        source='get_paid_amount', 
        max_digits=10, 
        decimal_places=2, 
        read_only=True
    )
    balance = serializers.SerializerMethodField()
    is_fully_paid = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = Invoice
        fields = [
            'id', 'invoice_number', 'user', 'user_email', 'amount',
            'currency', 'status', 'issue_date', 'due_date', 'paid_date',
            'description', 'notes', 'payments', 'paid_amount', 'balance',
            'is_fully_paid', 'created_by', 'created_by_name',
            'created_at', 'updated_at'
        ]
    
    def get_balance(self, obj):
        return obj.amount - obj.get_paid_amount()


class ContentAuditLogSerializer(serializers.ModelSerializer):
    actor_name = serializers.CharField(source='actor_user.full_name', read_only=True)
    actor_email = serializers.CharField(source='actor_user.email', read_only=True)
    
    class Meta:
        model = ContentAuditLog
        fields = [
            'id', 'actor_user', 'actor_name', 'actor_email', 'action',
            'entity_type', 'entity_id', 'entity_name', 'old_values',
            'new_values', 'ip_address', 'user_agent', 'request_path',
            'timestamp'
        ]


class EnhancedRoleSerializer(serializers.ModelSerializer):
    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)
    user_count = serializers.IntegerField(source='user_assignments.count', read_only=True)
    
    class Meta:
        model = EnhancedRole
        fields = [
            'id', 'name', 'role_type', 'is_system', 'parent_role',
            'description', 'scopes', 'created_by', 'created_by_name',
            'user_count', 'created_at', 'updated_at'
        ]


class UserRoleAssignmentSerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    role_name = serializers.CharField(source='role.name', read_only=True)
    assigned_by_name = serializers.CharField(source='assigned_by.full_name', read_only=True)
    
    class Meta:
        model = UserRoleAssignment
        fields = [
            'id', 'user', 'user_email', 'user_name', 'role',
            'role_name', 'assigned_by', 'assigned_by_name', 'assigned_at'
        ]


class UserSerializer(serializers.ModelSerializer):
    """Extended user serializer with Netflix entitlements"""
    netflix_entitlements = UserEntitlementsSerializer(read_only=True)
    viewing_profiles = UserProfileSerializer(many=True, read_only=True)
    streaming_devices = DeviceSerializer(many=True, read_only=True)
    role_assignments = UserRoleAssignmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'full_name', 'phone_number',
            'is_active', 'is_staff', 'is_superuser', 'role',
            'netflix_entitlements', 'viewing_profiles', 'streaming_devices',
            'role_assignments', 'date_joined', 'last_login'
        ]


# Bulk operation serializers
class BulkTitleUpdateSerializer(serializers.Serializer):
    """Serializer for bulk title operations"""
    title_ids = serializers.ListField(child=serializers.UUIDField())
    action = serializers.ChoiceField(choices=['publish', 'unpublish', 'delete'])
    visibility = serializers.ChoiceField(
        choices=Title.VISIBILITY_CHOICES,
        required=False
    )


class ContentImportSerializer(serializers.Serializer):
    """Serializer for importing content from CSV/JSON"""
    import_file = serializers.FileField()
    format = serializers.ChoiceField(choices=['csv', 'json'])
    overwrite_existing = serializers.BooleanField(default=False)
