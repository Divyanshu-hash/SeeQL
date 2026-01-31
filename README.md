# SeeQL

A **visual SQL playground** for beginners. See how your queries change data in real time, with friendly explanations and no setup.

## Features

- **Dataset-first**: Built-in datasets (Students, Employees, Titanic, Iris) — explore data before writing SQL
- **Optional CSV upload**: Use your own data without any account
- **SQL playground**: Write SQL, run it, see results instantly with smooth transitions
- **Understand panel**: Step-by-step explanations of what your query does (in plain English)
- **Friendly errors**: Helpful messages that explain what went wrong and how to fix it
- **Learning tips**: Dataset descriptions and example queries for each table
- **Export**: Download the current result as CSV or JSON

## Quick start

### 1. Backend (API)

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

The API will be at `http://127.0.0.1:8000`. On first run it loads Titanic and Iris from public URLs; if that fails, small fallback tables are used.

### 2. Frontend (web app)

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173**. The frontend proxies `/api` to the backend, so both must be running.

### 3. Use SeeQL

1. **Choose Dataset** — Students, Employees, Titanic, or Iris (or upload a CSV).
2. **Explore Data** — The full table is shown with row count and description.
3. **Write SQL** — e.g. `SELECT * FROM students WHERE marks > 80`.
4. Click **Run Query** — Results appear under **See the Result**.
5. Read **Understand What Happened** for a step-by-step explanation.
6. Use **Export CSV** or **Export JSON** to download the result.

## Tech stack

- **Backend**: FastAPI, SQLAlchemy (SQLite), Pandas  
- **Frontend**: React (Vite), TypeScript, Framer Motion  
- **Optional**: Set `GROQ_API_KEY` for richer error and query explanations (LangChain/Groq). Without it, built-in fallback explanations are used.

## Project layout

```
SeeQL/
├── backend/          # FastAPI app, SQLite, datasets
│   ├── main.py       # API routes
│   ├── database.py
│   ├── sample_data.py
│   ├── error_translator.py
│   └── sql_explainer.py
├── frontend/         # React app
│   └── src/
│       ├── App.tsx
│       └── ...
└── README.md
```

## License

See [LICENSE](LICENSE).
