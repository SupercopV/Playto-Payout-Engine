import random
from celery import shared_task
from django.db import transaction
from django.utils import timezone
from .models import Payout, LedgerEntry
from datetime import timedelta

@shared_task
def process_pending_payouts():
    """
    Pick payouts with status = pending and move to processing
    """
    payouts = Payout.objects.filter(status='pending')
    for payout in payouts:
        execute_payout_simulation.delay(payout.id)

@shared_task
def execute_payout_simulation(payout_id):
    with transaction.atomic():
        try:
            payout = Payout.objects.select_for_update().get(id=payout_id)
        except Payout.DoesNotExist:
            return

        if payout.status != 'pending':
            return

        # Move to processing
        payout.status = 'processing'
        payout.attempt_count += 1
        payout.save()

        # Simulate result
        rand = random.random()
        if rand < 0.70:
            # Completed
            payout.status = 'completed'
            payout.save()
            
            # Add final debit and reverse the hold
            # Reversing hold (+amount) and adding debit (-amount)
            LedgerEntry.objects.create(
                merchant=payout.merchant,
                amount_paise=payout.amount_paise, # Positive reversal of hold
                type='refund', # Re-using refund type for reversal or just "hold_reversal"
                reference_id=payout.id
            )
            LedgerEntry.objects.create(
                merchant=payout.merchant,
                amount_paise=-payout.amount_paise, # Final negative debit
                type='payout_debit',
                reference_id=payout.id
            )
            
        elif rand < 0.90:
            # Failed
            payout.status = 'failed'
            payout.save()
            
            # Refund (positive amount)
            LedgerEntry.objects.create(
                merchant=payout.merchant,
                amount_paise=payout.amount_paise,
                type='refund',
                reference_id=payout.id
            )
        else:
            # Stuck (do nothing)
            pass

@shared_task
def retry_stuck_payouts():
    """
    If payout stuck in processing > 30 seconds:
    Retry with exponential backoff (simplified here as re-queueing)
    Max 3 attempts. After that -> mark failed + refund
    """
    cutoff = timezone.now() - timedelta(seconds=30)
    stuck_payouts = Payout.objects.filter(status='processing', updated_at__lt=cutoff)
    
    for payout in stuck_payouts:
        with transaction.atomic():
            payout = Payout.objects.select_for_update().get(id=payout.id)
            if payout.attempt_count >= 3:
                payout.status = 'failed'
                payout.save()
                # Refund
                LedgerEntry.objects.create(
                    merchant=payout.merchant,
                    amount_paise=payout.amount_paise,
                    type='refund',
                    reference_id=payout.id
                )
            else:
                # Retry: Move back to pending to be picked up by process_pending_payouts
                # or just call execute_payout_simulation again
                payout.status = 'pending'
                payout.save()
