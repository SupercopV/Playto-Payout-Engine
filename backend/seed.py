import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'playto_engine.settings')
django.setup()

from merchants.models import Merchant
from payouts.models import LedgerEntry

from merchants.models import Merchant
from payouts.models import LedgerEntry, Payout
from django.utils import timezone
from datetime import timedelta

def seed():
    print("Seeding database...")
    
    # 1. Create Merchants
    merchants_data = [
        {"name": "Alpha Corp", "initial_credit": 1000000},  # ₹10,000
        {"name": "Beta Logistics", "initial_credit": 500000}, # ₹5,000
        {"name": "Gamma Tech", "initial_credit": 2500000},   # ₹25,000
    ]

    for data in merchants_data:
        m, _ = Merchant.objects.get_or_create(name=data['name'])
        
        # Add initial credits if none exist
        if not LedgerEntry.objects.filter(merchant=m, type='credit').exists():
            LedgerEntry.objects.create(
                merchant=m,
                amount_paise=data['initial_credit'],
                type='credit'
            )
            print(f"Added initial credit to {m.name}")

        # 2. Add some History for Alpha Corp (the main demo merchant)
        if m.name == "Alpha Corp" and not Payout.objects.filter(merchant=m).exists():
            print("Seeding history for Alpha Corp...")
            
            # Completed Payout
            p1 = Payout.objects.create(
                merchant=m, amount_paise=50000, status='completed', 
                idempotency_key='seed-1'
            )
            LedgerEntry.objects.create(merchant=m, amount_paise=-50000, type='payout_hold', reference_id=p1.id)
            LedgerEntry.objects.create(merchant=m, amount_paise=50000, type='refund', reference_id=p1.id) # Release hold
            LedgerEntry.objects.create(merchant=m, amount_paise=-50000, type='payout_debit', reference_id=p1.id)

            # Failed Payout
            p2 = Payout.objects.create(
                merchant=m, amount_paise=25000, status='failed', 
                idempotency_key='seed-2'
            )
            LedgerEntry.objects.create(merchant=m, amount_paise=-25000, type='payout_hold', reference_id=p2.id)
            LedgerEntry.objects.create(merchant=m, amount_paise=25000, type='refund', reference_id=p2.id)

            # Pending Payout
            p3 = Payout.objects.create(
                merchant=m, amount_paise=10000, status='pending', 
                idempotency_key='seed-3'
            )
            LedgerEntry.objects.create(merchant=m, amount_paise=-10000, type='payout_hold', reference_id=p3.id)

    print("Seeding completed!")

if __name__ == "__main__":
    seed()
