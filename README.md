# 🌐 Browser Automation System

**Run browser tasks from natural-language instructions and review their execution in a web dashboard.**

A FastAPI backend coordinates AI analysis and browser-use execution; a React interface lets you create tasks and follow progress.

## ⚡ What it does

- 🧭 **Browser tasks** — describe a goal and run it through an AI-driven browser agent.
- 🖥️ **Live progress** — follow task updates over WebSockets and inspect execution history.
- 💾 **Checkpoints** — preserve context for later attempts.
- 🧩 **Saved patterns** — extract information from previous runs and suggest similar tasks.
- 📊 **Execution records** — keep results, screenshots and reported token usage.

## 🔧 Built for experimentation

- **Separate backend and frontend**, connected through REST and WebSockets.
- **Pluggable model providers**, with Anthropic and browser-use integrations.
- **JSON storage** for tasks, execution history and patterns.
- **Inspectable execution flow**, with goal evaluation and checkpoint handling.

This is an experimental automation application. Stored patterns do not guarantee better results, and checkpoints preserve context rather than a live browser session. Review **[current implementation notes](docs/REFERENCE.md#current-implementation-notes)** before deploying it.

## 🚀 Quick start

Requires **Python 3.11+**, **Node.js 18+** and an **Anthropic API key**.

```bash
git clone https://github.com/mazamaka/browser-automation-system.git
cd browser-automation-system
make install
cp .env.example .env
```

Add `ANTHROPIC_API_KEY` to `.env`. `BROWSER_USE_API_KEY` is optional. The configured model names must be available to your provider account.

In one terminal, from the project root:

```bash
source .venv/bin/activate
HOST=127.0.0.1 python -m backend.main
```

In another:

```bash
cd frontend
npm run dev
```

Open **http://localhost:3000**. Keep the backend local: it exposes browser-control actions without built-in authentication.

**[API, configuration & development →](docs/REFERENCE.md)**

---

**Python · FastAPI · React · TypeScript · browser-use · Playwright**

**[MIT license](LICENSE)** · Built by **[Maksym Babenko](https://github.com/mazamaka)**.
