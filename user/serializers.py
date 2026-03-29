# user/serializers.py

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Order, OrderItem, Payment
from laundryadmin.models import Service


class CustomerRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model  = User
        fields = ['id', 'username', 'full_name']

    def create(self, validated_data):
        user = User.objects.create_user(
            username   = validated_data['username'],
            full_name = validated_data.get('full_name', ''),
            is_staff   = False,
            is_superuser = False,
        )
        return user


class OrderItemSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    subtotal     = serializers.SerializerMethodField()

    class Meta:
        model  = OrderItem
        fields = ['id', 'service', 'service_name', 'quantity', 'price', 'subtotal']

    def get_subtotal(self, obj):
        return obj.subtotal()


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model  = Order
        fields = [
            'id', 'invoice_id', 'customer', 'customer_name', 'telephone',
            'status', 'items', 'total', 'notes', 'created_by_staff',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'invoice_id', 'total', 'created_at', 'updated_at']


class CreateOrderSerializer(serializers.Serializer):
    """
    Shared between customer self-ordering and staff ordering on behalf.
    The view is responsible for setting customer and created_by_staff.
    """
    customer_name = serializers.CharField(max_length=100)
    telephone     = serializers.CharField(max_length=15)
    notes         = serializers.CharField(required=False, allow_blank=True)
    items         = serializers.ListField(
        child=serializers.DictField(),
        min_length=1
    )

    def validate_items(self, items):
        validated = []
        for item in items:
            service_id = item.get('service_id')
            quantity   = item.get('quantity', 1)

            if not service_id:
                raise serializers.ValidationError('Each item must have a service_id')

            try:
                service = Service.objects.get(id=service_id, is_active=True)
            except Service.DoesNotExist:
                raise serializers.ValidationError(f'Service with id {service_id} does not exist or is inactive')

            validated.append({'service': service, 'quantity': int(quantity)})
        return validated

    def create(self, validated_data):
        items_data       = validated_data.pop('items')
        customer         = validated_data.pop('customer', None)
        created_by_staff = validated_data.pop('created_by_staff', False)

        order = Order.objects.create(
            **validated_data,
            customer         = customer,
            created_by_staff = created_by_staff,
        )

        for item in items_data:
            OrderItem.objects.create(
                order    = order,
                service  = item['service'],
                quantity = item['quantity'],
                price    = item['service'].price,  # snapshot price
            )

        order.calculate_total()
        return order


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Payment
        fields = ['id', 'order', 'method', 'amount', 'notes', 'created_at']
        read_only_fields = ['id', 'created_at']


class CustomerOrderTrackSerializer(serializers.ModelSerializer):
    """Lean serializer — only what the customer needs to see"""
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model  = Order
        fields = ['invoice_id', 'customer_name', 'status', 'items', 'total', 'created_at']