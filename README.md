# ⚡ AgentForge — Multi-Agent AI System

AgentForge is a multi-agent system that routes a user's question to the right
specialized agent (or breaks it into a multi-step plan across several agents),
executes the plan, and returns a single combined answer. The agent graph,
parallel execution, retries, and shared memory are all built from scratch in
raw Python — no LangGraph/CrewAI runtime is used at execution time, even
though the libraries are listed as dependencies.

## How it works

1. A question comes in through the FastAPI `/ask` endpoint.
2. The **Orchestrator** decides whether the question needs a single agent or
2. The **Orchestrator** decides whether the question needs a single agent or
   a multi-step plan (via keyword rules and the **Planner Agent**).
3. For multi-step questions, the **Planner Agent** breaks the request into
   tasks with dependencies, which are represented as a **Workflow Graph**.
4. The **Graph Executor** runs independent tasks in parallel
   (`ThreadPoolExecutor`), respects dependencies, and retries failed steps
   via the **Retry Manager**.
5. Each agent's output is stored in **Shared Working Memory** so later
   agents can use earlier results.
6. The **Final Answer Agent** combines all results into one response.
7. The conversation is saved to **Conversation Memory** for context in
   future turns.

## Agents

| Agent | Responsibility |
|---|---|
| Research Agent | Searches the web (via Tavily) and answers with Groq |
| Coding Agent | Programming questions, debugging, code generation |
| SQL Agent | SQL queries, explanations, and debugging |
| Planner Agent | Breaks complex questions into a multi-step plan |
| Final Answer Agent | Merges results from multiple agents into one answer |
| Calculator Tool | Handles arithmetic questions directly |

## Tech stack

- **Backend**: FastAPI, Python
- **LLM**: Groq (`openai/gpt-oss-20b` by default)
- **Web search**: Tavily
- **Memory**: FAISS + Sentence-Transformers for vector memory, JSON-based
  conversation and shared working memory
- **Frontend**: Vanilla HTML/CSS/JS (no framework)

## Project structure

```
backend/
├── agents/          # Research, Coding, SQL, Planner, Final Answer agents
├── graph/            # WorkflowGraph + GraphExecutor (custom DAG execution)
├── workflow/         # Retry logic
├── memory/           # Conversation memory, shared memory, vector memory
├── tools/            # Web search (Tavily), calculator
├── models/           # AgentMessage data model
├── orchestrator/      # Central controller: routing, planning, execution
├── api.py            # FastAPI routes (/ask, /health, /info)
└── main.py           # App entrypoint
frontend/
├── index.html
├── script.js
└── style.css
```

## Setup

1. Clone the repo and create a virtual environment:
   ```
   python -m venv .venv
   .venv\Scripts\activate      # Windows
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root with:
   ```
   GROQ_API_KEY=your_groq_key
   TAVILY_API_KEY=your_tavily_key
   GROQ_MODEL=openai/gpt-oss-20b   # optional, this is the default
   ```

3. Start the backend:
   ```
   uvicorn backend.main:app --reload --port 8000
   ```

4. Serve the frontend with a local server (e.g. VS Code's Live Server
   extension) rather than opening `index.html` directly — the backend's
   CORS settings only allow `http://127.0.0.1:5500` and
   `http://localhost:5500`.

## API endpoints

- `GET /` — health/info
- `GET /health` — health check used by the frontend's status indicator
- `GET /info` — basic service info
- `POST /ask` — `{ "question": "..." }` → `{ "success", "question", "answer" }`

## Status / roadmap

- [x] Multi-agent routing with keyword-based classification
- [x] Multi-step planning and parallel graph execution with retries
- [x] Shared memory across agents in a single request
- [x] Conversation memory across turns
- [ ] Iterative (ReAct-style) retrieval loop in the Research Agent —
      currently single-shot search + answer
- [ ] Automated tests