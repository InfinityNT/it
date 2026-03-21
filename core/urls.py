from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# JSON API URLs - For data exchange only
api_urlpatterns = [
    # User management API (JSON only)
    path('users/', views.UserListCreateView.as_view(), name='api-user-list'),
    path('users/<int:pk>/', views.UserDetailView.as_view(), name='api-user-detail'),
    path('users/<int:user_id>/toggle-status/', views.toggle_user_status, name='api-toggle-user-status'),
    path('users/<int:user_id>/reset-password/', views.reset_user_password, name='api-reset-user-password'),

    # System API (JSON only)
    path('audit-logs/', views.AuditLogListView.as_view(), name='api-audit-logs'),
    path('settings/', views.SystemSettingsListView.as_view(), name='api-settings'),
    path('settings/<int:pk>/', views.SystemSettingsDetailView.as_view(), name='api-settings-detail'),
    
    # Authentication API (JSON only)
    path('auth/login/', views.api_login_view, name='api-login'),
    path('auth/logout/', views.api_logout_view, name='api-logout'),
    path('auth/me/', views.current_user_view, name='api-current-user'),
    
    # Dashboard data API (JSON only)
    path('dashboard/stats/', views.dashboard_stats_view, name='api-dashboard-stats'),
    path('dashboard/activity/', views.dashboard_activity_view, name='api-dashboard-activity'),
    path('dashboard/search/', views.dashboard_search_view, name='api-dashboard-search'),
    path('dashboard/quick-actions/', views.dashboard_quick_actions_view, name='api-dashboard-quick-actions'),
    
    # Quick actions API (JSON only)
    path('quick-actions/', views.quick_actions_api_view, name='api-quick-actions'),
    path('quick-actions/toggle/', views.quick_actions_toggle_api_view, name='api-quick-actions-toggle'),

    # Component view endpoints for SPA
    path('views/dashboard/', views.dashboard_component_view, name='api-view-dashboard'),
    path('views/devices/', views.devices_component_view, name='api-view-devices'),
    path('views/users/', views.users_component_view, name='api-view-users'),

    # User list HTML endpoint for HTMX
    path('users/list/', views.user_list_api_view, name='api-user-list-html'),

    # Global search
    path('global-search/', views.dashboard_search_view, name='api-global-search'),

    # Docs content-only view for SPA
    path('views/docs/', views.docs_content_view, name='api-view-docs'),
]

# HTMX Fragment URLs - For dynamic content updates
htmx_urlpatterns = [
    # Dashboard fragments
    path('dashboard/stats/', views.dashboard_stats_view, name='htmx-dashboard-stats'),
    path('dashboard/activity/', views.dashboard_activity_view, name='htmx-dashboard-activity'),
    
    # Quick actions fragments  
    path('quick-actions/', views.quick_actions_api_view, name='htmx-quick-actions'),
    path('quick-actions/config/', views.quick_actions_config_api_view, name='htmx-quick-actions-config'),
]

# Frontend URLs - Django templates
urlpatterns = [
    # Main pages - only core app pages
    path('', views.dashboard_view, name='dashboard'),
    path('users/', views.users_view, name='users'),
    
    # Settings and profile
    path('settings/', views.settings_view, name='settings'),
    path('settings/save/', views.save_settings_view, name='save-settings'),
    path('settings/backup/', views.run_backup_view, name='run-backup'),
    path('settings/integrity-check/', views.check_data_integrity_view, name='check-integrity'),
    path('profile/', views.profile_settings_view, name='profile'),
    
    # Authentication
    path('login/', views.login_page_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-change/', views.password_change_view, name='password-change'),

    # Session management
    path('api/session/extend/', views.extend_session_view, name='session-extend'),

    # User management modals
    path('users/add/', views.add_user_modal_view, name='add-user-modal'),
    path('users/<int:user_id>/detail/', views.user_detail_view, name='user-detail-modal'),
    path('users/<int:user_id>/edit/', views.user_edit_view, name='edit-user-modal'),
    path('users/<int:user_id>/deactivate-modal/', views.deactivate_user_modal_view, name='deactivate-user-modal'),
    path('users/<int:user_id>/reactivate-modal/', views.reactivate_user_modal_view, name='reactivate-user-modal'),

    # Location management
    path('locations/add/', views.add_location_modal_view, name='add-location'),
    path('locations/manage/', views.manage_locations_view, name='manage-locations'),
    path('locations/manage/list/', views.manage_locations_list_view, name='manage-locations-list'),
    path('locations/manage/add-form/', views.manage_locations_add_form_view, name='manage-locations-add-form'),
    path('locations/manage/<int:location_id>/edit/', views.manage_locations_edit_view, name='manage-locations-edit'),
    path('locations/manage/<int:location_id>/delete/', views.manage_locations_delete_view, name='manage-locations-delete'),

    # Documentation / Help
    path('docs/', views.docs_view, name='docs'),
    path('docs/<path:doc_path>/', views.docs_page_view, name='docs-page'),

    # Include API and HTMX routes
    path('api/', include(api_urlpatterns)),
    path('fragments/', include(htmx_urlpatterns)),
]