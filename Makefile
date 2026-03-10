.PHONY: help install up down backend frontend clean test kill-ports
SHELL := /bin/bash

# Цвета для вывода
GREEN  := \033[0;32m
YELLOW := \033[0;33m
NC     := \033[0m

help: ## Показать справку
	@echo "$(GREEN)Browser Automation System - Команды:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(YELLOW)%-15s$(NC) %s\n", $$1, $$2}'

install: ## Установить все зависимости
	@echo "$(GREEN)Установка Python зависимостей...$(NC)"
	python3 -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	@echo "$(GREEN)Установка Playwright браузеров...$(NC)"
	.venv/bin/playwright install chromium
	@echo "$(GREEN)Установка Frontend зависимостей...$(NC)"
	cd frontend && npm install
	@echo "$(GREEN)Готово! Не забудьте настроить .env файл$(NC)"

kill-ports: ## Освободить порты 8000 и 3000
	@echo "$(YELLOW)Освобождение портов...$(NC)"
	@-lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@-lsof -ti:3000 | xargs kill -9 2>/dev/null || true
	@-lsof -ti:3001 | xargs kill -9 2>/dev/null || true
	@-pkill -f "python -m backend.main" || true
	@-pkill -f "vite" || true
	@sleep 1
	@echo "$(GREEN)Порты освобождены$(NC)"

up: kill-ports ## Запустить backend и frontend
	@echo "$(GREEN)Запуск системы...$(NC)"
	@make -j2 backend frontend

backend: ## Запустить только backend
	@echo "$(GREEN)Запуск Backend на http://localhost:8000$(NC)"
	@bash -c "source .venv/bin/activate && python -m backend.main"

frontend: ## Запустить только frontend
	@echo "$(GREEN)Запуск Frontend на http://localhost:3000$(NC)"
	@cd frontend && npm run dev

down: ## Остановить все процессы
	@echo "$(YELLOW)Остановка серверов...$(NC)"
	@-lsof -ti:8000 | xargs kill -9 2>/dev/null || true
	@-lsof -ti:3000 | xargs kill -9 2>/dev/null || true
	@-lsof -ti:3001 | xargs kill -9 2>/dev/null || true
	@-pkill -f "python -m backend.main" || true
	@-pkill -f "vite" || true
	@echo "$(GREEN)Серверы остановлены$(NC)"

clean: ## Очистить временные файлы и кеш
	@echo "$(YELLOW)Очистка...$(NC)"
	rm -rf .venv
	rm -rf frontend/node_modules
	rm -rf frontend/dist
	rm -rf __pycache__
	rm -rf backend/__pycache__
	rm -rf backend/*/__pycache__
	rm -rf backend/*/*/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "$(GREEN)Очистка завершена$(NC)"

clean-data: ## Очистить данные (промпты, история)
	@echo "$(YELLOW)Очистка данных...$(NC)"
	rm -rf data/prompts/*
	rm -rf data/executions/*
	rm -rf data/screenshots/*
	rm -rf data/patterns/*
	@echo "$(GREEN)Данные очищены$(NC)"

test: ## Запустить тесты
	@echo "$(GREEN)Запуск тестов...$(NC)"
	.venv/bin/pytest

check-env: ## Проверить .env файл
	@if [ ! -f .env ]; then \
		echo "$(YELLOW)Файл .env не найден. Создаем из примера...$(NC)"; \
		cp .env.example .env; \
		echo "$(GREEN).env создан. Добавьте ваш ANTHROPIC_API_KEY$(NC)"; \
	else \
		echo "$(GREEN)Файл .env существует$(NC)"; \
		if grep -q "ANTHROPIC_API_KEY=your_anthropic_api_key_here" .env; then \
			echo "$(YELLOW)⚠️  ANTHROPIC_API_KEY не настроен!$(NC)"; \
		else \
			echo "$(GREEN)✓ ANTHROPIC_API_KEY настроен$(NC)"; \
		fi \
	fi

status: ## Показать статус серверов
	@echo "$(GREEN)Статус серверов:$(NC)"
	@if pgrep -f "python -m backend.main" > /dev/null; then \
		echo "$(GREEN)✓ Backend запущен (http://localhost:8000)$(NC)"; \
	else \
		echo "$(YELLOW)✗ Backend не запущен$(NC)"; \
	fi
	@if pgrep -f "vite" > /dev/null; then \
		echo "$(GREEN)✓ Frontend запущен (http://localhost:3000)$(NC)"; \
	else \
		echo "$(YELLOW)✗ Frontend не запущен$(NC)"; \
	fi

logs-backend: ## Показать логи backend
	@tail -f logs/backend.log 2>/dev/null || echo "Логи не найдены. Backend запущен?"

logs-frontend: ## Показать логи frontend
	@tail -f logs/frontend.log 2>/dev/null || echo "Логи не найдены. Frontend запущен?"

dev: check-env up ## Запустить в режиме разработки (с проверкой .env)

build-frontend: ## Собрать frontend для production
	@echo "$(GREEN)Сборка Frontend...$(NC)"
	cd frontend && npm run build
	@echo "$(GREEN)Frontend собран в frontend/dist$(NC)"

docker-build: ## Собрать Docker образы
	@echo "$(GREEN)Сборка Docker образов...$(NC)"
	docker-compose build

docker-up: ## Запустить через Docker
	@echo "$(GREEN)Запуск через Docker...$(NC)"
	docker-compose up -d

docker-down: ## Остановить Docker контейнеры
	@echo "$(YELLOW)Остановка Docker контейнеров...$(NC)"
	docker-compose down

docker-logs: ## Показать логи Docker
	docker-compose logs -f

stats: ## Показать статистику системы
	@echo "$(GREEN)Статистика системы:$(NC)"
	@curl -s http://localhost:8000/api/stats/general | python3 -m json.tool 2>/dev/null || echo "Backend не запущен"

health: ## Проверить здоровье системы
	@echo "$(GREEN)Проверка здоровья:$(NC)"
	@curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "$(YELLOW)Backend не отвечает$(NC)"
	@curl -s http://localhost:3000 > /dev/null 2>&1 && echo "$(GREEN)✓ Frontend доступен$(NC)" || echo "$(YELLOW)✗ Frontend не доступен$(NC)"

.DEFAULT_GOAL := help
