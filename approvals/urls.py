from django.urls import path, include
from . import views

# API URLs
api_urlpatterns = [
    path('list/', views.approval_list_api_view, name='approval-list-html'),
    path('stats/', views.approval_statistics_view, name='approval-stats'),
    path('<int:approval_id>/approve/', views.approve_request_view, name='approve-request'),
    path('<int:approval_id>/reject/', views.reject_request_view, name='reject-request'),
    path('<int:approval_id>/comment/', views.add_comment_view, name='add-approval-comment'),
    path('request/device-assignment/', views.request_device_assignment_view, name='request-device-assignment'),
]

# Frontend URLs
urlpatterns = [
    path('', views.approvals_view, name='approvals'),
    path('<int:approval_id>/', views.approval_detail_view, name='approval-detail'),
    path('api/', include(api_urlpatterns)),
]