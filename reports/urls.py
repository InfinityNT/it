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
]

# Frontend URLs
urlpatterns = [
    path('', views.reports_view, name='reports'),
    path('custom/', views.custom_report_form_view, name='custom-report-form'),
    path('generate-custom/', views.generate_custom_report_view, name='generate-custom-report'),
    path('api/', include(api_urlpatterns)),
]