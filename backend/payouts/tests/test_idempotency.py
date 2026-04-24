from django.test import TransactionTestCase
from merchants.models import Merchant
from payouts.models import LedgerEntry, Payout
from payouts.services import PayoutService

class IdempotencyTest(TransactionTestCase):
    def setUp(self):
        self.merchant = Merchant.objects.create(name="Idempotency Inc")
        LedgerEntry.objects.create(
            merchant=self.merchant,
            amount_paise=10000,
            type='credit'
        )

    def test_idempotent_request(self):
        """
        Same idempotency key used twice should return the same payout object 
        and NOT create a second ledger entry.
        """
        key = "unique-key-123"
        
        # First request
        payout1, created1 = PayoutService.create_payout(self.merchant.id, 500, key)
        self.assertTrue(created1)
        
        # Second request with same key
        payout2, created2 = PayoutService.create_payout(self.merchant.id, 500, key)
        self.assertFalse(created2)
        self.assertEqual(payout1.id, payout2.id)
        
        # Check ledger entries
        ledger_entries = LedgerEntry.objects.filter(merchant=self.merchant, reference_id=payout1.id)
        self.assertEqual(ledger_entries.count(), 1, "Only one hold should exist")
        
        # Check balance (should have subtracted only 500)
        balances = PayoutService.get_balances(self.merchant.id)
        self.assertEqual(balances['available_balance'], 9500)
