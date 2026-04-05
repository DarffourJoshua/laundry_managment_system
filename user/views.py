# user/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from laundryadmin.auth import CookieJWTAuthentication

from .models import Order, Payment
from .serializers import (
    CreateOrderSerializer,
    RecordPaymentSerializer,
    OrderSerializer,
    CustomerOrderTrackSerializer,
)


# ─────────────────────────────────────────────
# CUSTOMER — NO AUTH NEEDED
# ─────────────────────────────────────────────

class CustomerOrderCreateView(APIView):
    """
    Customer places an order online.
    No login required — just name, phone, and selected services.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save()
            return Response({
                'message':    'Order placed successfully. Proceed to payment.',
                'invoice_id': order.invoice_id,
                'total':      order.total,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerRecordPaymentView(APIView):
    """
    Customer submits their payment details after placing the order.
    They provide the invoice ID, payment method, amount and transaction ID.
    After this, the invoice is confirmed and they can use it to track.
    """
    permission_classes = [AllowAny]

    def post(self, request, invoice_id):
        try:
            order = Order.objects.get(invoice_id=invoice_id)
        except Order.DoesNotExist:
            return Response(
                {'message': 'No order found with that invoice ID'},
                status=status.HTTP_404_NOT_FOUND
            )

        if hasattr(order, 'payment'):
            return Response(
                {'message': 'Payment already recorded for this order'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RecordPaymentSerializer(
            data    = request.data,
            context = {'order': order}     # pass order into serializer
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message':    'Payment recorded. Use your invoice ID to track your order.',
                'invoice_id': order.invoice_id,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerOrderTrackView(APIView):
    """
    Customer tracks their order using just their invoice ID.
    No login required.
    """
    permission_classes = [AllowAny]

    def get(self, request, invoice_id):
        try:
            order = Order.objects.get(invoice_id=invoice_id)
        except Order.DoesNotExist:
            return Response(
                {'message': 'No order found with that invoice ID'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = CustomerOrderTrackSerializer(order)
        return Response(serializer.data, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
# STAFF — ORDER MANAGEMENT
# ─────────────────────────────────────────────

class StaffOrderListCreateView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """List all orders — filterable by ?status=WASHING"""
        orders       = Order.objects.all().order_by('-created_at')
        order_status = request.query_params.get('status')
        if order_status:
            orders = orders.filter(status=order_status.upper())
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Staff creates order on behalf of a customer"""
        serializer = CreateOrderSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save()
            return Response({
                'message':    'Order created successfully',
                'invoice_id': order.invoice_id,
                'total':      order.total,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffOrderDetailView(APIView):
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated, IsAdminUser]

    def get_object(self, invoice_id):
        try:
            return Order.objects.get(invoice_id=invoice_id)
        except Order.DoesNotExist:
            return None

    def get(self, request, invoice_id):
        order = self.get_object(invoice_id)
        if not order:
            return Response({'message': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrderSerializer(order)
        return Response(serializer.data)

    def patch(self, request, invoice_id):
        """Update order status e.g RECEIVED → WASHING"""
        order = self.get_object(invoice_id)
        if not order:
            return Response({'message': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = OrderSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Order updated', 'data': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────
# STAFF — RECORD PAYMENT ON BEHALF
# ─────────────────────────────────────────────

class StaffRecordPaymentView(APIView):
    """Staff records payment manually if customer pays in person"""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated, IsAdminUser]

    def post(self, request, invoice_id):
        try:
            order = Order.objects.get(invoice_id=invoice_id)
        except Order.DoesNotExist:
            return Response({'message': 'Order not found'}, status=status.HTTP_404_NOT_FOUND)

        if hasattr(order, 'payment'):
            return Response(
                {'message': 'Payment already recorded for this order'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RecordPaymentSerializer(
            data    = request.data,
            context = {'order': order}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Payment recorded', 'invoice_id': order.invoice_id},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)