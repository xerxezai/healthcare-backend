from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import Patient

User = get_user_model()


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_all_patients(request):
    """Delete all dermatology patients and their associated user accounts"""
    
    # Check if user has permission (should be admin/superuser)
    if not (request.user.is_superuser or request.user.is_staff):
        return Response(
            {'error': 'Permission denied. Only admin users can delete all patients.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    try:
        with transaction.atomic():
            # Get all dermatology patients
            patients = Patient.objects.all()
            patient_count = patients.count()
            
            # Get associated users
            user_ids = list(patients.values_list('user_id', flat=True))
            
            # Delete patients (this will cascade to related records)
            patients.delete()
            
            # Delete associated user accounts (only those that were dermatology patients)
            deleted_users = User.objects.filter(id__in=user_ids).delete()
            
            return Response({
                'message': f'Successfully deleted {patient_count} dermatology patients and {deleted_users[0]} user accounts.',
                'deleted_patients': patient_count,
                'deleted_users': deleted_users[0]
            }, status=status.HTTP_200_OK)
                
    except Exception as e:
        return Response(
            {'error': f'Error deleting patients: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
