# Money Map Manager - Makefile
# Unified commands for development, testing, and deployment.

.PHONY: install dev dev-backend dev-frontend build clean reset-db \
       lint lint-backend lint-frontend \
       format format-backend format-frontend \
       typecheck typecheck-backend typecheck-frontend \
       test test-backend test-frontend help

# Default target.
.DEFAULT_GOAL := help

# ============================================
# COLORS
# ============================================

CYAN := \033[1;36m
GREEN := \033[1;32m
YELLOW := \033[1;33m
BLUE := \033[1;34m
RED := \033[1;31m
RESET := \033[0m

# ============================================
# INSTALLATION
# ============================================

install: ## Install all dependencies (backend + frontend).
	@echo "$(CYAN)📦 Installing all dependencies...$(RESET)"
	@echo "$(BLUE)→ Installing backend dependencies...$(RESET)"
	cd backend && uv sync
	@echo "$(BLUE)→ Installing frontend dependencies...$(RESET)"
	cd frontend && bun install
	@echo "$(GREEN)✓ All dependencies installed$(RESET)"

install-backend: ## Install backend dependencies only.
	@echo "$(CYAN)📦 Installing backend dependencies...$(RESET)"
	cd backend && uv sync
	@echo "$(GREEN)✓ Backend dependencies installed$(RESET)"

install-frontend: ## Install frontend dependencies only.
	@echo "$(CYAN)📦 Installing frontend dependencies...$(RESET)"
	cd frontend && bun install
	@echo "$(GREEN)✓ Frontend dependencies installed$(RESET)"

# ============================================
# DEVELOPMENT
# ============================================

dev: ## Start both servers (backend:8000, frontend:3000).
	@echo "$(CYAN)🚀 Starting development servers...$(RESET)"
	@echo "$(BLUE)→ Backend:  http://localhost:8000$(RESET)"
	@echo "$(BLUE)→ Frontend: http://localhost:3000$(RESET)"
	@make -j2 dev-backend dev-frontend

dev-backend: ## Start backend server only.
	@echo "$(CYAN)🐍 Starting backend server on http://localhost:8000...$(RESET)"
	cd backend && uv run uvicorn app.main:app --reload --port 8000

dev-frontend: ## Start frontend server only.
	@echo "$(CYAN)⚡ Starting frontend server on http://localhost:3000...$(RESET)"
	cd frontend && bun dev

# ============================================
# CODE QUALITY
# ============================================

# Formatting.
format: format-backend format-frontend ## Format all code.
	@echo "$(GREEN)✓ All code formatted$(RESET)"

format-backend: ## Format backend code with ruff.
	@echo "$(CYAN)🎨 Formatting backend code...$(RESET)"
	cd backend && uv run ruff format .
	@echo "$(GREEN)✓ Backend formatted$(RESET)"

format-frontend: ## Format frontend code with prettier.
	@echo "$(CYAN)🎨 Formatting frontend code...$(RESET)"
	cd frontend && bun run format
	@echo "$(GREEN)✓ Frontend formatted$(RESET)"

# Linting.
lint: lint-backend lint-frontend ## Run linters on all code.
	@echo "$(GREEN)✓ All linting passed$(RESET)"

lint-backend: ## Run ruff linter on backend.
	@echo "$(CYAN)🔍 Linting backend code...$(RESET)"
	cd backend && uv run ruff check --fix .
	@echo "$(GREEN)✓ Backend linting passed$(RESET)"

lint-frontend: ## Run ESLint on frontend.
	@echo "$(CYAN)🔍 Linting frontend code...$(RESET)"
	cd frontend && bun run lint
	@echo "$(GREEN)✓ Frontend linting passed$(RESET)"

# Type checking.
typecheck: typecheck-backend typecheck-frontend ## Type check all code.
	@echo "$(GREEN)✓ All type checks passed$(RESET)"

typecheck-backend: ## Run mypy on backend.
	@echo "$(CYAN)🔬 Type checking backend...$(RESET)"
	cd backend && uv run mypy .
	@echo "$(GREEN)✓ Backend type check passed$(RESET)"

typecheck-frontend: ## Run TypeScript type check on frontend.
	@echo "$(CYAN)🔬 Type checking frontend...$(RESET)"
	cd frontend && bun run typecheck
	@echo "$(GREEN)✓ Frontend type check passed$(RESET)"

# Testing.
test: test-backend test-frontend ## Run all tests.
	@echo "$(GREEN)✓ All tests passed$(RESET)"

test-backend: ## Run pytest on backend.
	@echo "$(CYAN)🧪 Running backend tests...$(RESET)"
	cd backend && uv run pytest
	@echo "$(GREEN)✓ Backend tests passed$(RESET)"

test-frontend: ## Run tests on frontend.
	@echo "$(CYAN)🧪 Running frontend tests...$(RESET)"
	cd frontend && bun run test
	@echo "$(GREEN)✓ Frontend tests passed$(RESET)"

test-backend-v: ## Run pytest with verbose output.
	@echo "$(CYAN)🧪 Running backend tests (verbose)...$(RESET)"
	cd backend && uv run pytest -v

test-backend-cov: ## Run pytest with coverage report.
	@echo "$(CYAN)🧪 Running backend tests with coverage...$(RESET)"
	cd backend && uv run pytest --cov=app --cov-report=term-missing

# Quality gate (run before commit).
quality: ## Run all quality checks (lint, typecheck, test).
	@echo "$(CYAN)🚦 Running quality gate...$(RESET)"
	@make lint
	@make typecheck
	@make test
	@echo "$(GREEN)✓ Quality gate passed$(RESET)"

# ============================================
# BUILD
# ============================================

build: ## Build frontend for production.
	@echo "$(CYAN)🏗️  Building frontend for production...$(RESET)"
	cd frontend && bun run build
	@echo "$(GREEN)✓ Build complete$(RESET)"

# ============================================
# DATABASE
# ============================================

reset-db: ## Delete and recreate database.
	@echo "$(YELLOW)⚠️  Deleting database...$(RESET)"
	rm -f data/moneymap.db
	@echo "$(GREEN)✓ Database deleted. It will be recreated on next backend startup.$(RESET)"

# ============================================
# CLEANUP
# ============================================

clean: ## Remove all generated files and dependencies.
	@echo "$(CYAN)🧹 Cleaning all generated files...$(RESET)"
	@echo "$(BLUE)→ Removing backend .venv...$(RESET)"
	rm -rf backend/.venv
	@echo "$(BLUE)→ Removing frontend node_modules...$(RESET)"
	rm -rf frontend/node_modules
	@echo "$(BLUE)→ Removing frontend .next...$(RESET)"
	rm -rf frontend/.next
	@echo "$(GREEN)✓ Cleanup complete$(RESET)"

clean-cache: ## Remove Python cache files.
	@echo "$(CYAN)🧹 Cleaning Python cache files...$(RESET)"
	find backend -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find backend -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cache cleaned$(RESET)"

# ============================================
# HELP
# ============================================

help: ## Show this help message.
	@echo "$(CYAN)Money Map Manager$(RESET) - Development Commands"
	@echo ""
	@echo "Usage: $(GREEN)make$(RESET) [target]"
	@echo ""
	@echo "Targets:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*##/ {printf "  $(GREEN)%-18s$(RESET) %s\n", $$1, $$2}' $(MAKEFILE_LIST)
