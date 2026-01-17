.PHONY: help run stop logs status restart healthcheck clean install

PORT ?= 5050
WORKERS ?= 2

help:
	@echo "Quantum AI API - Makefile targets:"
	@echo "  make run         - Start API with Gunicorn on port $(PORT)"
	@echo "  make stop        - Stop running API"
	@echo "  make logs        - Tail API logs"
	@echo "  make status      - Check API status"
	@echo "  make restart     - Restart API"
	@echo "  make healthcheck - Run health check"
	@echo "  make clean       - Remove PID and log files"
	@echo "  make install     - Install dependencies"
	@echo ""
	@echo "Environment variables:"
	@echo "  PORT=$(PORT)     - API port"
	@echo "  WORKERS=$(WORKERS) - Gunicorn workers"

run:
	@echo "🚀 Starting Quantum AI API on port $(PORT) with $(WORKERS) workers..."
	@if [ -f .api.pid ]; then \
		echo "⚠️  API already running (PID: $$(cat .api.pid))"; \
		exit 1; \
	fi
	@gunicorn -w $(WORKERS) -b 0.0.0.0:$(PORT) wsgi:app \
		--daemon \
		--pid .api.pid \
		--access-logfile logs/access.log \
		--error-logfile logs/error.log
	@sleep 2
	@if [ -f .api.pid ]; then \
		echo "✅ API started (PID: $$(cat .api.pid))"; \
		$(MAKE) healthcheck; \
	else \
		echo "❌ Failed to start API"; \
		exit 1; \
	fi

stop:
	@echo "🛑 Stopping Quantum AI API..."
	@if [ ! -f .api.pid ]; then \
		echo "⚠️  No PID file found"; \
		pkill -f "gunicorn.*wsgi:app" 2>/dev/null && echo "✅ Killed gunicorn processes" || echo "ℹ️  No processes found"; \
	else \
		kill $$(cat .api.pid) 2>/dev/null && echo "✅ API stopped" || echo "⚠️  Process not found"; \
		rm -f .api.pid; \
	fi

logs:
	@echo "📋 Tailing API logs (Ctrl+C to exit)..."
	@mkdir -p logs
	@tail -f logs/error.log logs/access.log

status:
	@if [ -f .api.pid ]; then \
		PID=$$(cat .api.pid); \
		if ps -p $$PID > /dev/null 2>&1; then \
			echo "✅ API running (PID: $$PID)"; \
			$(MAKE) healthcheck; \
		else \
			echo "❌ PID file exists but process not found"; \
			rm -f .api.pid; \
		fi \
	else \
		echo "❌ API not running"; \
	fi

restart: stop
	@sleep 1
	@$(MAKE) run

healthcheck:
	@chmod +x healthcheck.sh
	@./healthcheck.sh

clean:
	@echo "🧹 Cleaning up..."
	@rm -f .api.pid
	@rm -rf logs/*.log
	@echo "✅ Cleaned"

install:
	@echo "📦 Installing dependencies..."
	@pip install -q gunicorn flask torch scikit-learn pennylane
	@echo "✅ Dependencies installed"
