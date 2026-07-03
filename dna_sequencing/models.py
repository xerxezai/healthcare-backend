from django.conf import settings
from django.db import models


class DNASample(models.Model):
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    sample_id = models.CharField(max_length=100, unique=True)
    analysis_id = models.CharField(max_length=100, blank=True)
    patient_name = models.CharField(max_length=200)
    sequencing_type = models.CharField(max_length=100, blank=True)
    analysis_type = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')

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
