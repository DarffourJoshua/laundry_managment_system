# user/urls.py

from django.urls import path
from .views import (
    CustomerRegisterView,
    CustomerLoginView,
    CustomerAuthSessionView,
    CustomerTokenRefreshView,
    CustomerLogoutView,
    CustomerOrderCreateView,
    CustomerOrderTrackView,
    StaffOrderListCreateView,
    StaffOrderDetailView,
    StaffRecordPaymentView,
)

urlpatterns = [

    # Customer auth
    path('register/',               CustomerRegisterView.as_view(),     name='customer-register'),
    path('login/',                  CustomerLoginView.as_view(),         name='customer-login'),
    path('auth/session/',           CustomerAuthSessionView.as_view(),   name='customer-session'),
    path('token/refresh/',          CustomerTokenRefreshView.as_view(),  name='customer-token-refresh'),
    path('logout/',                 CustomerLogoutView.as_view(),        name='customer-logout'),

    # Customer order
    path('orders/',                 CustomerOrderCreateView.as_view(),   name='customer-order-create'),

    # Order tracking — no login needed
    path('track/<str:invoice_id>/', CustomerOrderTrackView.as_view(),    name='customer-order-track'),

    # Staff order management
    path('staff/orders/',                        StaffOrderListCreateView.as_view(), name='staff-order-list-create'),
    path('staff/orders/<str:invoice_id>/',       StaffOrderDetailView.as_view(),     name='staff-order-detail'),
    path('staff/orders/<str:invoice_id>/pay/',   StaffRecordPaymentView.as_view(),   name='staff-order-payment'),
]