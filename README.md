# Nonprofit Information System

Information system for nonprofit organizations in the Czech Republic.  
Bachelor's thesis, Adam Kinzel (xkinzea00), FIT VUT Brno, 2026.

---

## Project structure

```
bp_src/
├── backend/
│   ├── is/          — Express/TypeScript REST API
│   └── scraper/     — Python ETL pipeline
├── frontend/        — React/TypeScript/Vite UI
└── data/
    ├── seed.sql                — Database dump (~X organizations, ready to use)
    ├── res_data_sample.csv     — Sample ČSÚ input for pipeline demo (1000 orgs)
    └── ground_truth_urls.csv  — Ground truth dataset for URL accuracy evaluation
```

---

## Requirements

| Tool | Version |
|---|---|
| Node.js | 20+ |
| Python | 3.11+ |
| PostgreSQL | 14+ |

---

## Quick start — preloaded database (recommended)

This path loads the prebuilt database and starts the application.
No API keys required.

**1. Create the database and load seed data**
```bash
psql -U postgres -c "CREATE DATABASE npo_db;"
psql -U postgres -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;" -d npo_db
psql -U postgres -d npo_db < data/seed.sql
```

**2. Configure and start the backend**
```bash
cd backend/is
cp .env.example .env
# Edit .env — fill in your PostgreSQL credentials
npm install
npm run dev
```

**3. Start the frontend** (new terminal)
```bash
cd frontend
cp .env.example .env
# VITE_API_URL is pre-filled, change only if your backend runs on a different port
npm install
npm run dev
```

**4. Open the application**
```
http://localhost:5173
```

---

## Running the pipeline (optional)

The pipeline requires valid API keys for two external services:

- **Serper API** — web search for URL discovery. Free tier: 2 500 queries. Register at [serper.dev](https://serper.dev).
- **OpenAI API** — GPT-4o-mini for description and category generation. Register at [platform.openai.com](https://platform.openai.com).

These keys are only needed to run the pipeline. The preloaded `seed.sql` is sufficient to evaluate all application features without them.

**1. Set up the Python environment**
```bash
cd backend/scraper
python3 -m venv env
source env/bin/activate        # Windows: env\Scripts\activate
pip install -r requirements.txt
```

**2. Configure credentials**
```bash
cp .env.example .env
# Edit .env — fill in DB credentials and API keys
```

**3. Run the pipeline**

The sample dataset (`data/res_data_sample.csv`) is used automatically if present.  
The full ČSÚ dataset (~500 MB) is downloaded automatically if no local file is found.

```bash
# Process a limited number of organizations (recommended for testing)
python main.py --limit 20

# Process the full sample dataset
python main.py
```

Press `CTRL+C` at any time to stop — progress is saved after each organization.

---

## URL accuracy evaluation

```bash
cd backend/scraper

# Copy ground truth dataset to the scraper directory
cp ../../data/ground_truth_urls.csv data/ground_truth_urls.csv

# Run pipeline first to generate fetched_urls.csv, then evaluate
python eval_urls.py
```

---

## Environment variables

### `backend/is/.env`

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:pass@localhost:5432/npo_db` |
| `PORT` | API server port | `3000` |

### `backend/scraper/.env`

| Variable | Description |
|---|---|
| `DB_USER` | PostgreSQL username |
| `DB_PASSWORD` | PostgreSQL password |
| `OPENAI_API_KEY` | OpenAI API key (pipeline only) |
| `SERPER_API_KEY` | Serper API key (pipeline only) |

### `frontend/.env`

| Variable | Description | Default |
|---|---|---|
| `VITE_API_URL` | Backend API base URL | `http://localhost:3000/api` |

---

## Dataset notes

The full ČSÚ register (~500 MB) is **not included** in this submission. It is publicly available at [opendata.csu.gov.cz](https://opendata.csu.gov.cz) and is downloaded automatically by `main.py` when no local file is found.

To force a fresh download of the full dataset, delete `data/res_data.csv` and rerun the pipeline.  
The ČSÚ register is updated approximately twice a month.