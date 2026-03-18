# JobMatch AI - Resume Screening Agent

JobMatch AI is an agentic resume screening system built with:

- **Frontend**: React + Vite
- **Backend**: Flask + LangGraph + LangChain
- **LLM**: Gemini (`gemini-3.1-flash-lite-preview`)
- **Web Search**: Tavily
- **Database**: SQLite

---

## Project Structure

```text
AI Resume Screening System/
├─ backend/
│  ├─ app/
│  │  ├─ __init__.py
│  │  ├─ config.py
│  │  ├─ routes.py
│  │  ├─ agent/
│  │  │  ├─ graph.py
│  │  │  └─ prompt.py
│  │  ├─ tools/
│  │  │  ├─ db_tool.py
│  │  │  ├─ jd_scorer.py
│  │  │  └─ web_search.py
│  │  └─ services/
│  │     └─ sqlite_service.py
│  ├─ data/
│  ├─ .env.example
│  ├─ requirements.txt
│  └─ run.py
├─ frontend/
│  ├─ src/
│  ├─ .env.example
│  └─ package.json
└─ README.md
```

---

## Prerequisites

- **Python** 3.10+
- **Node.js** 18+ (recommended)
- **npm** 9+

---

## Backend Setup (Flask)

### 1) Go to backend folder

```bash
cd backend
```

### 2) Create and activate virtual environment

#### Windows (PowerShell)

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

If activation is blocked:

```bash
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

#### macOS/Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3) Install dependencies

```bash
pip install -r requirements.txt
```

### 4) Create `.env` from `.env.example`

```bash
copy .env.example .env
```

For macOS/Linux:

```bash
cp .env.example .env
```

### 5) Add values in `backend/.env`

Use this exact template:

```env
FLASK_ENV=development
FLASK_PORT=5000

# Gemini
GOOGLE_API_KEY=your_google_api_key_here
GEMINI_MODEL=gemini-3.1-flash-lite-preview
GEMINI_TEMPERATURE=0.2

# Tavily
TAVILY_API_KEY=your_tavily_api_key_here

# SQLite
DB_PATH=./data/jobmatch.db

# Agent
MAX_AGENT_ITERATIONS=8

# Frontend CORS origin
FRONTEND_ORIGIN=http://localhost:5173
```

### 6) Run backend server

```bash
python run.py
```

Backend runs on:

- `http://127.0.0.1:5000`
- Health API: `http://127.0.0.1:5000/api/health`

---

## Frontend Setup (React + Vite)

Open a **new terminal**:

### 1) Go to frontend folder

```bash
cd frontend
```

### 2) Install dependencies

```bash
npm install
```

### 3) Create frontend `.env`

Create `frontend/.env` with:

```env
VITE_API_BASE_URL=http://127.0.0.1:5000/api
VITE_API_TIMEOUT_MS=120000
```

### 4) Run frontend

```bash
npm run dev
```

Frontend runs on:

- `http://localhost:5173`

---

## How to Use

1. Start backend.
2. Start frontend.
3. Open frontend in browser.
4. Enter:
   - **Recruiter Command**
   - **Job Description** (optional for DB-only commands)
5. Click **Run JobMatch Agent**.

Expected flow:

`web_search -> jd_scorer -> db_tool INSERT -> db_tool SELECT -> final recommendation`

---

## Sample Commands

### Candidate evaluation (full flow)

```text
Score Rahul Sharma for our Python backend role, search his GitHub, save results, and recommend.
```

### Candidate with no online profile

```text
Evaluate Priya Mehta for our Python backend role and save.
```

Expected behavior: score around 40-55 and recommendation `Insufficient Info — Request Resume`.

### DB-only commands (no JD needed)

```text
Show all evaluated candidates.
Who are the top 3 candidates?
Show me Rahul Sharma's record.
Remove Rahul Sharma from the database.
```

---

## Sample Output (Example)

```text
Rahul Sharma scored 85/100.
Strength: Strong alignment with Python backend stack.
Gap: Unspecified depth of SQL optimization.
Recommend: Interview.
```

---

## Real ReAct Trace (Example Run)

```text
Thought: I need to find Rahul Sharma's professional profile or GitHub first.
Action: web_search({"query":"Rahul Sharma Python developer GitHub profile"})
Observation: github.com/rahulsushilsharma ... backend systems, cloud, AI/ML projects.

Thought: Now I will score him against the Python Backend JD.
Action: jd_scorer({"candidate":"Rahul Sharma", "profile":"GitHub ...", "jd":"Role: Python Backend Developer ..."})
Observation: score=85, strengths=3, gaps=2, recommendation=Interview

Thought: Save the result.
Action: db_tool({"action":"INSERT", ...})
Observation: Saved successfully.

Thought: Verify the saved record.
Action: db_tool({"action":"SELECT","candidate":"Rahul Sharma"})
Observation: Record retrieved successfully.

Thought: Done.
Action: finish({})
Observation: N/A
```

---

## Common Commands

### Backend

```bash
python run.py
```

### Frontend

```bash
npm run dev
npm run build
```

---

## Notes

- Keep real API keys only in `backend/.env`.
- Do not put real secrets in `.env.example`.
- `backend/.gitignore` already excludes `.env` and SQLite DB files.
- Timestamps are rendered in **IST** in frontend.
