from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API URLs
api_urlpatterns = [
    path('employees/', views.EmployeeListAPIView.as_view(), name='employee-list-api'),
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

    # Department management
    path('departments/manage/', views.manage_departments_view, name='manage-departments'),
    path('departments/manage/list/', views.manage_departments_list_view, name='manage-departments-list'),
    path('departments/manage/add-form/', views.manage_departments_add_form_view, name='manage-departments-add-form'),
    path('departments/manage/<int:department_id>/edit/', views.manage_departments_edit_view, name='manage-departments-edit'),
    path('departments/manage/<int:department_id>/delete/', views.manage_departments_delete_view, name='manage-departments-delete'),

    # Job title management
    path('job-titles/manage/', views.manage_job_titles_view, name='manage-job-titles'),
    path('job-titles/manage/list/', views.manage_job_titles_list_view, name='manage-job-titles-list'),
    path('job-titles/manage/add-form/', views.manage_job_titles_add_form_view, name='manage-job-titles-add-form'),
    path('job-titles/manage/<int:job_title_id>/edit/', views.manage_job_titles_edit_view, name='manage-job-titles-edit'),
    path('job-titles/manage/<int:job_title_id>/delete/', views.manage_job_titles_delete_view, name='manage-job-titles-delete'),

    path('<int:employee_id>/', views.employee_detail_view, name='employee-detail'),
    path('<int:employee_id>/edit/', views.employee_edit_view, name='employee-edit'),
]