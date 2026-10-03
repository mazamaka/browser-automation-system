# 🧰 API & development reference

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
| `BROWSER_USE_API_KEY` | *optional* | optional browser-use model service |
| `HOST` | `0.0.0.0` | Server bind address |
| `PORT` | `8000` | Server port |
| `HEADLESS` | `false` | Run browser without GUI |
| `DATA_DIR` | `data` | Storage directory |

---


## Current implementation notes

- `BROWSER_TIMEOUT` and `MAX_BROWSER_STEPS` appear in the example environment file, but the execution path currently uses hard-coded values. Changing these variables alone does not reconfigure a run.
- Model names are set in `backend/ai/anthropic_provider.py` and `backend/ai/browser_use_model.py`; verify that your provider still accepts the configured model before deployment.
- A checkpoint stores execution context for the next attempt. It does not restore a browser process or guarantee continuation from the exact previous page state.
- Saved patterns and similar-task suggestions are implemented; improvement in success rate has not been established by a published benchmark.
- `make up` and `make down` kill processes on the configured development ports and matching process names. Use the separate terminal commands in the README when sharing the host with other projects.
- Runtime data is stored as local JSON files. The API has no built-in authentication; keep it local or behind your own access controls.

## Frontend checks

```bash
cd frontend
npm run build
```

The Makefile includes a `test` target, but this repository currently contains no automated test suite. A successful frontend build does not verify an agent run.
