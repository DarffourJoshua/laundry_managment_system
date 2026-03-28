# laundryadmin/urls.py

from django.urls import path
from .views import (
    AdminLoginView,
    StaffListCreateView,
    StaffDetailView,
    ServiceListCreateView,
    ServiceDetailView,
    AdminOrderListView,
    CompanySettingsView,
    AdminLogoutView,
    AdminTokenRefreshView,
    AdminAuthSessionView
)

urlpatterns = [
    # Auth
    path('login/',                  AdminLoginView.as_view(),          name='admin-login'),

    # Staff management
    path('staff/',                  StaffListCreateView.as_view(),     name='staff-list-create'),
    path('staff/<int:pk>/',         StaffDetailView.as_view(),         name='staff-detail'),

    # Service management
    path('services/',               ServiceListCreateView.as_view(),   name='service-list-create'),
    path('services/<int:pk>/',      ServiceDetailView.as_view(),       name='service-detail'),

    # Orders (read-only)
    path('orders/',                 AdminOrderListView.as_view(),      name='admin-order-list'),

    # Company settings
    path('settings/',               CompanySettingsView.as_view(),     name='company-settings'),

    path('logout/', AdminLogoutView.as_view(), name='admin-logout'),

    path('token/refresh/', AdminTokenRefreshView.as_view(), name='admin-token-refresh'),

    # laundryadmin/urls.py
    path('auth/session/', AdminAuthSessionView.as_view(), name='admin-auth-session'),
]