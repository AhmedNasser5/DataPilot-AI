# DataPilot AI

**"Upload Your Data. Understand It. Clean It. Analyze It."**

DataPilot AI is a production-grade, AI-assisted data analytics platform. It is
**not** a CSV viewer and **not** a collection of fake AI features: every
number shown to the user — quality scores, statistics, KPI values, SQL
results — comes from real, deterministic computation (pandas / NumPy / SciPy
/ scikit-learn / DuckDB). The AI layer is used strictly for reasoning,
planning, explanation, and SQL/text generation — **never for inventing a
number**.

---

## ✨ Features

- **Universal ingestion** — CSV, TSV, delimited TXT, XLSX/XLS (multi-sheet
  aware), JSON, NDJSON, Parquet, Feather, with content-based format
  detection (not just file extension).
- **Deep profiling** — per-column type detection (including numeric/date
  stored as text), semantic-type guessing (email, phone, URL, currency,
  percentage, geography, ID) with explicit confidence scores.
- **Transparent Data Quality Score** — an auditable, documented formula
  across Completeness, Validity, Consistency, and Uniqueness. You can see
  exactly which issues affected the score.
- **Explainable cleaning engine** — three levels (Safe Automatic,
  AI-Assisted Suggested, Advanced Contextual). Every transformation shows
  before/after, reason, confidence, and expected impact. You approve or
  reject each one. **The original dataset is never overwritten.**
- **Outlier policy: FLAG, not silently remove** — IQR, Z-score, Modified
  Z-score, or Isolation Forest, auto-selected based on sample size and
  skewness.
- **Real SQL analytics** — every dataset version is registered as a real
  DuckDB table. SQL shown to the user is the SQL that was actually executed.
  A safety layer blocks DROP/DELETE/UPDATE/INSERT/ALTER and multi-statement
  injection, and enforces row/time limits.
- **Domain-aware KPI discovery** — infers the likely business domain
  (Sales, Finance, HR, Marketing, ...) from column names and semantic types,
  then recommends only KPIs whose required columns actually exist. KPI
  values are calculated by executing real SQL — never estimated.
- **Auto-generated dashboard** — chart type is chosen based on the actual
  column-type combinations present (date+numeric → line chart, category+
  numeric → bar chart, two numerics → scatter, etc.).
- **Conversational AI Analyst** — ask questions in natural language; the
  system generates SQL, **validates** it, **executes** it, and explains the
  **real** result. Dataset values are always treated as untrusted data, never
  as instructions (prompt-injection protection).
- **Full transformation audit trail & dataset versioning** (v1 Original, v2
  Cleaned, ...).
- **Exports** — cleaned dataset (CSV/XLSX/Parquet/JSON), data-quality report,
  cleaning report, transformation history.

---

## 🏗️ Architecture

```
Streamlit UI  →  Application Services  →  Workflow Orchestration
                                              ↓
                                     Core Data Engines
                              (Ingestion / Profiling / Quality /
                               Cleaning / SQL / Analytics / KPI /
                               Dashboard)
                                              ↓
                                DuckDB  +  In-memory Dataset Storage
```

Streamlit is a thin UI layer only. **All business logic lives in
`core/`, `services/`, and `ai/`**, which are completely framework-independent
— they can be reused behind FastAPI + React later without a rewrite.

See [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md),
[`docs/AI_DESIGN.md`](docs/AI_DESIGN.md), and
[`docs/DATA_PIPELINE.md`](docs/DATA_PIPELINE.md) for details.

---

## 📁 Project Structure

```
datapilot-ai/
├── streamlit_app/        # UI layer only (pages + components)
├── core/                 # Framework-independent engines
│   ├── ingestion/         Format detection + loaders (CSV/Excel/JSON/Parquet)
│   ├── profiling/         Column/dataset profiling, type & semantic detection
│   ├── quality/            Missing/duplicate/type/consistency/outlier detectors
│   ├── cleaning/           Planner, transformations, executor, validator
│   ├── sql/                DuckDB engine, safety validator, executor
│   ├── analytics/          Statistics, correlation, trends, anomalies
│   ├── kpi/                Domain detection, KPI recommender & calculator
│   ├── dashboard/          Chart recommender, dashboard planner/generator
│   └── export/             Dataset / report / transformation exporters
├── ai/                   # LLM orchestration — reasoning & generation ONLY
├── services/             # Application-layer facades used by the UI
├── models/               # Dataclasses shared across all layers
├── storage/              # Original / versioned / processed datasets, exports
├── data/                 # DuckDB file (in-memory by default)
├── tests/                # Unit + integration tests
└── docs/                 # Architecture, AI design, data pipeline docs
```

---

## 🚀 Installation

```bash
git clone <repo-url>
cd datapilot-ai
python -m venv .venv && source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env
# Edit .env and set LLM_API_KEY if you want the AI features enabled
```

## ▶️ Running the app

```bash
streamlit run streamlit_app/app.py
```

Then open the URL Streamlit prints (typically `http://localhost:8501`).

## 🔑 Environment Variables

See [`.env.example`](.env.example). Key ones:

| Variable | Purpose |
|---|---|
| `LLM_PROVIDER` | `anthropic` or `none`. AI features degrade gracefully when `none`. |
| `LLM_API_KEY` | Your API key. Never commit this. |
| `MODEL_NAME` | Model identifier, e.g. `claude-sonnet-4-5`. |
| `MAX_FILE_SIZE_MB` | Upload size ceiling. |
| `MAX_QUERY_TIME_SECONDS` / `MAX_RESULT_ROWS` | SQL safety limits. |

**AI features work without a key too** — the app tells you plainly that AI
generation is disabled, and every deterministic feature (profiling, quality,
cleaning, SQL Lab, KPIs, dashboard) keeps working fully.

---

## 🧪 Testing

```bash
pip install pytest
pytest tests/ -v
```

24 tests cover ingestion (multiple formats, encodings, duplicate columns),
profiling & quality scoring, the cleaning engine (including a hard guarantee
that the **original dataframe object is never mutated**), SQL safety
(destructive statements blocked, injection blocked), and a full
ingest → clean → validate → SQL → KPI integration test on a realistic messy
dataset.

---

## 🔒 Security

- File-size limits, safe filename handling, isolated in-memory dataset
  handling per session.
- SQL: read-only by construction (SELECT/WITH only), destructive keywords
  blocked, multi-statement injection blocked, automatic row-limit injection,
  execution timing tracked.
- Prompt-injection protection: dataset **values** are always sent to the LLM
  as inert context, never as instructions; the system prompt explicitly
  tells the model to treat any instruction-like text found in cell values as
  literal data.
- No secrets are hardcoded; everything sensitive comes from environment
  variables (`.env`, excluded from version control).

---

## ⚠️ Limitations & Honesty Notice

- Not every file format that exists is supported — see the ingestion list
  above. The loader registry is designed so new formats/sources (databases,
  REST APIs, Google Sheets, cloud storage) can be added without touching
  existing code.
- Domain detection and semantic-type guesses are **probabilistic** — they
  always carry a confidence score and are never asserted as certain facts.
- KPIs are only shown when their required columns can actually be resolved
  in your dataset. If a KPI can't be calculated, the app says so explicitly
  instead of guessing a value.
- Outlier detection flags candidates for review — it does not decide for you
  whether a value is invalid.

---

## 🗺️ Roadmap

- FastAPI + React frontend reusing the exact same `core/` and `services/`
  layers.
- Database connectors (PostgreSQL, MySQL, SQL Server, SQLite) via the same
  loader-registry pattern already used for files.
- REST API / Google Sheets / cloud-storage ingestion sources.
- Multi-agent AI orchestration for deeper root-cause analysis ("why did
  revenue drop in March") once the single-agent flow has more production
  mileage.
- PDF analytical report export.

---

## License

MIT
