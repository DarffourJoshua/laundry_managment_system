from datetime import date
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, logout, login as auth_login,
from django.contrib.auth.models
from django.contrib import messages
from .models import *
from user.models import UserReqeuest
from service.model import Services
from staff.model import Staffs
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from django.http import HttpResponse

# Create your views here.

today = date.today()

def is_superuser(user):
    return user.is_superuser


def login(request):
    logout(request)
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if user.is_superuser or user.is_staff:
                auth_login(request, user)
                return HttpResponse("Login successful")
            else:
                messages.error(request, 'You are not authorized to access this page.')
        else:
            messages.error(request, 'Invalid username or password.')

    # return render(request, 'admin/login.html')

def createStaff(request):
    if request.method == 'POST':
        fullName = request.POST.get('fullName')
        userName = request.POST.get('userName')
        password = request.POST.get('password')


    
def home(request):
    def create_service():
        if request.method == 'POST':
            name = request.POST.get('name')
            price = request.POST.get('price')
            color = request.POST.get('color')
            status = request.POST.get('status').default(True)
        return {name, price, color, status}

    def update_service(id):
        if id is None:
            return HttpResponse('No or invalid service id')
        
        service_id = request.POST.get('id')
        exitingService = Services.objects.get(id=id)
        if exitingService is None:
            return HttpResponse('No Service found')
        
        if request.data and request.method == 'PUT':
            exitingService.name = request.PUT.get('name')
            exitingService.price = request.PUT.get('price')
            exitingService.color = request.PUT.get('color')
    
    def delete_service(id):
        if id is None:
            return HttpResponse('No or invalid service id')
        
        Service.objects.delete(id=id)

        return HttpResponse('Service deleted successfully')

    def getAllServices():
        return Services.objects.all().list()

    total_services = Services.objects.all().count()
    active_services = Services.objects.filter(status='active').count()
    total_staffs = Staffs.objects.all().count()
    disable_services = Services.objects.filter(status='disable').count()