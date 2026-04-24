# Playto Payout Engine - Technical Explainer

## 1. Ledger Architecture
The system uses a **Single Source of Truth** ledger. Balance is never stored as a column in the `Merchant` table; it is always computed by aggregating `LedgerEntry` rows.

### SQL for Balance Calculation
```sql
SELECT SUM(amount_paise) 
FROM payouts_ledgerentry 
WHERE merchant_id = <ID>;
```

### Why Ledger?
- **Auditability**: Every movement of money is recorded.
- **Correctness**: Prevents "drift" between balance and transaction history.
- **Flexibility**: We can calculate historical balances at any point in time.

## 2. Concurrency Control (Locking)
To prevent race conditions (e.g., two requests spending the same balance), we use **Pessimistic Locking** on the merchant row.

### Code snippet:
```python
with transaction.atomic():
    merchant = Merchant.objects.select_for_update().get(id=merchant_id)
    # Balance calculation and payout creation happen while merchant row is LOCKED
```
This ensures that if two requests for the same merchant arrive simultaneously, the second one will wait until the first one commits its transaction.

## 3. Idempotency
We prevent duplicate payouts using an `Idempotency-Key` header.

- **Storage**: The key is stored in the `Payout` model.
- **Constraint**: A unique database constraint on `(merchant, idempotency_key)`.
- **Logic**: If a key exists, we return the existing payout data without performing any further balance checks or ledger entries.

## 4. State Machine
Payouts follow a strict lifecycle:
`pending` → `processing` → `completed` | `failed`

- **Blocked Transitions**: We cannot move from `completed` to `failed`, or `failed` to `processing`.
- **Worker Logic**: The background worker picks `pending` payouts, moves them to `processing`, and then simulates an external API call to reach a final state.

## 5. AI Audit (Refactoring Example)

### ❌ Wrong AI Generation (Buggy)
The AI might try to calculate balance in Python and then save it:
```python
# BUGGY: Race condition possible between read and write
balance = LedgerEntry.objects.filter(merchant=m).aggregate(Sum('amount'))['amount__sum']
if balance >= request_amount:
    payout = Payout.objects.create(...)
    LedgerEntry.objects.create(amount=-request_amount, ...)
```
**Problem**: Two threads can both read the same balance before either has written the debit, leading to double-spending.

### ✅ Corrected Version (Safe)
```python
with transaction.atomic():
    # Lock the merchant row to serialize all financial operations for this merchant
    merchant = Merchant.objects.select_for_update().get(id=merchant_id)
    
    # Calculate balance INSIDE the lock
    current_balance = LedgerEntry.objects.filter(merchant=merchant).aggregate(
        Sum('amount_paise')
    )['amount_paise__sum'] or 0
    
    if current_balance < amount_paise:
        raise ValidationError("Insufficient funds")
    
    # Commit together
    Payout.objects.create(...)
    LedgerEntry.objects.create(...)
```
**Fix**: Using `select_for_update()` ensures that no other process can modify or even read (with lock) the merchant's financial state until this transaction completes.
