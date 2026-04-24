from django.db import transaction
from django.db.models import Sum
from django.core.exceptions import ValidationError
from .models import Payout, LedgerEntry
from merchants.models import Merchant

class PayoutService:
    @staticmethod
    def get_balances(merchant_id):
        """
        Available balance = SUM(credits) - SUM(payout_hold + payout_debit)
        Actually, since payout_hold and payout_debit are negative in our ledger, 
        it's simpler: Sum of all ledger entries.
        
        Wait, requirement says:
        Available balance = SUM(credits) - SUM(payout_hold + payout_debit)
        Held balance = SUM(payout_hold where payout not completed/failed)
        """
        
        # Total balance (all credits - all debits/holds)
        total_balance = LedgerEntry.objects.filter(merchant_id=merchant_id).aggregate(
            total=Sum('amount_paise')
        )['total'] or 0
        
        # Held balance: Sum of payout_hold entries where the associated payout is NOT completed or failed
        # This is a bit tricky since reference_id is just an int.
        # Let's refine the query.
        
        held_balance = LedgerEntry.objects.filter(
            merchant_id=merchant_id,
            type='payout_hold'
        ).exclude(
            reference_id__in=Payout.objects.filter(
                merchant_id=merchant_id,
                status__in=['completed', 'failed']
            ).values_list('id', flat=True)
        ).aggregate(held=Sum('amount_paise'))['held'] or 0
        
        # Since payout_hold is negative, held balance should be shown as positive to user? 
        # Usually held is absolute. But let's follow the requirement logic.
        # Held balance = SUM(payout_hold)
        
        return {
            "available_balance": total_balance,
            "held_balance": abs(held_balance)
        }

    @staticmethod
    def create_payout(merchant_id, amount_paise, idempotency_key):
        # 1. Start DB transaction
        with transaction.atomic():
            # 2. Lock merchant row
            merchant = Merchant.objects.select_for_update().get(id=merchant_id)
            
            # 3. Check idempotency
            existing_payout = Payout.objects.filter(
                merchant=merchant, 
                idempotency_key=idempotency_key
            ).first()
            
            if existing_payout:
                return existing_payout, False # Already exists
            
            # 4. Calculate balance
            balances = PayoutService.get_balances(merchant_id)
            if balances['available_balance'] < amount_paise:
                raise ValidationError("Insufficient funds")
            
            # 5. Create payout
            payout = Payout.objects.create(
                merchant=merchant,
                amount_paise=amount_paise,
                idempotency_key=idempotency_key,
                status='pending'
            )
            
            # 6. Create ledger entry (payout_hold = negative amount)
            LedgerEntry.objects.create(
                merchant=merchant,
                amount_paise=-amount_paise,
                type='payout_hold',
                reference_id=payout.id
            )
            
            return payout, True
