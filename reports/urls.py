from django.urls import path, include
from . import views

app_name = 'reports'

# API URLs
api_urlpatterns = [
    path('summary/', views.reports_summary_view, name='reports-summary'),
    path('charts/', views.reports_charts_view, name='reports-charts'),
    path('top-users/', views.reports_top_users_view, name='reports-top-users'),
    path('generate/<str:report_type>/', views.reports_generate_view, name='reports-generate'),
    path('categories/', views.device_categories_api_view, name='device-categories-api'),

    # Dynamic Report Builder API
    path('schema/', views.report_schema_api_view, name='report-schema'),
    path('suggest-primary/', views.suggest_primary_source_view, name='suggest-primary'),
    path('generate-dynamic/', views.generate_dynamic_report_view, name='generate-dynamic'),

    # Component view for SPA
    path('views/reports/', views.reports_component_view, name='reports-component'),
]

# Frontend URLs
urlpatterns = [
    path('', views.reports_view, name='reports'),
    path('custom/', views.custom_report_form_view, name='custom-report-form'),
    path('custom/modal/', views.custom_report_modal_view, name='custom-report-modal'),
    path('generate-custom/', views.generate_custom_report_view, name='generate-custom-report'),
    path('api/', include(api_urlpatterns)),
]