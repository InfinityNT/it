from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API URLs
api_urlpatterns = [
    path('assignments/', views.assignment_list_api_view, name='assignment-list-html'),
    path('assignments/json/', views.AssignmentListView.as_view(), name='assignment-list-json'),
    path('assignments/statistics/', views.assignment_statistics_view, name='assignment-statistics'),
    path('assignments/<int:pk>/', views.AssignmentDetailView.as_view(), name='assignment-detail-api'),
    path('return-device/<int:device_id>/', views.return_device_view, name='return-device-api'),
    path('return-device-modal/<int:device_id>/', views.return_device_modal_view, name='return-device-modal'),
]

# Frontend URLs
urlpatterns = [
    path('', views.assignments_view, name='assignments'),
    path('<int:assignment_id>/', views.assignment_detail_view, name='assignment-detail-page'),
    path('api/', include(api_urlpatterns)),
]