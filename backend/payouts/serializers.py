from rest_framework import serializers
from .models import Payout, LedgerEntry

class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = ['id', 'merchant', 'amount_paise', 'status', 'idempotency_key', 'created_at', 'updated_at']
        read_only_fields = ['status', 'created_at', 'updated_at']

class PayoutCreateSerializer(serializers.Serializer):
    merchant_id = serializers.IntegerField()
    amount_paise = serializers.IntegerField(min_value=1)
    bank_account_id = serializers.CharField(required=False)

class BalanceSerializer(serializers.Serializer):
    available_balance = serializers.IntegerField()
    held_balance = serializers.IntegerField()
