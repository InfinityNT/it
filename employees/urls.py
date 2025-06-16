from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API URLs will be added here
api_urlpatterns = [
    # Employee API endpoints will be added
]

# Frontend URLs
urlpatterns = [
    path('api/', include(api_urlpatterns)),
]