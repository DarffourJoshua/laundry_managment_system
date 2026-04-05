# user/serializers.py

from rest_framework import serializers
from .models import Order, OrderItem, Payment
from laundryadmin.models import Service


class OrderItemSerializer(serializers.ModelSerializer):
    service_name = serializers.CharField(source='service.name', read_only=True)
    subtotal     = serializers.SerializerMethodField()

    class Meta:
        model  = OrderItem
        fields = ['id', 'service', 'service_name', 'quantity', 'price', 'subtotal']

    def get_subtotal(self, obj):
        return obj.subtotal()


class CreateOrderSerializer(serializers.Serializer):
    """
    Customer submits their order — no auth needed.
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
        items_data = validated_data.pop('items')

        order = Order.objects.create(**validated_data)

        for item in items_data:
            OrderItem.objects.create(
                order    = order,
                service  = item['service'],
                quantity = item['quantity'],
                price    = item['service'].price,  # snapshot price at time of order
            )

        order.calculate_total()
        return order


class RecordPaymentSerializer(serializers.Serializer):
    """
    Customer submits payment details after placing order.
    transaction_id is required for MOMO and CARD, optional for CASH.
    """
    method         = serializers.ChoiceField(choices=Payment.Method.choices)
    amount         = serializers.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = serializers.CharField(required=False, allow_blank=True)
    notes          = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        method         = data.get('method')
        transaction_id = data.get('transaction_id', '')

        # transaction_id is required for MOMO and CARD payments
        if method in [Payment.Method.MOMO, Payment.Method.CARD] and not transaction_id:
            raise serializers.ValidationError(
                {'transaction_id': 'Transaction ID or Momo reference is required for MOMO and CARD payments'}
            )
        return data

    def create(self, validated_data):
        order = self.context['order']

        return Payment.objects.create(
            order          = order,
            method         = validated_data['method'],
            amount         = validated_data['amount'],
            transaction_id = validated_data.get('transaction_id', ''),
            notes          = validated_data.get('notes', ''),
        )


class OrderSerializer(serializers.ModelSerializer):
    """Full order serializer — used by staff and admin"""
    items   = OrderItemSerializer(many=True, read_only=True)
    payment = serializers.SerializerMethodField()

    class Meta:
        model  = Order
        fields = [
            'id', 'invoice_id', 'customer_name', 'telephone',
            'status', 'items', 'total', 'notes', 'payment',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'invoice_id', 'total', 'created_at', 'updated_at']

    def get_payment(self, obj):
        if hasattr(obj, 'payment'):
            return {
                'method':         obj.payment.method,
                'amount':         obj.payment.amount,
                'transaction_id': obj.payment.transaction_id,
            }
        return None


class CustomerOrderTrackSerializer(serializers.ModelSerializer):
    """Lean serializer — only what the customer needs to see"""
    items           = OrderItemSerializer(many=True, read_only=True)
    payment_status  = serializers.SerializerMethodField()

    class Meta:
        model  = Order
        fields = [
            'invoice_id', 'customer_name', 'status',
            'items', 'total', 'payment_status', 'created_at'
        ]

    def get_payment_status(self, obj):
        return 'PAID' if hasattr(obj, 'payment') else 'UNPAID'