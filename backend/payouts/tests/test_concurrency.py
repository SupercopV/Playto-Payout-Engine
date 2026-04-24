import threading
from django.test import TransactionTestCase
from django.core.exceptions import ValidationError
from merchants.models import Merchant
from payouts.models import LedgerEntry, Payout
from payouts.services import PayoutService
from django.db import connection

class ConcurrencyTest(TransactionTestCase):
    def setUp(self):
        self.merchant = Merchant.objects.create(name="Concurrency Corp")
        # Add 1000 paise credit
        LedgerEntry.objects.create(
            merchant=self.merchant,
            amount_paise=1000,
            type='credit'
        )

    def test_simultaneous_payouts(self):
        """
        Simulate 2 simultaneous payout requests of 600 each.
        Only one should succeed since total balance is 1000.
        """
        results = []

        def make_request(key):
            # We need to close the connection in each thread for Django to handle it correctly
            connection.close()
            try:
                payout, created = PayoutService.create_payout(
                    self.merchant.id, 
                    600, 
                    key
                )
                results.append(('success', created))
            except Exception as e:
                results.append(('error', str(e)))

        t1 = threading.Thread(target=make_request, args=("key1",))
        t2 = threading.Thread(target=make_request, args=("key2",))

        t1.start()
        t2.start()
        t1.join()
        t2.join()

        successes = [r for r in results if r[0] == 'success']
        errors = [r for r in results if r[0] == 'error']

        self.assertEqual(len(successes), 1, f"Expected 1 success, got {len(successes)}. Results: {results}")
        self.assertEqual(len(errors), 1)
        self.assertIn("Insufficient funds", errors[0][1])
