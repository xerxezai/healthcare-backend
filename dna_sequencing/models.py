from django.conf import settings
from django.db import models


class DNASample(models.Model):
    STATUS_CHOICES = [
        ('received', 'Received'),
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('sequencing', 'Sequencing'),
        ('analysis', 'Analysis'),
        ('completed', 'Completed'),
        ('failed', 'QC Failed'),
        ('on_hold', 'On Hold'),
    ]
    STATUS_DISPLAY = {
        'received': 'Received',
        'queued': 'Received',
        'processing': 'Processing',
        'sequencing': 'Sequencing',
        'analysis': 'Analysis',
        'completed': 'Complete',
        'failed': 'QC Failed',
        'on_hold': 'On Hold',
    }
    STATUS_PROGRESS = {
        'received': 15,
        'queued': 15,
        'processing': 40,
        'sequencing': 65,
        'analysis': 85,
        'completed': 100,
        'failed': 30,
        'on_hold': 50,
    }
    PRIORITY_CHOICES = [
        ('urgent', 'Urgent'),
        ('high', 'High'),
        ('normal', 'Normal'),
        ('low', 'Low'),
    ]

    sample_id = models.CharField(max_length=100, unique=True)
    analysis_id = models.CharField(max_length=100, blank=True)
    patient_name = models.CharField(max_length=200)
    patient_id = models.CharField(max_length=100, blank=True)
    sample_type = models.CharField(max_length=50, blank=True)  # Blood / Saliva / Tissue
    sequencing_type = models.CharField(max_length=100, blank=True)
    analysis_type = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='received')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')

    platform = models.CharField(max_length=100, blank=True)
    technician = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    failure_reason = models.TextField(blank=True)
    collection_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)
    estimated_completion = models.DateTimeField(null=True, blank=True)

    coverage = models.CharField(max_length=20, blank=True)
    quality_score = models.FloatField(null=True, blank=True)
    total_reads = models.CharField(max_length=20, blank=True)
    mapped_reads = models.CharField(max_length=20, blank=True)
    mapping_rate = models.FloatField(null=True, blank=True)

    total_variants = models.IntegerField(default=0)
    snvs = models.IntegerField(default=0)
    indels = models.IntegerField(default=0)
    high_impact = models.IntegerField(default=0)
    moderate_impact = models.IntegerField(default=0)
    low_impact = models.IntegerField(default=0)
    pathogenic = models.IntegerField(default=0)
    likely_pathogenic = models.IntegerField(default=0)
    vus = models.IntegerField(default=0)
    benign = models.IntegerField(default=0)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.sample_id} ({self.patient_name})"

    @property
    def progress(self):
        return self.STATUS_PROGRESS.get(self.status, 0)

    @property
    def status_display(self):
        return self.STATUS_DISPLAY.get(self.status, self.status)

    def to_summary_dict(self):
        return {
            'id': self.id,
            'sample_id': self.sample_id,
            'patient_name': self.patient_name,
            'patient_id': self.patient_id,
            'status': self.status_display,
            'priority': self.get_priority_display(),
            'sample_type': self.sample_type,
            'sequencing_type': self.sequencing_type,
            'analysis_type': self.analysis_type,
            'collection_date': self.collection_date.isoformat() if self.collection_date else None,
            'received_date': self.received_date.isoformat() if self.received_date else None,
            'progress': self.progress,
            'quality_score': self.quality_score,
            'platform': self.platform,
            'technician': self.technician,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'completion_date': self.completed_at.date().isoformat() if self.completed_at else None,
            'notes': self.notes,
            'failure_reason': self.failure_reason,
        }


class DNAVariant(models.Model):
    sample = models.ForeignKey(DNASample, related_name='variant_records', on_delete=models.CASCADE)

    chromosome = models.CharField(max_length=10)
    position = models.BigIntegerField()
    ref = models.CharField(max_length=50)
    alt = models.CharField(max_length=50)
    gene = models.CharField(max_length=50)
    variant_type = models.CharField(max_length=20)
    impact = models.CharField(max_length=20)
    consequence = models.CharField(max_length=100)
    clinical_significance = models.CharField(max_length=50)
    allele_frequency = models.FloatField(null=True, blank=True)
    coverage = models.IntegerField(null=True, blank=True)
    quality = models.FloatField(null=True, blank=True)
    genotype = models.CharField(max_length=20, blank=True)
    dbsnp_id = models.CharField(max_length=50, blank=True)
    cosmic_id = models.CharField(max_length=50, blank=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.gene} {self.chromosome}:{self.position} ({self.clinical_significance})"
