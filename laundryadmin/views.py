from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from laundryadmin.auth import CookieJWTAuthentication

from .models import CompanySettings, Service
from .serializers import CompanySettingsSerializer, ServiceSerializer, StaffSerializer
from user.models import Order
from user.serializers import OrderSerializer


# ---------------
# AUTH
# ---------------

class AdminLoginView(APIView):
    """
    Only supersusers or staff can log in through this endpoint.
    """

    permission_classes = []
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username and password:
            return Response(
                {'message': 'Username and password are rerquired'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response(
                {'message': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not (user.is_superuser or user.is_staff):
            return Response(
                {'message', 'You are not authorized to access this panel'},
                status=status.HTTP_403_FORBIDDEN
            )

        response =  Response(
            {'message': 'Login Successful'},
            status=status.HTTP_200_OK
        )

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        # Store tokens in HttpOnly cookies — not accessible via JavaScript
        response.set_cookie(
            key      = 'access_token',
            value    = access_token,
            httponly = True,       # blocks JS access — protects against XSS
            secure   = True,       # only sent over HTTPS
            samesite = 'Lax',      # protects against CSRF
            max_age  = 60 * 5,     # 5 minutes — matches simplejwt access token lifetime
        )
        response.set_cookie(
            key      = 'refresh_token',
            value    = refresh_token,
            httponly = True,
            secure   = True,
            samesite = 'Lax',
            max_age  = 60 * 60 * 24,  # 24 hours — matches simplejwt refresh token lifetime
        )

        return response


class AdminTokenRefreshView(APIView):
    
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')

        if not refresh_token:
            return Response(
                {'message': 'Refresh token missing'},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            refresh = RefreshToken(refresh_token)
            new_access_token = str(refresh.access_token)

        except:
            return Response(
                {'message': 'Invalid or expired refresh token, please login again'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        response = Response(
            {'message': 'Token refreshed'},
            status=status.HTTP_200_OK
        )
        response.set_cookie(
            key      = 'access_token',
            value    = new_access_token,
            httponly = True,
            secure   = True,
            samesite = 'Lax',
            max_age  = 60 * 5,
        )
        return response

class AdminAuthSessionView(APIView):
    """
    Returns the currently authenticated admin/staff user details.
    React calls this on app load to check if the session is still valid.
    If the cookie is missing or expired, returns 401.
    """
    authentication_classes = [CookieJWTAuthentication]
    permission_classes     = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        user = request.user
        return Response({
            'id':           user.id,
            'username':     user.username,
            'full_name':    user.get_full_name(),
            # 'email':        user.email,
            'is_superuser': user.is_superuser,
            'is_staff':     user.is_staff,
        }, status=status.HTTP_200_OK)

class AdminLogoutView(APIView):
    def post(self, request):
        response = Response(
            {'message': 'Logged out successfully'},
            status=status.HTTP_200_OK
        )
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response

# ─────────────────────────────────────────────
# STAFF MANAGEMENT  (superuser only)
# ─────────────────────────────────────────────

class StaffListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """List all staff accounts"""
        staff = User.objects.filter(is_staff=True, is_superuser=False)
        serializer = StaffSerializer(staff, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new staff account"""
        serializer = StaffSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Staff account created successfully', 'data': serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_object(self, pk):
        try:
            return User.objects.get(pk=pk, is_staff=True, is_superuser=False)
        except User.DoesNotExist:
            return None

    def get(self, request, pk):
        """Get a single staff account"""
        staff = self.get_object(pk)
        if not staff:
            return Response(
                {'message': 'Staff not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = StaffSerializer(staff)
        return Response(serializer.data)

    def patch(self, request, pk):
        """Update a staff account (partial update)"""
        staff = self.get_object(pk)
        if not staff:
            return Response(
                {'message': 'Staff not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = StaffSerializer(staff, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Staff updated', 'data': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Deactivate a staff account — never hard delete"""
        staff = self.get_object(pk)
        if not staff:
            return Response({'message': 'Staff not found'}, status=status.HTTP_404_NOT_FOUND)
        staff.is_active = False
        staff.save()
        return Response({'message': 'Staff account deactivated'}, status=status.HTTP_200_OK)


# ─────────────────────────────────────────────
# SERVICE MANAGEMENT
# ─────────────────────────────────────────────

class ServiceListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """List all services"""
        services = Service.objects.all().order_by('-created_at')
        serializer = ServiceSerializer(services, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """Create a new service"""
        serializer = ServiceSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Service created', 'data': serializer.data},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class ServiceDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_object(self, pk):
        try:
            return Service.objects.get(pk=pk)
        except Service.DoesNotExist:
            return None

    def patch(self, request, pk):
        """Partially update a service e.g. change price or toggle active"""
        service = self.get_object(pk)
        if not service:
            return Response({'message': 'Service not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ServiceSerializer(service, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Service updated', 'data': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """Soft delete — just deactivate the service"""
        service = self.get_object(pk)
        if not service:
            return Response({'message': 'Service not found'}, status=status.HTTP_404_NOT_FOUND)
        service.is_active = False
        service.save()
        return Response({'message': 'Service deactivated'}, status=status.HTTP_200_OK)


class AdminDashboardView(APIView):
    authentication_classes=[CookieJWTAuthentication]
    permission_classes=[IsAuthenticated, IsAdminUser]

    def get(self, request):
        total_services = Service.objects.count()
        active_services = Service.objects.filter(is_active=True).count()
        inactive_services = Service.objects.filter(is_active=False).count()


        total_staffs = User.objects.filter(is_staff=True, is_superuser=False).count()
        active_staffs = User.objects.filter(is_staff=True, is_superuser=False,is_active=True).count()
        inactive_staffs = User.objects.filter(is_staff=True, is_superuser=False,is_active=False).count()

        return Response({
            'services': {
                'total':    total_services,
                'active':   active_services,
                'inactive': inactive_services,
            },
            'staffs': {
                'total':    total_staffs,
                'active':   active_staffs,
                'inactive': inactive_staffs,
            }
        }, status=status.HTTP_200_OK)

# ─────────────────────────────────────────────
# ORDER VIEWING  (read-only for admin)
# ─────────────────────────────────────────────

class AdminOrderListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        """
        List all customer orders.
        Supports ?status=pending filtering.
        """
        orders = Order.objects.all().order_by('-created_at')

        order_status = request.query_params.get('status')
        if order_status:
            orders = orders.filter(status=order_status)

        # We'll wire up OrderSerializer once the user/order model is finalized
        # services = Service.objects.all().order_by('-created_at')
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            {orders},
            status=status.HTTP_200_OK
        )


# ─────────────────────────────────────────────
# COMPANY SETTINGS
# ─────────────────────────────────────────────

class CompanySettingsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        settings = CompanySettings.get()
        serializer = CompanySettingsSerializer(settings)
        return Response(serializer.data)

    def patch(self, request):
        settings = CompanySettings.get()
        serializer = CompanySettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Settings updated', 'data': serializer.data})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)