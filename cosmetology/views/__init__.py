# Views package for cosmetology module
# Import all views from the main views.py file

from cosmetology.views import (
    CosmetologyClientViewSet, CosmetologyServiceViewSet, CosmetologyProductViewSet,
    CosmetologyAppointmentViewSet, CosmetologyTreatmentPlanViewSet, 
    CosmetologyConsultationViewSet, CosmetologyProgressViewSet,
    CosmetologyDashboardStatsView, CosmetologyAppointmentCalendarView,
    # Cosmetic Gynecology Views
    CosmeticGynecologyClientViewSet, CosmeticGynecologyTreatmentViewSet,
    CosmeticGynecologyConsultationViewSet, CosmeticGynecologyTreatmentPlanViewSet,
    CosmeticGynecologyProgressViewSet, CosmeticGynecologyDashboardStatsView
)
