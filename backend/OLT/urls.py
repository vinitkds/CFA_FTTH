from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OLTViewSet, OLTInfraChargesViewSet

router = DefaultRouter()

router.register(r'networkelement', OLTViewSet, basename='networkelement') 
router.register(r'infracharges', OLTInfraChargesViewSet, basename='infracharges') 

urlpatterns = [
    # This correctly structures your endpoints under the /api/ prefix
    path('', include(router.urls)) 
]


# With this configuration, your React frontend can now reliably interact with the following endpoints:
# • GET /api/OLT/ (List all OLTs)
# • POST /api/OLT/ (Create a new OLT)
# • GET /api/OLT/<id>/ (Get a single OLT detail)
# • PUT /api/OLT/<id>/ (Update an OLT)
# • DELETE /api/OLT/<id>/ (Delete an OLT)
