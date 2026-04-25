.PHONY: help install migrate makemigrations shell createsuperuser test test-coverage test-fast test-frontend wallet-balance check-deposits sync-balances dev-backend dev-celery dev-frontend

help:
	@echo "Available commands:"
	@echo "  make install          - Install backend dependencies"
	@echo "  make migrate          - Run database migrations"
	@echo "  make makemigrations   - Create new migrations"
	@echo "  make shell            - Open Django shell"
	@echo "  make createsuperuser  - Create Django superuser"
	@echo "  make test             - Run all backend tests with coverage"
	@echo "  make test-fast        - Run tests without coverage (faster)"
	@echo "  make test-frontend    - Run frontend tests"
	@echo "  make wallet-balance   - Check wallet balances"
	@echo "  make check-deposits   - Manually trigger deposit check"
	@echo "  make sync-balances    - Manually trigger balance sync"
	@echo "  make dev-backend      - Start Django development server"
	@echo "  make dev-celery       - Start Celery worker"
	@echo "  make dev-frontend     - Start Next.js development server"

install:
	@echo "Installing backend dependencies..."
	cd backend && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd frontend && npm install

migrate:
	cd backend && python manage.py migrate

makemigrations:
	cd backend && python manage.py makemigrations

shell:
	cd backend && python manage.py shell

createsuperuser:
	cd backend && python manage.py createsuperuser

test:
	cd backend && venv\Scripts\python.exe -m pytest apps/ tests/ --no-cov -q

test-coverage:
	cd backend && venv\Scripts\python.exe -m pytest apps/ tests/ --cov=apps --cov-report=term-missing --cov-report=html:htmlcov -v

test-fast:
	cd backend && venv\Scripts\python.exe -m pytest apps/ tests/ --no-cov -x -q

test-frontend:
	cd frontend && npm test -- --run

dev-backend:
	cd backend && python manage.py runserver

dev-celery:
	cd backend && celery -A config worker -l info --pool=solo

dev-frontend:
	cd frontend && npm run dev

# Blockchain-specific commands
wallet-balance:
	@echo "Checking wallet balances..."
	cd backend && python manage.py shell -c "from apps.wallets.models import Wallet; from apps.wallets.services import WalletService; \
	for w in Wallet.objects.select_related('user').all(): \
		print(f'User: {w.user.username}, Address: {w.address}, Balance: {w.user.balance}')"

check-deposits:
	@echo "Manually triggering deposit check..."
	cd backend && python manage.py shell -c "from apps.wallets.tasks import monitor_deposits; monitor_deposits.delay()"

sync-balances:
	@echo "Manually triggering balance sync..."
	cd backend && python manage.py shell -c "from apps.wallets.tasks import sync_wallet_balances; sync_wallet_balances.delay()"
