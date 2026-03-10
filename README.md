# Browser Automation System

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Self-learning browser automation system based on **browser-use** and AI models (Claude). Transforms short text descriptions into fully automated browser interaction scenarios, learning from execution results.

## Features

✅ **Automatic Script Generation** - Describe task, system creates detailed automation plan
✅ **Self-Learning** - Improves with each execution
✅ **Multi-Model Support** - Claude, GPT-4, browser-use
✅ **Web Interface** - React-based UI for task management
✅ **Real-time Updates** - WebSocket for execution progress
✅ **JSON Storage** - Simple prompts and history storage without database

## Quick Start

### Setup

```bash
cd browser-automation-system
make install
nano .env  # Add ANTHROPIC_API_KEY
make up    # Run backend (8000) and frontend (3000)
```

### Manual Setup

**Requirements:** Python 3.11+, Node.js 18+, Anthropic API key

Backend:
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Frontend:
```bash
cd frontend && npm install
```

Run:
```bash
python -m backend.main  # Backend
cd frontend && npm run dev  # Frontend
```

## Architecture

```
backend/
├── core/                   # Main orchestration
│   ├── agent_manager.py    # Main orchestrator
│   ├── browser_controller.py
│   ├── prompt_engine.py    # Prompt generation
│   └── learning_engine.py  # Self-learning
├── storage/               # Data storage (JSON)
│   ├── models.py          # Pydantic models
│   └── prompt_store.py    # File-based storage
├── ai/                    # AI providers
│   ├── model_provider.py  # Abstraction
│   └── anthropic_provider.py
├── api/                   # FastAPI routes
└── main.py               # Entry point

frontend/                  # React + TypeScript
```

## How It Works

### First Task Execution

1. **Analysis** - AI analyzes task and determines initial page
2. **Page Exploration** - Browser opens page, extracts DOM
3. **Prompt Generation** - Claude creates detailed system prompt with:
   - Step-by-step instructions
   - CSS selectors for elements
   - Success checks
4. **Execution** - browser-use performs task following the detailed prompt
5. **Learning** - Extract successful patterns for future reuse

### Subsequent Runs

1. **Similarity Search** - Find similar tasks in history
2. **Reuse Prompt** - Use proven successful prompt
3. **Fast Execution** - browser-use runs task from existing plan
4. **Auto-Optimize** - Improve prompts when errors occur

## API

```bash
# Create task
POST /api/tasks/create
{
  "mini_prompt": "go to google.com and find beer information"
}

# Run task
POST /api/tasks/{task_id}/run

# Get status
GET /api/tasks/{task_id}

# List tasks
GET /api/tasks/?limit=20

# Statistics
GET /api/stats/general
GET /api/stats/learning
```

## Environment Configuration

```env
ANTHROPIC_API_KEY=your_key_here
HOST=0.0.0.0
PORT=8000
HEADLESS=false
DATA_DIR=data
BROWSER_TIMEOUT=60000
MAX_BROWSER_STEPS=50
```

## Data Structure

**Task Storage** (`data/prompts/`):
- Task ID, mini-prompt, system-prompt with success rate
- Maintains execution history

**Learning Patterns** (`data/patterns/`):
- Extracted from successful executions
- Types: login, form_fill, search, ecommerce
- Shared selectors and approaches

## Development

### Commands

```bash
make status    # Check server status
make health    # Health check
make logs-backend    # Backend logs
make test      # Run tests
```

### Add New AI Provider

```python
from backend.ai.model_provider import AIModelProvider, ModelFactory

class MyProvider(AIModelProvider):
    async def generate_response(self, prompt, system_prompt=None):
        # Implementation
        pass

    def get_langchain_model(self):
        # Return LangChain model
        pass

ModelFactory.register_provider("my-provider", MyProvider)
```

## Troubleshooting

- **ANTHROPIC_API_KEY not set** - Add to `.env` file
- **Browser won't open** - Run `playwright install chromium`
- **Frontend can't connect** - Verify backend runs on 8000
- **Import errors** - Run from project root: `python -m backend.main`

## License

MIT - see [LICENSE](LICENSE) file.

## Links

- **Documentation**: See [CLAUDE.md](./CLAUDE.md) for architecture details
- **Frontend Build**: `cd frontend && npm run build`
- **Testing**: `pytest` from project root
