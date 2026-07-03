"""
🧬 DNA Sequencing Views
=====================

Main views for DNA sequencing dashboard and analysis
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json
import random
from datetime import datetime, timedelta
import logging

from .models import DNASample, DNAVariant

logger = logging.getLogger(__name__)

# Reference variants used to seed simulated (but consistent, per-sample)
# analysis results, since there is no real sequencing pipeline behind this.
_KNOWN_GENE_VARIANTS = [
    {'chromosome': 'chr17', 'position': 43094124, 'ref': 'G', 'alt': 'A', 'gene': 'BRCA1',
     'consequence': 'missense_variant', 'clinical_significance': 'Pathogenic', 'dbsnp_id': 'rs80357382', 'cosmic_id': 'COSM5739'},
    {'chromosome': 'chr13', 'position': 32936732, 'ref': 'T', 'alt': 'C', 'gene': 'BRCA2',
     'consequence': 'missense_variant', 'clinical_significance': 'Pathogenic', 'dbsnp_id': 'rs81002825', 'cosmic_id': 'COSM6904'},
    {'chromosome': 'chr7', 'position': 117559590, 'ref': 'C', 'alt': 'T', 'gene': 'CFTR',
     'consequence': 'stop_gained', 'clinical_significance': 'Pathogenic', 'dbsnp_id': 'rs113993960', 'cosmic_id': ''},
    {'chromosome': 'chr3', 'position': 37034946, 'ref': 'A', 'alt': 'G', 'gene': 'MLH1',
     'consequence': 'missense_variant', 'clinical_significance': 'Likely pathogenic', 'dbsnp_id': 'rs63750231', 'cosmic_id': ''},
    {'chromosome': 'chr2', 'position': 47630304, 'ref': 'G', 'alt': 'A', 'gene': 'MSH2',
     'consequence': 'splice_donor_variant', 'clinical_significance': 'Likely pathogenic', 'dbsnp_id': 'rs63750969', 'cosmic_id': ''},
    {'chromosome': 'chr19', 'position': 11224304, 'ref': 'C', 'alt': 'T', 'gene': 'LDLR',
     'consequence': 'missense_variant', 'clinical_significance': 'Uncertain significance', 'dbsnp_id': 'rs137929305', 'cosmic_id': ''},
    {'chromosome': 'chr11', 'position': 47364249, 'ref': 'T', 'alt': 'C', 'gene': 'MYBPC3',
     'consequence': 'missense_variant', 'clinical_significance': 'Uncertain significance', 'dbsnp_id': 'rs397516037', 'cosmic_id': ''},
    {'chromosome': 'chr1', 'position': 11856378, 'ref': 'G', 'alt': 'A', 'gene': 'MTHFR',
     'consequence': 'missense_variant', 'clinical_significance': 'Benign', 'dbsnp_id': 'rs1801133', 'cosmic_id': ''},
]


def _generate_simulated_analysis(sample_id, sequencing_type):
    """Deterministically generate plausible quality metrics + variants for a
    sample, seeded by its sample_id so results are stable across refetches."""
    rng = random.Random(sample_id)

    total_reads_m = rng.randint(400, 900)
    mapping_rate = round(rng.uniform(94.0, 99.5), 1)
    quality_score = round(rng.uniform(90.0, 99.5), 1)
    mapped_reads_m = round(total_reads_m * mapping_rate / 100)

    variants = []
    for ref in _KNOWN_GENE_VARIANTS:
        if rng.random() < 0.7:  # not every sample carries every reference variant
            variants.append({
                **ref,
                'variant_type': 'SNV',
                'impact': 'HIGH' if ref['clinical_significance'] in ('Pathogenic', 'Likely pathogenic') else 'MODERATE',
                'allele_frequency': round(rng.uniform(0.0001, 0.01), 4),
                'coverage': rng.randint(30, 90),
                'quality': round(rng.uniform(90.0, 99.9), 1),
                'genotype': rng.choice(['het', 'hom']),
            })

    pathogenic = sum(1 for v in variants if v['clinical_significance'] == 'Pathogenic')
    likely_pathogenic = sum(1 for v in variants if v['clinical_significance'] == 'Likely pathogenic')
    vus = sum(1 for v in variants if v['clinical_significance'] == 'Uncertain significance')
    benign = sum(1 for v in variants if v['clinical_significance'] == 'Benign')

    total_variants = rng.randint(3800000, 4900000)
    snvs = round(total_variants * 0.95)
    indels = total_variants - snvs

    return {
        'coverage': f"{rng.randint(30, 60)}x",
        'quality_score': quality_score,
        'total_reads': f"{total_reads_m / 1000:.1f}B" if total_reads_m >= 1000 else f"{total_reads_m}M",
        'mapped_reads': f"{mapped_reads_m / 1000:.1f}B" if mapped_reads_m >= 1000 else f"{mapped_reads_m}M",
        'mapping_rate': mapping_rate,
        'total_variants': total_variants,
        'snvs': snvs,
        'indels': indels,
        'high_impact': pathogenic + likely_pathogenic,
        'moderate_impact': vus,
        'low_impact': total_variants - (pathogenic + likely_pathogenic + vus + benign),
        'pathogenic': pathogenic,
        'likely_pathogenic': likely_pathogenic,
        'vus': vus,
        'benign': benign,
        'variants': variants,
    }

@require_http_methods(["GET"])
def get_dna_sequencing_dashboard(request):
    """Get DNA sequencing dashboard data"""
    try:
        dashboard_data = {
            'summary': {
                'total_samples': 47,
                'pending_analyses': 8,
                'completed_analyses': 32,
                'failed_analyses': 7,
                'total_variants': 28750,
                'high_impact_variants': 245,
                'medium_impact_variants': 1680,
                'low_impact_variants': 26825,
                'pathogenic_variants': 12,
                'likely_pathogenic': 33,
                'vus_variants': 156,
                'likely_benign': 892,
                'benign_variants': 27657
            },
            'recent_samples': [
                {
                    'id': 1,
                    'sample_id': 'WGS-2025-001',
                    'patient_name': 'John Smith',
                    'patient_id': 'P001234',
                    'status': 'completed',
                    'quality_score': 98.5,
                    'coverage': '45x',
                    'completion_date': '2025-09-02',
                    'analysis_type': 'Whole Genome Sequencing',
                    'indication': 'Hereditary Cancer Screening',
                    'urgency': 'routine',
                    'variants_found': 8924,
                    'pathogenic_found': 2
                },
                {
                    'id': 2,
                    'sample_id': 'ES-2025-002',
                    'patient_name': 'Sarah Johnson',
                    'patient_id': 'P001235',
                    'status': 'processing',
                    'quality_score': None,
                    'coverage': None,
                    'completion_date': None,
                    'analysis_type': 'Exome Sequencing',
                    'indication': 'Rare Disease Diagnosis',
                    'urgency': 'urgent',
                    'variants_found': None,
                    'pathogenic_found': None
                }
            ],
            'ai_models_status': {
                'deepvariant': 'online',
                'gatk_cnn': 'online',
                'nanovar': 'online',
                'pharmaco_ai': 'online',
                'omicsnet': 'maintenance'
            },
            'analysis_stats': {
                'avg_turnaround_time': 4.2,
                'success_rate': 91.5,
                'avg_quality_score': 96.8,
                'monthly_throughput': 156,
                'queue_length': 8
            },
            'sequencing_technologies': [
                {'name': 'Illumina NovaSeq', 'percentage': 59.6, 'samples': 28},
                {'name': 'Oxford Nanopore', 'percentage': 25.5, 'samples': 12},
                {'name': 'PacBio Sequel', 'percentage': 14.9, 'samples': 7}
            ],
            'variant_calling_stats': {
                'snvs_detected': 25480,
                'indels_detected': 3270,
                'cnvs_detected': 892,
                'svs_detected': 156
            }
        }
        
        return JsonResponse({
            'status': 'success',
            'data': dashboard_data
        })
        
    except Exception as e:
        logger.error(f"DNA Sequencing dashboard error: {str(e)}")
        return JsonResponse({
            'error': f'Failed to retrieve dashboard data: {str(e)}',
            'status': 'error'
        }, status=500)

@require_http_methods(["GET"])
def get_genome_analysis(request):
    """Get genome analysis data for a specific sample (?sample_id=...),
    falling back to the most recently analyzed sample if none is given."""
    try:
        sample_id = request.GET.get('sample_id')

        if sample_id:
            sample = DNASample.objects.filter(sample_id=sample_id).first()
            if not sample:
                return JsonResponse({
                    'status': 'error',
                    'error': f"No analysis found for sample_id '{sample_id}'"
                }, status=404)
        else:
            sample = DNASample.objects.order_by('-created_at').first()
            if not sample:
                return JsonResponse({
                    'status': 'error',
                    'error': 'No analyzed samples found'
                }, status=404)

        top_variants = [
            {
                'id': v.id,
                'chromosome': v.chromosome,
                'position': v.position,
                'ref': v.ref,
                'alt': v.alt,
                'gene': v.gene,
                'variant_type': v.variant_type,
                'impact': v.impact,
                'consequence': v.consequence,
                'clinical_significance': v.clinical_significance,
                'allele_frequency': v.allele_frequency,
                'coverage': v.coverage,
                'quality': v.quality,
                'genotype': v.genotype,
                'dbsnp_id': v.dbsnp_id,
                'cosmic_id': v.cosmic_id,
            }
            for v in sample.variant_records.all()
        ]

        analysis_data = {
            'sample_info': {
                'sample_id': sample.sample_id,
                'patient_name': sample.patient_name,
                'sequencing_type': sample.sequencing_type,
                'coverage': sample.coverage,
                'quality_score': sample.quality_score,
                'total_reads': sample.total_reads,
                'mapped_reads': sample.mapped_reads,
                'mapping_rate': sample.mapping_rate,
            },
            'variant_summary': {
                'total_variants': sample.total_variants,
                'snvs': sample.snvs,
                'indels': sample.indels,
                'high_impact': sample.high_impact,
                'moderate_impact': sample.moderate_impact,
                'low_impact': sample.low_impact,
                'pathogenic': sample.pathogenic,
                'likely_pathogenic': sample.likely_pathogenic,
                'vus': sample.vus,
                'benign': sample.benign,
            },
            'top_variants': top_variants,
        }

        return JsonResponse({
            'status': 'success',
            'data': analysis_data
        })

    except Exception as e:
        logger.error(f"Genome analysis error: {str(e)}")
        return JsonResponse({
            'error': f'Failed to retrieve analysis data: {str(e)}',
            'status': 'error'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def start_dna_analysis(request):
    """Start a new DNA sequencing analysis and persist it with generated results"""
    try:
        data = json.loads(request.body)

        # Extract analysis parameters
        sample_id = data.get('sample_id')
        patient_id = data.get('patient_id')  # actually the patient's name, per the upload form
        analysis_method = data.get('analysis_method')
        analysis_type = data.get('analysis_type', '')

        # Validate required fields
        if not all([sample_id, patient_id, analysis_method]):
            return JsonResponse({
                'success': False,
                'message': 'Missing required fields: sample_id, patient_id, analysis_method'
            }, status=400)

        # Generate a unique analysis ID
        analysis_id = f"ANALYSIS-{datetime.now().strftime('%Y%m%d%H%M%S')}-{random.randint(1000, 9999)}"

        # Generate consistent simulated results for this sample (no real
        # sequencing pipeline exists behind this platform yet)
        generated = _generate_simulated_analysis(sample_id, analysis_method)

        user = request.user if getattr(request, 'user', None) and request.user.is_authenticated else None

        sample, _created = DNASample.objects.update_or_create(
            sample_id=sample_id,
            defaults={
                'analysis_id': analysis_id,
                'patient_name': patient_id,
                'sequencing_type': analysis_method,
                'analysis_type': analysis_type,
                'status': 'completed',
                'coverage': generated['coverage'],
                'quality_score': generated['quality_score'],
                'total_reads': generated['total_reads'],
                'mapped_reads': generated['mapped_reads'],
                'mapping_rate': generated['mapping_rate'],
                'total_variants': generated['total_variants'],
                'snvs': generated['snvs'],
                'indels': generated['indels'],
                'high_impact': generated['high_impact'],
                'moderate_impact': generated['moderate_impact'],
                'low_impact': generated['low_impact'],
                'pathogenic': generated['pathogenic'],
                'likely_pathogenic': generated['likely_pathogenic'],
                'vus': generated['vus'],
                'benign': generated['benign'],
                'created_by': user,
                'completed_at': timezone.now(),
            }
        )

        # Replace any previous variant records for this sample (re-analysis case)
        sample.variant_records.all().delete()
        DNAVariant.objects.bulk_create([
            DNAVariant(sample=sample, **v) for v in generated['variants']
        ])

        logger.info(f"Started DNA analysis: {analysis_id} for sample {sample_id}")

        return JsonResponse({
            'success': True,
            'message': f'Analysis {analysis_id} started successfully',
            'analysis_id': analysis_id,
            'sample_id': sample_id,
            'status': 'completed'
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Invalid JSON format'
        }, status=400)
    except Exception as e:
        logger.error(f"Analysis start error: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': f'Failed to start analysis: {str(e)}'
        }, status=500)


def _generate_sample_id():
    return f"DNA-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"


def _parse_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        return None


def _build_sample_from_payload(payload):
    """Create (but don't save) a DNASample from a single sample's submitted
    fields, raising ValueError on missing required data."""
    patient_name = payload.get('patient_name')
    if not patient_name:
        raise ValueError('patient_name is required')

    sample_id = payload.get('sample_id') or _generate_sample_id()

    return DNASample(
        sample_id=sample_id,
        patient_name=patient_name,
        patient_id=payload.get('patient_id', ''),
        sample_type=payload.get('sample_type', ''),
        sequencing_type=payload.get('sequencing_type') or payload.get('analysis_method', ''),
        analysis_type=payload.get('analysis_type', ''),
        priority=payload.get('priority', 'normal'),
        platform=payload.get('platform', ''),
        technician=payload.get('technician', ''),
        notes=payload.get('notes', ''),
        collection_date=_parse_date(payload.get('collection_date')),
        received_date=_parse_date(payload.get('received_date')) or timezone.now().date(),
        status='received',
    )


@require_http_methods(["GET"])
def list_samples(request):
    """List all registered DNA samples for the Sample Management page"""
    try:
        samples = DNASample.objects.all()
        return JsonResponse([s.to_summary_dict() for s in samples], safe=False)
    except Exception as e:
        logger.error(f"List samples error: {str(e)}")
        return JsonResponse({'error': f'Failed to list samples: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def register_sample(request):
    """Register a single new sample (New Sample button)"""
    try:
        data = json.loads(request.body)
        sample = _build_sample_from_payload(data)
        sample.full_clean(exclude=['created_by'])
        sample.save()
        return JsonResponse({'success': True, 'sample': sample.to_summary_dict()}, status=201)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)
    except ValueError as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=400)
    except Exception as e:
        logger.error(f"Register sample error: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Failed to register sample: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def batch_register_samples(request):
    """Register multiple samples at once (Batch Upload button)"""
    try:
        data = json.loads(request.body)
        entries = data.get('samples', [])
        if not isinstance(entries, list) or not entries:
            return JsonResponse({'success': False, 'message': 'No samples provided'}, status=400)

        created = []
        errors = []
        for index, entry in enumerate(entries):
            try:
                sample = _build_sample_from_payload(entry)
                sample.full_clean(exclude=['created_by'])
                sample.save()
                created.append(sample.to_summary_dict())
            except Exception as row_error:
                errors.append({'row': index + 1, 'error': str(row_error)})

        return JsonResponse({
            'success': len(created) > 0,
            'created_count': len(created),
            'error_count': len(errors),
            'created': created,
            'errors': errors,
        }, status=201 if created else 400)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"Batch register error: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Batch upload failed: {str(e)}'}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def update_sample_status(request, sample_pk):
    """Update a sample's status (e.g. Start Processing / Put On Hold)"""
    try:
        sample = DNASample.objects.filter(pk=sample_pk).first()
        if not sample:
            return JsonResponse({'success': False, 'message': 'Sample not found'}, status=404)

        data = json.loads(request.body)
        new_status = data.get('status')
        valid_statuses = dict(DNASample.STATUS_CHOICES)
        if new_status not in valid_statuses:
            return JsonResponse({
                'success': False,
                'message': f"Invalid status '{new_status}'. Must be one of: {', '.join(valid_statuses)}"
            }, status=400)

        sample.status = new_status
        if new_status == 'completed' and not sample.completed_at:
            sample.completed_at = timezone.now()
        sample.save(update_fields=['status', 'completed_at'])

        return JsonResponse({'success': True, 'sample': sample.to_summary_dict()})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON format'}, status=400)
    except Exception as e:
        logger.error(f"Update sample status error: {str(e)}")
        return JsonResponse({'success': False, 'message': f'Failed to update status: {str(e)}'}, status=500)


# Soft-coded export functionality
@csrf_exempt
@require_http_methods(["POST"])
def export_pdf_report(request):
    """Export analysis data as PDF report"""
    try:
        data = json.loads(request.body)
        sample_id = data.get('sample_id', 'unknown')

        # In a real implementation, this would generate a proper PDF
        # For now, return a simple text-based report
        from django.http import HttpResponse

        sample = DNASample.objects.filter(sample_id=sample_id).first()
        if sample:
            variant_lines = "\n".join(
                f"  - {v.gene} {v.chromosome}:{v.position} {v.ref}>{v.alt} "
                f"({v.clinical_significance}, {v.impact} impact)"
                for v in sample.variant_records.all()
            ) or "  (none recorded)"

            report_content = f"""GENOME ANALYSIS REPORT
Sample ID: {sample.sample_id}
Patient: {sample.patient_name}
Status: {sample.status_display}
Sequencing Type: {sample.sequencing_type}
Coverage: {sample.coverage}
Quality Score: {sample.quality_score}
Total Reads: {sample.total_reads}
Mapped Reads: {sample.mapped_reads}
Mapping Rate: {sample.mapping_rate}

Variant Summary:
  Total Variants: {sample.total_variants}
  Pathogenic: {sample.pathogenic}
  Likely Pathogenic: {sample.likely_pathogenic}
  VUS: {sample.vus}
  Benign: {sample.benign}

High-Priority Variants:
{variant_lines}

Generated: {datetime.now().isoformat()}
"""
        else:
            report_content = f"""GENOME ANALYSIS REPORT
Sample ID: {sample_id}
Generated: {datetime.now().isoformat()}

No stored analysis data was found for this sample.
"""

        response = HttpResponse(report_content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{sample_id}_report.txt"'
        return response

    except Exception as e:
        logger.error(f"PDF export error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def export_excel_report(request):
    """Export analysis data as Excel workbook"""
    try:
        data = json.loads(request.body)
        sample_id = data.get('sample_id', 'unknown')
        export_data = data.get('data', {})
        
        # Generate CSV content (in production, use openpyxl for real Excel files)
        csv_content = generate_csv_from_data(export_data)
        
        from django.http import HttpResponse
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{sample_id}_data.csv"'
        return response
        
    except Exception as e:
        logger.error(f"Excel export error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def export_csv_report(request):
    """Export analysis data as CSV"""
    try:
        data = json.loads(request.body)
        sample_id = data.get('sample_id', 'unknown')
        export_data = data.get('data', {})
        
        csv_content = generate_csv_from_data(export_data)
        
        from django.http import HttpResponse
        response = HttpResponse(csv_content, content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{sample_id}_variants.csv"'
        return response
        
    except Exception as e:
        logger.error(f"CSV export error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def export_vcf_report(request):
    """Export analysis data as VCF file"""
    try:
        data = json.loads(request.body)
        sample_id = data.get('sample_id', 'unknown')
        export_data = data.get('data', {})
        
        vcf_content = generate_vcf_from_data(export_data)
        
        from django.http import HttpResponse
        response = HttpResponse(vcf_content, content_type='text/plain')
        response['Content-Disposition'] = f'attachment; filename="{sample_id}_variants.vcf"'
        return response
        
    except Exception as e:
        logger.error(f"VCF export error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def export_json_report(request):
    """Export analysis data as JSON"""
    try:
        data = json.loads(request.body)
        sample_id = data.get('sample_id', 'unknown')
        export_data = data.get('data', {})
        
        from django.http import HttpResponse
        import json as json_lib
        
        json_content = json_lib.dumps(export_data, indent=2)
        
        response = HttpResponse(json_content, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{sample_id}_analysis.json"'
        return response
        
    except Exception as e:
        logger.error(f"JSON export error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def generate_csv_from_data(data):
    """Generate CSV content from analysis data"""
    csv_lines = []
    
    if 'variants' in data and data['variants']:
        csv_lines.append('Chromosome,Position,Ref,Alt,Gene,Impact,Clinical_Significance,Quality,Coverage,dbSNP_ID')
        for variant in data['variants']:
            csv_lines.append(f"{variant.get('chromosome', '')},{variant.get('position', '')},{variant.get('ref', '')},{variant.get('alt', '')},{variant.get('gene', '')},{variant.get('impact', '')},{variant.get('clinical_significance', '')},{variant.get('quality', '')},{variant.get('coverage', '')},{variant.get('dbsnp_id', '')}")
    
    return '\n'.join(csv_lines)


def generate_vcf_from_data(data):
    """Generate VCF content from analysis data"""
    vcf_lines = [
        '##fileformat=VCFv4.2',
        f'##fileDate={datetime.now().strftime("%Y%m%d")}',
        '##source=GenomeAnalysisExport',
        '#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO'
    ]
    
    if 'variants' in data and data['variants']:
        for variant in data['variants']:
            chrom = str(variant.get('chromosome', '')).replace('chr', '')
            pos = str(variant.get('position', ''))
            id_col = variant.get('dbsnp_id', '.')
            ref = variant.get('ref', '')
            alt = variant.get('alt', '')
            qual = str(variant.get('quality', ''))
            filter_col = 'PASS'
            info = f"GENE={variant.get('gene', '')};IMPACT={variant.get('impact', '')}"
            
            vcf_lines.append(f"{chrom}\t{pos}\t{id_col}\t{ref}\t{alt}\t{qual}\t{filter_col}\t{info}")
    
    return '\n'.join(vcf_lines)
