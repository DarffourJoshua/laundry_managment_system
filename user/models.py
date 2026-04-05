# user/models.py

from django.db import models
from laundryadmin.models import Service
import random
import string


def generate_invoice_id():
    number = ''.join(random.choices(string.digits, k=4))
    return f'INV-{number}'


class Order(models.Model):

    class Status(models.TextChoices):
        RECEIVED  = 'RECEIVED',  'Received'
        WASHING   = 'WASHING',   'Washing'
        DRYING    = 'DRYING',    'Drying'
        IRONING   = 'IRONING',   'Ironing'
        PICKUP    = 'PICKUP',    'Ready for Pickup'
        COLLECTED = 'COLLECTED', 'Collected'

    invoice_id    = models.CharField(max_length=10, unique=True, default=generate_invoice_id, editable=False)
    customer_name = models.CharField(max_length=100)
    telephone     = models.CharField(max_length=15)
    status        = models.CharField(max_length=20, choices=Status.choices, default=Status.RECEIVED)
    total         = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    notes         = models.TextField(blank=True)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.invoice_id} - {self.customer_name}'

    def calculate_total(self):
        self.total = sum(item.subtotal() for item in self.items.all())
        self.save()


class OrderItem(models.Model):
    order    = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    service  = models.ForeignKey(Service, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
    price    = models.DecimalField(max_digits=10, decimal_places=2)  # price snapshot

    def subtotal(self):
        return self.price * self.quantity

    def __str__(self):
        return f'{self.service.name} x{self.quantity}'


class Payment(models.Model):

    class Method(models.TextChoices):
        CASH = 'CASH', 'Cash'
        MOMO = 'MOMO', 'Mobile Money'
        CARD = 'CARD', 'Card'

    order          = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='payment')
    method         = models.CharField(max_length=10, choices=Method.choices, default=Method.CASH)
    amount         = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_id = models.CharField(max_length=100, blank=True)  # momo reference or card transaction id
    notes          = models.TextField(blank=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Payment for {self.order.invoice_id}'