.PHONY: help sync run test token reload status accounts

help:
	@echo "Usage: make [target]"
	@echo ""
	@echo "Targets:"
	@echo "  sync     - Sync dependencies"
	@echo "  run      - Run the server"
	@echo "  test     - Run tests"
	@echo "  token    - Sync token from AWS SSO"
	@echo "  reload   - Reload configuration (hot reload)"
	@echo "  status   - Show account manager status"
	@echo "  accounts - List all configured accounts"

sync:
	uv sync

run:
	uv run python main.py

test:
	uv run pytest

token:
	uv run python sync_token.py

reload:
	@echo "Reloading configuration..."
	@PROXY_API_KEY=$$(grep '^PROXY_API_KEY=' .env | cut -d '=' -f 2 | tr -d '"' | tr -d "'"); \
	if [ -z "$$PROXY_API_KEY" ]; then \
		echo "Error: PROXY_API_KEY not found in .env"; \
		exit 1; \
	fi; \
	curl -X POST http://localhost:8000/admin/reload \
		-H "X-Admin-Token: $$PROXY_API_KEY" \
		-H "Content-Type: application/json" \
		-s | python -m json.tool || echo "Failed to reload configuration"

status:
	@echo "Fetching account manager status..."
	@PROXY_API_KEY=$$(grep '^PROXY_API_KEY=' .env | cut -d '=' -f 2 | tr -d '"' | tr -d "'"); \
	if [ -z "$$PROXY_API_KEY" ]; then \
		echo "Error: PROXY_API_KEY not found in .env"; \
		exit 1; \
	fi; \
	curl -X GET http://localhost:8000/admin/status \
		-H "X-Admin-Token: $$PROXY_API_KEY" \
		-s | python -m json.tool || echo "Failed to fetch status"

accounts:
	@echo "Fetching configured accounts..."
	@PROXY_API_KEY=$$(grep '^PROXY_API_KEY=' .env | cut -d '=' -f 2 | tr -d '"' | tr -d "'"); \
	if [ -z "$$PROXY_API_KEY" ]; then \
		echo "Error: PROXY_API_KEY not found in .env"; \
		exit 1; \
	fi; \
	curl -X GET http://localhost:8000/admin/accounts \
		-H "X-Admin-Token: $$PROXY_API_KEY" \
		-s | python -m json.tool || echo "Failed to fetch accounts"
