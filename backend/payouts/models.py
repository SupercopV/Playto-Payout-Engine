from django.db import models
from django.core.validators import MinValueValidator

class Payout(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    merchant = models.ForeignKey('merchants.Merchant', on_delete=models.CASCADE, related_name='payouts')
    amount_paise = models.BigIntegerField(validators=[MinValueValidator(1)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    idempotency_key = models.CharField(max_length=255)
    attempt_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('merchant', 'idempotency_key')
        indexes = [
            models.Index(fields=['merchant', 'idempotency_key']),
        ]

    def __str__(self):
        return f"Payout {self.id} - {self.merchant.name} - {self.amount_paise} paise"

class LedgerEntry(models.Model):
    TYPE_CHOICES = [
        ('credit', 'Credit'),
        ('payout_hold', 'Payout Hold'),
        ('payout_debit', 'Payout Debit'),
        ('refund', 'Refund'),
    ]

    merchant = models.ForeignKey('merchants.Merchant', on_delete=models.CASCADE, related_name='ledger_entries')
    amount_paise = models.BigIntegerField()  # Signed: +credit, -debit
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    reference_id = models.IntegerField(null=True, blank=True)  # Payout ID
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ledger {self.id} - {self.type} - {self.amount_paise} paise"
