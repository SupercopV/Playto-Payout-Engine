# Playto Payout Engine

A production-grade fintech payout system built with Django, PostgreSQL, Celery, and React.

## Features
- **Ledger-based Balance**: Single source of truth for all transactions.
- **Concurrency Safe**: Uses row-level locking (`SELECT FOR UPDATE`) to prevent double-spending.
- **Strict Idempotency**: Handles duplicate requests gracefully via `Idempotency-Key`.
- **Background Workers**: Celery tasks for asynchronous payout processing and retries.
- **Beautiful Dashboard**: Modern React UI with real-time balance and status updates.

## Prerequisites
- Docker & Docker Compose

## Quick Start

1. **Clone the repository** (or use these files).
2. **Spin up the infrastructure**:
   ```bash
   docker-compose up --build -d
   ```
3. **Run Migrations**:
   ```bash
   docker-compose exec backend python manage.py migrate
   ```
4. **Seed Data**:
   ```bash
   docker-compose exec backend python seed.py
   ```
5. **Run Frontend**:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

The dashboard will be available at `http://localhost:5173`.
The API will be running at `http://localhost:8000`.

## Testing
To run the concurrency and idempotency tests:
```bash
docker-compose exec backend python manage.py test
```

## Architecture
See [EXPLAINER.md](EXPLAINER.md) for a deep dive into the ledger logic, locking mechanisms, and AI audit.
