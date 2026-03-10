# Browser Automation System

Самообучающаяся система автоматизации браузера на базе **browser-use** и AI моделей.

## Описание

Это инновационная система, которая преобразует короткие текстовые описания задач (мини-промпты) в полностью автоматизированные сценарии работы с браузером. Система использует AI для анализа веб-страниц, генерации детальных инструкций и самообучается на основе результатов выполнения.

### Основные возможности

✅ **Автоматическая генерация скриптов** - Вы даете короткое описание, система создает детальный план
✅ **Самообучение** - С каждым выполнением система становится точнее и быстрее
✅ **Мультимодельность** - Поддержка разных AI моделей (Claude, GPT-4, browser-use)
✅ **Веб-интерфейс** - Удобный React интерфейс для управления задачами
✅ **Реал-тайм обновления** - WebSocket для отслеживания прогресса выполнения
✅ **JSON хранилище** - Простое хранение промптов и истории без БД

## Архитектура

```
browser-automation-system/
├── backend/                  # Python FastAPI бэкенд
│   ├── core/                # Основная логика
│   │   ├── agent_manager.py      # Главный оркестратор
│   │   ├── browser_controller.py # Управление browser-use
│   │   ├── prompt_engine.py      # Генерация промптов
│   │   └── learning_engine.py    # Самообучение
│   ├── storage/             # Хранилище данных
│   │   ├── models.py             # Pydantic модели
│   │   └── prompt_store.py       # JSON storage
│   ├── ai/                  # AI провайдеры
│   │   ├── model_provider.py     # Абстракция
│   │   ├── anthropic_provider.py # Claude
│   │   └── browser_use_model.py  # browser-use
│   ├── api/                 # FastAPI routes
│   │   ├── routes.py
│   │   ├── schemas.py
│   │   └── websocket.py
│   └── main.py             # Точка входа
├── frontend/                # React TypeScript фронтенд
│   ├── src/
│   │   ├── components/
│   │   │   ├── TaskCreator.tsx
│   │   │   └── TaskList.tsx
│   │   ├── App.tsx
│   │   └── main.tsx
│   └── package.json
└── data/                   # Данные (создается автоматически)
    ├── prompts/            # Сохраненные промпты
    ├── executions/         # Результаты выполнения
    └── screenshots/        # Скриншоты

```

## Быстрый старт (с Makefile)

### Установка

```bash
# Клонировать или перейти в директорию проекта
cd browser-automation-system

# Установить все зависимости
make install

# Настроить .env файл
nano .env
# Добавьте:
# ANTHROPIC_API_KEY=ваш_ключ_anthropic
# BROWSER_USE_API_KEY=ваш_ключ_browser_use
```

### Запуск

```bash
# Запустить backend и frontend одной командой
make up

# Или запустить с проверкой .env
make dev
```

### Другие команды

```bash
make down     # Остановить серверы
make status   # Проверить статус
make health   # Проверить здоровье системы
make help     # Показать все команды
```

## Установка вручную (без Makefile)

### Требования

- Python 3.11+
- Node.js 18+
- Anthropic API ключ (для анализа и генерации промптов)
- Browser Use API ключ (для выполнения задач в браузере)

### Backend

```bash
# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# или
.venv\Scripts\activate  # Windows

# Установка зависимостей
pip install -r requirements.txt

# Установка Playwright браузеров
playwright install chromium

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env и добавьте ваш ANTHROPIC_API_KEY
```

### Frontend

```bash
cd frontend
npm install
```

### Запуск вручную

Backend:
```bash
source .venv/bin/activate
python -m backend.main
```

Frontend:
```bash
cd frontend
npm run dev
```

**Рекомендуется использовать `make up` для автоматического запуска!**

## Использование

### Пример 1: Простая задача

```
Мини-промпт: "зайти на google.com и найти информацию о пиве"
```

Система:
1. Откроет браузер на google.com
2. Проанализирует DOM структуру страницы
3. Создаст детальный промпт с селекторами элементов
4. Выполнит поиск через browser-use
5. Сохранит результаты и промпт для повторного использования

### Пример 2: Сложная задача

```
Мини-промпт: "зайти в гугл аккаунт и запустить рекламу по пиву"
```

Система:
1. Определит начальный URL (https://ads.google.com)
2. Проанализирует форму входа
3. Создаст план действий:
   - Перейти на страницу входа
   - Заполнить email
   - Заполнить пароль
   - Перейти в рекламный кабинет
   - Создать кампанию
4. Выполнит все шаги
5. Сохранит успешный паттерн для обучения

### API Endpoints

#### Создание задачи
```bash
POST /api/tasks/create
{
  "mini_prompt": "ваше описание задачи",
  "metadata": {}
}
```

#### Запуск выполнения
```bash
POST /api/tasks/{task_id}/run
{
  "force_new_prompt": false
}
```

#### Получение информации о задаче
```bash
GET /api/tasks/{task_id}
```

#### Список всех задач
```bash
GET /api/tasks/?limit=20&offset=0
```

#### Статистика
```bash
GET /api/stats/general
GET /api/stats/learning
```

## Как работает самообучение

### Первый запуск задачи

1. **Анализ**: AI анализирует мини-промпт и определяет начальную страницу
2. **Исследование**: Браузер открывает страницу и извлекает DOM
3. **Генерация промпта**: Claude создает детальный системный промпт с:
   - Пошаговыми инструкциями
   - CSS селекторами элементов
   - Проверками успешности
4. **Выполнение**: browser-use выполняет задачу по детальному промпту
5. **Сохранение**: Промпт и результаты сохраняются в JSON

### Повторные запуски

1. **Поиск похожих**: Система ищет похожие задачи в истории
2. **Использование промпта**: Если найден успешный промпт, используется он
3. **Быстрое выполнение**: browser-use сразу выполняет по готовому плану
4. **Оптимизация**: При ошибках промпт автоматически улучшается

### Паттерны обучения

Система извлекает и сохраняет паттерны:
- **Login patterns**: Успешные сценарии входа в аккаунты
- **Form fill patterns**: Заполнение форм
- **Navigation patterns**: Навигация по сайтам
- **E-commerce patterns**: Покупки и корзины

## Конфигурация

### Переменные окружения (.env)

```bash
# API ключи
ANTHROPIC_API_KEY=your_key_here

# Сервер
HOST=0.0.0.0
PORT=8000
HEADLESS=false  # true для запуска браузера без UI

# Данные
DATA_DIR=data

# Браузер
BROWSER_TIMEOUT=60000
MAX_BROWSER_STEPS=50
```

### Выбор AI моделей

В коде можно изменить модели:

```python
# Для анализа и генерации промптов
analysis_provider = ModelFactory.create_provider(
    "anthropic",  # или "openai"
    api_key=api_key,
    model_name="claude-sonnet-4-20250514"  # Claude Sonnet 4.5
)

# Для выполнения в браузере
execution_provider = ModelFactory.create_provider(
    "browser-use",  # использует bu-1-0 или Claude
    api_key=api_key
)
```

## Структура данных

### Task (Задача)
```json
{
  "task_id": "uuid",
  "mini_prompt": "короткий промпт от пользователя",
  "system_prompt": {
    "content": "детальный промпт с инструкциями",
    "selectors": ["#email", ".button-submit"],
    "success_rate": 0.85,
    "executions_count": 10
  },
  "status": "completed",
  "executions": [...]
}
```

### TaskExecution (Выполнение)
```json
{
  "execution_id": "uuid",
  "timestamp": "2025-01-18T10:00:00",
  "success": true,
  "duration_ms": 15000,
  "steps": [
    {
      "step_number": 1,
      "description": "Navigate to page",
      "success": true
    }
  ],
  "screenshots": ["path/to/screenshot.png"]
}
```

## Разработка

### Добавление нового AI провайдера

1. Создайте класс в `backend/ai/`:

```python
from .model_provider import AIModelProvider, ModelFactory

class MyAIProvider(AIModelProvider):
    async def generate_response(self, prompt, system_prompt=None):
        # Ваша реализация
        pass
    
    def get_langchain_model(self):
        # Возвращает LangChain модель
        pass

# Регистрация
ModelFactory.register_provider("my-ai", MyAIProvider)
```

### Расширение frontend

Добавьте новые компоненты в `frontend/src/components/`:

```typescript
export default function MyComponent() {
  // Ваш код
}
```

## Troubleshooting

### Ошибка: "ANTHROPIC_API_KEY не установлен"
Убедитесь что в `.env` файле указан валидный API ключ

### Браузер не открывается
Проверьте что Playwright установлен:
```bash
playwright install chromium
```

### Frontend не подключается к backend
Проверьте что backend запущен на порту 8000 и vite proxy настроен правильно

### Ошибки импорта Python
Убедитесь что запускаете из корневой директории:
```bash
python -m backend.main
```

## Roadmap

- [ ] Поддержка GPT-4 и других моделей
- [ ] Улучшенная система паттернов
- [ ] Экспорт задач в скрипты
- [ ] Планировщик задач (cron)
- [ ] Мультиязычность интерфейса
- [ ] Docker контейнеры
- [ ] CI/CD pipeline

## Лицензия

MIT

## Контакты

Если у вас есть вопросы или предложения, создайте Issue в репозитории.

---

**Создано с использованием:**
- browser-use - автоматизация браузера
- Claude (Anthropic) - AI анализ и генерация
- FastAPI - Python backend
- React + TypeScript - Frontend
- Playwright - управление браузером
