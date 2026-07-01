from django.contrib import admin
from .models import (
    PathologyDepartment, PathologyTest, Patient, PathologyOrder,
    PathologyOrderTest, Specimen, PathologyReport, DigitalSlide,
    PathologyQualityControl
)


@admin.register(PathologyDepartment)
class PathologyDepartmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'location', 'head_pathologist', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'code', 'location']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PathologyTest)
class PathologyTestAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'category', 'cost', 'processing_time_hours', 'is_active']
    list_filter = ['category', 'is_active', 'requires_fasting']
    search_fields = ['name', 'code', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'code', 'category', 'description')
        }),
        ('Technical Details', {
            'fields': ('specimen_type', 'test_methodology', 'processing_time_hours', 'normal_range')
        }),
        ('Cost and Requirements', {
            'fields': ('cost', 'requires_fasting', 'special_instructions')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ['patient_id', 'full_name', 'date_of_birth', 'gender', 'phone']
    search_fields = ['patient_id', 'first_name', 'last_name', 'medical_record_number']
    list_filter = ['gender', 'created_at']
    readonly_fields = ['created_at', 'updated_at', 'age']
    fieldsets = (
        ('Personal Information', {
            'fields': ('patient_id', 'first_name', 'last_name', 'date_of_birth', 'gender')
        }),
        ('Contact Information', {
            'fields': ('phone', 'email', 'address', 'emergency_contact')
        }),
        ('Medical Records', {
            'fields': ('medical_record_number', 'insurance_number')
        }),
        ('System Information', {
            'fields': ('age', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


class PathologyOrderTestInline(admin.TabularInline):
    model = PathologyOrderTest
    extra = 1
    readonly_fields = ['started_at', 'completed_at']


@admin.register(PathologyOrder)
class PathologyOrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'patient', 'ordering_physician', 'status', 'priority', 'order_date', 'total_cost']
    list_filter = ['status', 'priority', 'order_date', 'department']
    search_fields = ['order_id', 'patient__first_name', 'patient__last_name', 'ordering_physician__username']
    readonly_fields = ['order_id', 'created_at', 'updated_at']
    inlines = [PathologyOrderTestInline]
    date_hierarchy = 'order_date'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_id', 'patient', 'ordering_physician', 'department')
        }),
        ('Order Details', {
            'fields': ('status', 'priority', 'clinical_history', 'special_instructions', 'notes')
        }),
        ('Timing', {
            'fields': ('order_date', 'collection_date', 'expected_completion')
        }),
        ('Financial', {
            'fields': ('total_cost',)
        }),
        ('System Information', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Specimen)
class SpecimenAdmin(admin.ModelAdmin):
    list_display = ['specimen_id', 'order', 'specimen_type', 'status', 'collection_datetime', 'collected_by']
    list_filter = ['specimen_type', 'status', 'collection_datetime']
    search_fields = ['specimen_id', 'order__order_id', 'order__patient__first_name']
    readonly_fields = ['specimen_id', 'created_at', 'updated_at']
    date_hierarchy = 'collection_datetime'


@admin.register(PathologyReport)
class PathologyReportAdmin(admin.ModelAdmin):
    list_display = ['report_id', 'order_test', 'pathologist', 'status', 'result_status', 'created_at']
    list_filter = ['status', 'result_status', 'confidence_level', 'created_at']
    search_fields = ['report_id', 'order_test__order__order_id', 'pathologist__username']
    readonly_fields = ['report_id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Report Information', {
            'fields': ('report_id', 'order_test', 'specimen', 'pathologist')
        }),
        ('Examination Results', {
            'fields': ('gross_description', 'microscopic_description', 'interpretation', 'diagnosis')
        }),
        ('Technical Details', {
            'fields': ('staining_methods', 'special_studies', 'immunohistochemistry', 'molecular_findings')
        }),
        ('Status and Quality', {
            'fields': ('status', 'result_status', 'confidence_level', 'recommendations')
        }),
        ('Timing', {
            'fields': ('reported_at', 'reviewed_at', 'finalized_at')
        }),
        ('Additional Information', {
            'fields': ('technical_notes', 'quality_control_notes', 'amendments'),
            'classes': ('collapse',)
        }),
        ('Digital Assets', {
            'fields': ('digital_slides', 'attachments'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(DigitalSlide)
class DigitalSlideAdmin(admin.ModelAdmin):
    list_display = ['slide_id', 'report', 'title', 'stain_type', 'magnification', 'created_by', 'created_at']
    list_filter = ['stain_type', 'format', 'created_at']
    search_fields = ['slide_id', 'title', 'report__report_id']
    readonly_fields = ['slide_id', 'file_size', 'created_at', 'updated_at']


@admin.register(PathologyQualityControl)
class PathologyQualityControlAdmin(admin.ModelAdmin):
    list_display = ['qc_id', 'qc_type', 'title', 'performed_by', 'performed_date', 'passed']
    list_filter = ['qc_type', 'passed', 'performed_date']
    search_fields = ['qc_id', 'title', 'equipment_instrument']
    readonly_fields = ['qc_id', 'created_at', 'updated_at']
    date_hierarchy = 'performed_date'
