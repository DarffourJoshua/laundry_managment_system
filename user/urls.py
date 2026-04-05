# user/urls.py

from django.urls import path
from .views import (
    CustomerOrderCreateView,
    CustomerRecordPaymentView,
    CustomerOrderTrackView,
    StaffOrderListCreateView,
    StaffOrderDetailView,
    StaffRecordPaymentView,
)

urlpatterns = [

    # Customer — no auth needed
    path('orders/',                              CustomerOrderCreateView.as_view(),    name='customer-order-create'),
    path('orders/<str:invoice_id>/pay/',         CustomerRecordPaymentView.as_view(),  name='customer-record-payment'),
    path('track/<str:invoice_id>/',              CustomerOrderTrackView.as_view(),     name='customer-order-track'),

    # Staff — auth required
    path('staff/orders/',                        StaffOrderListCreateView.as_view(),   name='staff-order-list-create'),
    path('staff/orders/<str:invoice_id>/',       StaffOrderDetailView.as_view(),       name='staff-order-detail'),
    path('staff/orders/<str:invoice_id>/pay/',   StaffRecordPaymentView.as_view(),     name='staff-record-payment'),
]