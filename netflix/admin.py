# Netflix app admin interface
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Genre, Title, Season, Episode, Asset, UserProfile, UserEntitlements,
    Device, Watchlist, PlaybackHistory, Rating, ManualPayment, Invoice,
    ContentAuditLog, EnhancedRole, UserRoleAssignment
)


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)


class SeasonInline(admin.TabularInline):
    model = Season
    extra = 1
    fields = ('number', 'name', 'overview', 'air_date')


class AssetInline(admin.TabularInline):
    model = Asset
    extra = 1
    fields = ('kind', 'file_name', 'quality', 'language', 'file_size')
    readonly_fields = ('file_size',)


@admin.register(Title)
class TitleAdmin(admin.ModelAdmin):
    list_display = ('name', 'type', 'release_year', 'rating', 'visibility', 'created_by', 'created_at')
    list_filter = ('type', 'rating', 'visibility', 'release_year', 'created_at')
    search_fields = ('name', 'synopsis')
    filter_horizontal = ('genres',)
    inlines = [SeasonInline, AssetInline]
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'type', 'name', 'synopsis', 'release_year', 'rating')
        }),
        ('Categorization', {
            'fields': ('genres', 'tags', 'visibility')
        }),
        ('Metadata', {
            'fields': ('duration_minutes', 'imdb_id', 'tmdb_id', 'regions')
        }),
        ('Management', {
            'fields': ('created_by', 'updated_by', 'created_at', 'updated_at')
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)


class EpisodeInline(admin.TabularInline):
    model = Episode
    extra = 1
    fields = ('number', 'name', 'runtime_minutes', 'air_date')


@admin.register(Season)
class SeasonAdmin(admin.ModelAdmin):
    list_display = ('title', 'number', 'name', 'episode_count', 'air_date')
    list_filter = ('title__type', 'air_date')
    search_fields = ('title__name', 'name')
    inlines = [EpisodeInline]
    
    def episode_count(self, obj):
        return obj.episodes.count()
    episode_count.short_description = 'Episodes'


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ('title_name', 'season_number', 'number', 'name', 'runtime_minutes', 'air_date')
    list_filter = ('season__title__name', 'air_date')
    search_fields = ('name', 'synopsis', 'season__title__name')
    inlines = [AssetInline]
    
    def title_name(self, obj):
        return obj.season.title.name
    title_name.short_description = 'Title'
    
    def season_number(self, obj):
        return obj.season.number
    season_number.short_description = 'Season'


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ('content_name', 'kind', 'quality', 'language', 'file_size_mb', 'created_at')
    list_filter = ('kind', 'quality', 'language', 'drm_protected', 'created_at')
    search_fields = ('file_name', 'title__name', 'episode__name')
    readonly_fields = ('id', 'file_size_mb', 'created_at')
    
    def content_name(self, obj):
        if obj.episode:
            return f"{obj.episode.season.title.name} S{obj.episode.season.number}E{obj.episode.number}"
        return obj.title.name if obj.title else "No content"
    content_name.short_description = 'Content'
    
    def file_size_mb(self, obj):
        if obj.file_size:
            return f"{obj.file_size / (1024*1024):.2f} MB"
        return "Unknown"
    file_size_mb.short_description = 'File Size'


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'name', 'maturity_rating', 'is_kid', 'created_at')
    list_filter = ('maturity_rating', 'is_kid', 'created_at')
    search_fields = ('user__email', 'name')
    readonly_fields = ('id', 'created_at')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'


@admin.register(UserEntitlements)
class UserEntitlementsAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'account_status', 'stream_access', 'max_profiles', 'max_devices', 'expiry_date')
    list_filter = ('account_status', 'stream_access', 'hd_enabled', 'uhd_enabled')
    search_fields = ('user__email',)
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Account Status', {
            'fields': ('account_status', 'expiry_date')
        }),
        ('Access Controls', {
            'fields': ('stream_access', 'max_profiles', 'max_devices')
        }),
        ('Quality Settings', {
            'fields': ('hd_enabled', 'uhd_enabled', 'download_enabled')
        }),
        ('Regional Access', {
            'fields': ('region_access',)
        }),
        ('Audit Trail', {
            'fields': ('last_modified_by', 'modification_reason', 'created_at', 'updated_at')
        })
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def save_model(self, request, obj, form, change):
        if change:  # Only for updates
            obj.last_modified_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'device_name', 'device_type', 'os', 'last_seen_at', 'is_blocked')
    list_filter = ('device_type', 'is_blocked', 'last_seen_at')
    search_fields = ('user__email', 'device_name', 'device_id')
    readonly_fields = ('id', 'created_at', 'last_seen_at')
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('profile_name', 'user_email', 'title_name', 'added_at')
    list_filter = ('added_at',)
    search_fields = ('profile__user__email', 'profile__name', 'title__name')
    readonly_fields = ('id', 'added_at')
    
    def profile_name(self, obj):
        return obj.profile.name
    profile_name.short_description = 'Profile'
    
    def user_email(self, obj):
        return obj.profile.user.email
    user_email.short_description = 'User'
    
    def title_name(self, obj):
        return obj.title.name
    title_name.short_description = 'Title'


@admin.register(PlaybackHistory)
class PlaybackHistoryAdmin(admin.ModelAdmin):
    list_display = ('profile_name', 'content_name', 'completed_percent', 'completed', 'updated_at')
    list_filter = ('completed', 'updated_at')
    search_fields = ('profile__user__email', 'title__name', 'episode__name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def profile_name(self, obj):
        return f"{obj.profile.user.email} - {obj.profile.name}"
    profile_name.short_description = 'Profile'
    
    def content_name(self, obj):
        if obj.episode:
            return f"{obj.title.name} S{obj.episode.season.number}E{obj.episode.number}"
        return obj.title.name
    content_name.short_description = 'Content'


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('profile_name', 'title_name', 'stars', 'created_at')
    list_filter = ('stars', 'created_at')
    search_fields = ('profile__user__email', 'title__name', 'review_text')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    def profile_name(self, obj):
        return f"{obj.profile.user.email} - {obj.profile.name}"
    profile_name.short_description = 'Profile'
    
    def title_name(self, obj):
        return obj.title.name
    title_name.short_description = 'Title'


@admin.register(ManualPayment)
class ManualPaymentAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'amount_display', 'method', 'date_received', 'verified', 'recorded_by')
    list_filter = ('method', 'currency', 'verified', 'date_received')
    search_fields = ('user__email', 'reference_no', 'notes')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('user', 'method', 'reference_no', 'amount', 'currency', 'date_received')
        }),
        ('Documentation', {
            'fields': ('notes', 'receipt_file')
        }),
        ('Verification', {
            'fields': ('verified', 'verification_notes')
        }),
        ('Audit', {
            'fields': ('recorded_by', 'created_at', 'updated_at')
        })
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def amount_display(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_display.short_description = 'Amount'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.recorded_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'user_email', 'amount_display', 'status', 'due_date', 'created_by')
    list_filter = ('status', 'currency', 'due_date', 'created_at')
    search_fields = ('invoice_number', 'user__email', 'description')
    filter_horizontal = ('payments',)
    readonly_fields = ('id', 'paid_amount', 'balance', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Invoice Details', {
            'fields': ('invoice_number', 'user', 'amount', 'currency', 'status')
        }),
        ('Dates', {
            'fields': ('issue_date', 'due_date', 'paid_date')
        }),
        ('Content', {
            'fields': ('description', 'notes')
        }),
        ('Payments', {
            'fields': ('payments', 'paid_amount', 'balance')
        }),
        ('Management', {
            'fields': ('created_by', 'created_at', 'updated_at')
        })
    )
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def amount_display(self, obj):
        return f"{obj.amount} {obj.currency}"
    amount_display.short_description = 'Amount'
    
    def paid_amount(self, obj):
        return f"{obj.get_paid_amount()} {obj.currency}"
    paid_amount.short_description = 'Paid Amount'
    
    def balance(self, obj):
        balance = obj.amount - obj.get_paid_amount()
        return f"{balance} {obj.currency}"
    balance.short_description = 'Balance'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ContentAuditLog)
class ContentAuditLogAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'actor_display', 'action', 'entity_type', 'entity_name')
    list_filter = ('action', 'entity_type', 'timestamp')
    search_fields = ('actor_user__email', 'entity_name', 'entity_id')
    readonly_fields = ('id', 'timestamp')
    
    def actor_display(self, obj):
        return obj.actor_user.email if obj.actor_user else 'System'
    actor_display.short_description = 'Actor'
    
    def has_add_permission(self, request):
        return False  # Audit logs should not be manually created
    
    def has_change_permission(self, request, obj=None):
        return False  # Audit logs should not be edited
    
    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser  # Only superusers can delete audit logs


@admin.register(EnhancedRole)
class EnhancedRoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'role_type', 'is_system', 'created_by', 'created_at')
    list_filter = ('role_type', 'is_system', 'created_at')
    search_fields = ('name', 'description')
    readonly_fields = ('created_at', 'updated_at')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        if obj and obj.is_system:
            return False  # System roles cannot be deleted
        return super().has_delete_permission(request, obj)


@admin.register(UserRoleAssignment)
class UserRoleAssignmentAdmin(admin.ModelAdmin):
    list_display = ('user_email', 'role_name', 'assigned_by', 'assigned_at')
    list_filter = ('role__role_type', 'assigned_at')
    search_fields = ('user__email', 'role__name')
    readonly_fields = ('assigned_at',)
    
    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'User'
    
    def role_name(self, obj):
        return obj.role.name
    role_name.short_description = 'Role'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.assigned_by = request.user
        super().save_model(request, obj, form, change)


# Register the app with custom admin site title
admin.site.site_header = "Netflix-like Content Management System"
admin.site.site_title = "Netflix CMS Admin"
admin.site.index_title = "Welcome to Netflix CMS Administration"
