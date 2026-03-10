<div align="center">

# Browser Automation System

### Self-Learning Browser Automation Powered by AI

[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black)](https://react.dev/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.3-3178C6?style=for-the-badge&logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Claude AI](https://img.shields.io/badge/Claude_AI-Sonnet_4-CC785C?style=for-the-badge&logo=anthropic&logoColor=white)](https://www.anthropic.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](https://opensource.org/licenses/MIT)

**Transform natural language instructions into fully automated browser workflows that improve with every execution.**

[Quick Start](#-quick-start) · [Architecture](#-architecture) · [API Reference](#-api-reference) · [How It Works](#-how-the-self-learning-loop-works)

</div>

---

## What is this?

Browser Automation System is an AI-powered platform that converts short text descriptions into complete browser automation scenarios. Unlike traditional RPA tools, it **learns from every execution** — extracting successful patterns, optimizing prompts, and reusing proven strategies for similar tasks.

**Example:** You type `"go to google.com and search for Python tutorials"` — the system opens a browser, navigates to Google, types the query, handles any popups, and saves the successful interaction pattern for future reuse.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **Natural Language Tasks** | Describe what you want in plain text — AI creates the execution plan |
| **Self-Learning Engine** | Extracts patterns from successful runs and reuses them for similar tasks |
| **Checkpoint System** | Saves progress mid-execution; resumes from where it left off on retry |
| **Goal Detection** | AI evaluates whether the task objective was actually achieved |
| **Prompt Optimization** | Automatically improves prompts when executions fail |
| **Real-time Monitoring** | WebSocket-powered live updates on task progress |
| **Cost Tracking** | Built-in token usage and cost calculation per execution |
| **Pattern Library** | Categorized patterns (login, form_fill, search, ecommerce, advertising) |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                        React Frontend                            │
│                   (TypeScript + TailwindCSS)                     │
│              Task Creator  │  Task List  │  Live Status           │
└──────────────┬───────────────────────────────┬───────────────────┘
               │ REST API                      │ WebSocket
┌──────────────▼───────────────────────────────▼───────────────────┐
│                      FastAPI Backend                              │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────────────┐   │
│  │   Routes    │  │  WebSocket   │  │      Schemas           │   │
│  │  (REST)     │  │  (Real-time) │  │    (Pydantic)          │   │
│  └──────┬──────┘  └──────┬───────┘  └────────────────────────┘   │
│         │                │                                        │
│  ┌──────▼────────────────▼───────────────────────────────────┐   │
│  │                   Agent Manager                            │   │
│  │            (Main Orchestrator)                              │   │
│  │  ┌─────────────┐ ┌──────────────┐ ┌────────────────────┐  │   │
│  │  │   Browser    │ │   Prompt     │ │   Learning         │  │   │
│  │  │  Controller  │ │   Engine     │ │   Engine           │  │   │
│  │  └──────┬───────┘ └──────┬───────┘ └────────┬───────────┘  │   │
│  │         │                │                   │              │   │
│  │  ┌──────▼───────┐ ┌─────▼────────┐ ┌───────▼──────────┐   │   │
│  │  │  Goal        │ │  Checkpoint  │ │  Token Usage     │   │   │
│  │  │  Detector    │ │  Manager     │ │  Tracker         │   │   │
│  │  └──────────────┘ └──────────────┘ └──────────────────┘   │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌─────────────────────┐  ┌──────────────────────────────────┐   │
│  │    AI Providers      │  │         JSON Storage             │   │
│  │  ┌───────────────┐  │  │  prompts/  executions/           │   │
│  │  │  Anthropic    │  │  │  patterns/ screenshots/          │   │
│  │  │  (Claude 4)   │  │  │  checkpoints/ websites/          │   │
│  │  ├───────────────┤  │  └──────────────────────────────────┘   │
│  │  │  browser-use  │  │                                         │
│  │  │  (bu-1-0)     │  │                                         │
│  │  └───────────────┘  │                                         │
│  └─────────────────────┘                                         │
└──────────────────────────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────────────┐
│                     Chromium Browser                              │
│              (Managed by browser-use + Playwright)                │
└──────────────────────────────────────────────────────────────────┘
```

---

## How the Self-Learning Loop Works

```
┌─────────────┐     ┌──────────────┐     ┌──────────────────┐
│  1. User     │────▶│  2. AI       │────▶│  3. browser-use  │
│  "search for │     │  generates   │     │  executes in     │
│   beer info" │     │  detailed    │     │  real browser    │
│              │     │  plan        │     │                  │
└─────────────┘     └──────────────┘     └────────┬─────────┘
                                                   │
┌─────────────┐     ┌──────────────┐     ┌────────▼─────────┐
│  6. Reuse    │◀────│  5. Store    │◀────│  4. Evaluate     │
│  patterns    │     │  successful  │     │  goal achievement│
│  on similar  │     │  patterns    │     │  & extract       │
│  tasks       │     │              │     │  patterns        │
└─────────────┘     └──────────────┘     └──────────────────┘
```

### First Execution
1. **Task Analysis** — AI analyzes the natural language prompt and determines the target URL
2. **Prompt Generation** — Claude creates a detailed system prompt with step-by-step instructions
3. **Browser Execution** — browser-use agent performs the task with vision-enabled analysis
4. **Goal Evaluation** — AI checks if the objective was actually achieved (not just "no errors")
5. **Pattern Extraction** — Successful steps are saved as reusable patterns with CSS selectors
6. **Checkpoint Save** — Progress is saved for potential retry with context

### Subsequent Runs
1. **Similarity Search** — Find matching tasks in execution history
2. **Pattern Reuse** — Apply proven successful patterns
3. **Prompt Optimization** — If a task fails, AI automatically rewrites the prompt
4. **Checkpoint Resume** — Continue from last known good state

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- [Anthropic API Key](https://console.anthropic.com/)

### Installation

```bash
git clone https://github.com/mazamaka/browser-automation-system.git
cd browser-automation-system

# Install all dependencies (Python + Node.js + Playwright)
make install

# Configure environment
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Start the system (backend on :8000, frontend on :3000)
make up
```

### Manual Setup

```bash
# Backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# Frontend
cd frontend && npm install

# Run
python -m backend.main          # Backend at http://localhost:8000
cd frontend && npm run dev      # Frontend at http://localhost:3000
```

Open **http://localhost:3000** and create your first automation task.

---

## API Reference

### Tasks

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/tasks/create` | Create a new automation task |
| `POST` | `/api/tasks/{id}/run` | Execute a task |
| `GET` | `/api/tasks/{id}` | Get task status and details |
| `GET` | `/api/tasks/` | List all tasks (paginated) |
| `GET` | `/api/tasks/{id}/executions` | Get execution history |

### Checkpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/checkpoints/{id}` | Get task checkpoint |
| `POST` | `/api/checkpoints/{id}/continue` | Resume from checkpoint |
| `DELETE` | `/api/checkpoints/{id}` | Reset task progress |

### Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/stats/general` | System-wide statistics |
| `GET` | `/api/stats/learning` | Learning engine metrics |
| `GET` | `/api/prompts/{id}` | Get generated system prompt |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `ws://localhost:8000/ws/{task_id}` | Real-time updates for a specific task |
| `ws://localhost:8000/ws` | Global event stream |

### Example: Create and Run a Task

```bash
# Create task
curl -X POST http://localhost:8000/api/tasks/create \
  -H "Content-Type: application/json" \
  -d '{"mini_prompt": "go to google.com and search for browser automation"}'

# Run task (use task_id from response)
curl -X POST http://localhost:8000/api/tasks/{task_id}/run

# Check status
curl http://localhost:8000/api/tasks/{task_id}
```

---

## Tech Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **AI Analysis** | Claude Sonnet 4 | Task analysis, prompt generation, goal evaluation |
| **Browser Execution** | browser-use + Playwright | Autonomous browser control with vision |
| **Backend** | FastAPI + Uvicorn | Async REST API + WebSocket server |
| **Frontend** | React 18 + TypeScript | Task management UI |
| **Styling** | TailwindCSS | Responsive design |
| **State** | React Query | Server state management |
| **Storage** | JSON (file-based) | Zero-config, no database required |
| **Logging** | Loguru | Structured logging with rotation |
| **AI SDK** | LangChain + Anthropic SDK | Model abstraction layer |

---

## Project Structure

```
browser-automation-system/
├── backend/
│   ├── main.py                    # FastAPI application entry point
│   ├── api/
│   │   ├── routes.py              # REST endpoints (tasks, stats, prompts, checkpoints)
│   │   ├── schemas.py             # Pydantic request/response models
│   │   └── websocket.py           # Real-time WebSocket manager
│   ├── core/
│   │   ├── agent_manager.py       # Main orchestrator — coordinates all components
│   │   ├── browser_controller.py  # browser-use wrapper with history parsing
│   │   ├── prompt_engine.py       # Prompt generation & optimization
│   │   ├── learning_engine.py     # Pattern extraction & task classification
│   │   ├── goal_detector.py       # AI-powered goal achievement evaluation
│   │   ├── checkpoint_manager.py  # Execution progress persistence
│   │   └── token_usage_tracker.py # Cost calculation per execution
│   ├── ai/
│   │   ├── model_provider.py      # Abstract AI provider (Factory pattern)
│   │   ├── anthropic_provider.py  # Claude Sonnet 4 implementation
│   │   └── browser_use_model.py   # browser-use optimized model
│   └── storage/
│       ├── models.py              # 15+ Pydantic domain models
│       └── prompt_store.py        # File-based JSON storage engine
├── frontend/
│   └── src/
│       ├── App.tsx                # Main application layout
│       └── components/
│           ├── TaskCreator.tsx     # Task creation form
│           └── TaskList.tsx        # Task history with status badges
├── data/                          # Runtime data (git-ignored)
│   ├── prompts/                   # Task definitions
│   ├── executions/                # Execution results
│   ├── patterns/                  # Learned patterns
│   ├── checkpoints/               # Saved progress
│   └── screenshots/               # Browser screenshots
├── Makefile                       # Development commands
├── requirements.txt               # Python dependencies
└── .env.example                   # Environment template
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | *required* | Claude API key for AI analysis |
| `BROWSER_USE_API_KEY` | *optional* | browser-use optimized API (faster, cheaper) |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `HEADLESS` | `false` | Run browser without GUI |
| `DATA_DIR` | `data` | Storage directory |
| `BROWSER_TIMEOUT` | `60000` | Browser operation timeout (ms) |
| `MAX_BROWSER_STEPS` | `50` | Maximum steps per execution |

---

## Development Commands

```bash
make help           # Show all available commands
make install        # Install all dependencies
make up             # Start backend + frontend
make down           # Stop all servers
make status         # Check server status
make health         # HTTP health check
make stats          # Show system statistics
make test           # Run pytest
make clean          # Remove .venv, node_modules, __pycache__
make clean-data     # Clear all execution data
```

---

## Extending the System

### Add a New AI Provider

```python
from backend.ai.model_provider import AIModelProvider, ModelFactory

class OpenAIProvider(AIModelProvider):
    async def generate_response(self, prompt, system_prompt=None, **kwargs):
        # Your implementation
        ...

    def get_langchain_model(self, callbacks=None):
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model="gpt-4", api_key=self.api_key)

ModelFactory.register_provider("openai", OpenAIProvider)
```

### Add a New Task Type

```python
# In backend/core/learning_engine.py → _classify_task()
elif any(word in prompt_lower for word in ['scrape', 'extract', 'parse']):
    return 'data_extraction'
```

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Author

**Maksym Babenko**

[![GitHub](https://img.shields.io/badge/GitHub-mazamaka-181717?style=flat-square&logo=github)](https://github.com/mazamaka)
[![Telegram](https://img.shields.io/badge/Telegram-@Mazamaka-26A5E4?style=flat-square&logo=telegram)](https://t.me/Mazamaka)
