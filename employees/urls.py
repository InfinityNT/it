from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API URLs
api_urlpatterns = [
    path('employees/', views.EmployeeListAPIView.as_view(), name='employee-list-api'),
    path('bulk-operations/', views.employee_bulk_operations_view, name='employee-bulk-operations'),
    path('departments/', views.department_list_api, name='department-list-api'),
    path('job-titles/', views.job_title_list_api, name='job-title-list-api'),
    path('import/', views.import_employees_view, name='employee-import-api'),
    path('import/template/', views.download_employee_template_view, name='employee-import-template'),
]

# Frontend URLs
urlpatterns = [
    path('api/', include(api_urlpatterns)),
    path('', views.employees_view, name='employees'),
    path('add/', views.add_employee_view, name='add-employee'),
    path('import/modal/', views.import_employees_modal_view, name='import-employees-modal'),
    path('<int:employee_id>/', views.employee_detail_view, name='employee-detail'),
    path('<int:employee_id>/edit/', views.employee_edit_view, name='employee-edit'),
]