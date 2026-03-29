# user/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from laundryadmin.auth import CookieJWTAuthentication

from .models import Order, Payment
from .serializers import (
    CustomerRegisterSerializer,
    OrderSerializer,
    CreateOrderSerializer,
    PaymentSerializer,
    CustomerOrderTrackSerializer,
)


# ─────────────────────────────────────────────
# CUSTOMER AUTH
# ─────────────────────────────────────────────

class CustomerRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Account created successfully'},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomerLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response(
                {'message': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response(
                {'message': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Block staff/admin from logging in through customer endpoint
        if user.is_staff or user.is_superuser:
            return Response(
                {'message': 'Please use the admin login'},
                status=status.HTTP_403_FORBIDDEN
            )

        refresh      = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        response = Response(
            {'message': 'Login successful'},
            status=status.HTTP_200_OK
        )
        response.set_cookie(
            key='access_token', value=access_token,
            httponly=True, secure=True, samesite='Lax', max_age=60 * 5
        )
        response.set_cookie(
            key='refresh_token', value=refresh_token,
            httponly=True, secure=True, samesite='Lax', max_age=60 * 60 * 24
        )
        return response


class CustomerAuthSessionView(APIView):
    """Returns logged in customer details — React calls this on app load"""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'id':         user.id,
            'username':   user.username,
            'full_name':  user.get_full_name(),
            'email':      user.email,
        }, status=status.HTTP_200_OK)


class CustomerTokenRefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {'message': 'Refresh token missing'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        try:
            refresh          = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)
        except TokenError:
            return Response(
                {'message': 'Invalid or expired refresh token, please login again'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        response = Response({'message': 'Token refreshed'}, status=status.HTTP_200_OK)
        response.set_cookie(
            key='access_token', value=new_access_token,
            httponly=True, secure=True, samesite='Lax', max_age=60 * 5
        )
        return response


class CustomerLogoutView(APIView):
    def post(self, request):
        response = Response(
            {'message': 'Logged out successfully'},
            status=status.HTTP_200_OK
        )
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response


# ─────────────────────────────────────────────
# CUSTOMER — PLACE ORDER
# ─────────────────────────────────────────────

class CustomerOrderCreateView(APIView):
    """Logged in customer places their own order"""
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated]

    def post(self, request):
        serializer = CreateOrderSerializer(data=request.data)
        if serializer.is_valid():
            order = serializer.save(
                customer         = request.user,   # link order to logged in customer
                created_by_staff = False,
            )
            return Response({
                'message':    'Order placed successfully',
                'invoice_id': order.invoice_id,
                'total':      order.total,
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ─────────────────────────────────────────────
# CUSTOMER — ORDER TRACKING (no login needed)
# ─────────────────────────────────────────────

class CustomerOrderTrackView(APIView):
    """
    Anyone can track an order using just the invoice ID.
    No account or login required.
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
            order = serializer.save(
                customer         = None,   # no user account needed
                created_by_staff = True,
            )
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
# STAFF — RECORD PAYMENT
# ─────────────────────────────────────────────

class StaffRecordPaymentView(APIView):
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

        serializer = PaymentSerializer(data={**request.data, 'order': order.id})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Payment recorded', 'data': serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)