

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import CompanySettings, Service


class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['id', 'name', 'price', 'color', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

class CompanySettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = CompanySettings
        fields = ['company_name', 'company_email', 'logo', 'fav_icon', 'phone', 'address']


class StaffSerializer(serializers.ModelSerializer):
    """
    Used by admin to create and manage staff accounts.
    password is write-only — never returned in responses.
    """
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model  = User
        fields = ['id', 'username', 'password', 'is_active', 'telephone']
        read_only_fields = ['id']

    def create(self, validated_data):
        # Use create_user so password gets hashed properly
        user = User.objects.create_user(
            username   = validated_data['username'],
            password   = validated_data['password'],
            telephone = validated_data.get('telephone', ''),
            is_staff   = True,   # marks them as staff, not superuser
            # full_name = validated_data.get('full_name', ''),
            # first_name = validated_data.get('first_name', ''),
            # last_name = validated_data.get('last_name', ''),
            # email      = validated_data.get('email', ''),
        )
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)  # hash the new password
        instance.save()
        return instance