from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# API URLs
api_urlpatterns = [
    path('users/', views.user_list_api_view, name='user-list-html'),
    path('users/json/', views.UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='toggle-user-status'),
    path('audit-logs/', views.AuditLogListView.as_view(), name='audit-log-list'),
    path('settings/', views.SystemSettingsListView.as_view(), name='settings-list'),
    path('settings/<int:pk>/', views.SystemSettingsDetailView.as_view(), name='settings-detail'),
    path('auth/login/', views.login_view, name='api-login'),
    path('auth/logout/', views.logout_view, name='api-logout'),
    path('auth/me/', views.current_user_view, name='current-user'),
    path('dashboard/stats/', views.dashboard_stats_view, name='dashboard-stats'),
    path('dashboard/activity/', views.dashboard_activity_view, name='dashboard-activity'),
    path('dashboard/search/', views.dashboard_search_view, name='dashboard-search'),
    path('reports/summary/', views.reports_summary_view, name='reports-summary'),
    path('reports/charts/', views.reports_charts_view, name='reports-charts'),
    path('reports/top-users/', views.reports_top_users_view, name='reports-top-users'),
    path('reports/generate/<str:report_type>/', views.reports_generate_view, name='reports-generate'),
]

# Frontend URLs
urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_page_view, name='login'),
    path('users/', views.users_view, name='users'),
    path('users/<int:user_id>/', views.user_detail_view, name='user-detail-page'),
    path('users/<int:user_id>/edit/', views.user_edit_view, name='user-edit-page'),
    path('reports/', views.reports_view, name='reports'),
    path('settings/', views.settings_view, name='settings'),
    path('api/', include(api_urlpatterns)),
]