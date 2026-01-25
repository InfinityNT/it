from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API URLs
api_urlpatterns = [
    path('devices/', views.device_list_api_view, name='device-list-html'),
    path('devices/json/', views.DeviceListCreateView.as_view(), name='device-list-create'),
    path('advanced-search/', views.advanced_search_api, name='advanced-search-api'),
    path('bulk-operations/', views.bulk_operations_view, name='bulk-operations'),
    path('devices/<int:pk>/', views.DeviceDetailView.as_view(), name='device-detail'),
    path('devices/<int:device_id>/assign/', views.assign_device_view, name='device-assign'),
    path('devices/<int:device_id>/unassign/', views.unassign_device_view, name='device-unassign'),
    path('categories/', views.DeviceCategoryListView.as_view(), name='device-category-list'),
    path('manufacturers/', views.DeviceManufacturerListView.as_view(), name='device-manufacturer-list'),
    path('vendors/', views.DeviceVendorListView.as_view(), name='device-vendor-list'),
    path('models/', views.DeviceModelListView.as_view(), name='device-model-list'),
    path('models/<int:model_id>/', views.device_model_detail_api, name='device-model-detail'),
]

# Frontend URLs
urlpatterns = [
    path('', views.devices_view, name='devices'),
    path('search/', views.advanced_search_view, name='advanced-search'),
    path('add/', views.add_device_view, name='add-device'),
    path('models/add/', views.add_device_model_modal_view, name='add-device-model'),
    path('models/spec-template/', views.get_spec_template_view, name='get-spec-template'),
    path('<int:device_id>/', views.device_detail_view, name='device-detail-page'),
    path('<int:device_id>/history/', views.device_history_view, name='device-history'),
    path('<int:device_id>/edit/', views.edit_device_view, name='edit-device'),
    path('api/', include(api_urlpatterns)),
]