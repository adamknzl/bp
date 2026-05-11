# Nonprofit Information System and Web Scraping Pipeline
  
Bachelor's thesis, Adam Kinzel (xkinzea00), FIT VUT Brno, 2026.

**Thesis title:** Non-profit Organisations Analysis by Searching Available Online Resources

---

## Project structure

```
bp_src/
├── backend/
│   ├── is/          — TypeScript REST API
│   └── scraper/     — Python ETL pipeline
├── frontend/        — React UI
└── data/
    ├── seed.sql                — Database dump (ready to use)
    ├── res_data_sample.csv     — Sample of ČSÚ data for pipeline demo (1000 orgs)
    ├── ground_truth_urls.csv   — Manually verified URL evaluation dataset (Experiment 1)
    └── llm_eval.csv            — Manually evaluated LLM output dataset (Experiment 2)
```

---

## Requirements

| Tool | Version |
|---|---|
| Node.js | 20+ |
| Python | 3.11+ |
| PostgreSQL | 14+ |

---

## Starting the information system

This path loads the prebuilt database and starts the application.
No API keys are required.

**1. Unzip the archive**

**2. Create the database and load seed data**
```bash
psql -U postgres -h localhost -c "CREATE DATABASE npo_db;"
psql -U postgres -h localhost -c "CREATE EXTENSION IF NOT EXISTS pgcrypto;" -d npo_db
psql -U postgres -h localhost -d npo_db < backend/scraper/data/seed.sql
```

**3. Configure and start the backend**
```bash
cd backend/is
cp .env.example .env
# Edit .env — fill in your PostgreSQL credentials
npm install
```

**4. Run Prisma ORM**
```bash
npx prisma generate
```

**5. Start the backend**
```bash
npm run dev
```

**6. Start the frontend** (new terminal)
```bash
cd frontend
npm install
npm run dev
```

**7. Open the application**
```
http://localhost:5173
```

---

## Running the pipeline (optional)

The pipeline requires valid API keys for two external services:

- **Serper API** — web search for URL discovery. Free tier includes 2 500 queries. Registration possible at [serper.dev](https://serper.dev).
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
# Process a limited number of organizations
python3 main.py --limit 20

# Process the full sample dataset in a single run
python3 main.py

# Process the full sample dataset in batches (recommended)
# Runs the pipeline 15 times, processing 100 organizations per run.
# Already-processed organizations are skipped automatically.
chmod +x run.sh
./run.sh

# Custom number of runs and batch size
./run.sh 20 50
```

Press `CTRL+C` at any time to stop — progress is saved at the end of each run. Re-running the pipeline will skip already-processed organizations automatically.

---

## Running the experiments

Experiments are executed via the `experiments.py` module. The module runs
sequentially: Experiment 1 (URL accuracy) first, then Experiment 2 (LLM quality).

The pre-filled evaluation datasets (`ground_truth_urls.csv` and `llm_eval.csv`)
are included in the submission under `backend/scraper/data/` and contain the
complete manually verified results. Run the module to reproduce the experiment
results immediately:

```bash
cd backend/scraper
python3 experiments.py
```

To run the experiments from scratch against a freshly populated database,
delete both CSV files from `data/` and re-run the module. It will generate
new evaluation files from the current database contents and prompt you to
fill in the evaluation columns manually before producing results.

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
| `SERPER_API_URL` | Serper API endpoint URL |

### `frontend/.env`

| Variable | Description | Default |
|---|---|---|
| `VITE_API_URL` | Backend API base URL | `http://localhost:3000/api` |

---

## Dataset notes

The full ČSÚ register (~500 MB) is **not included** in this archive. It is publicly available at [csu.gov.cz](https://csu.gov.cz/produkty/registr-ekonomickych-subjektu-otevrena-data) and is downloaded automatically by `main.py` when no local file is found.

To force a fresh download of the full dataset, delete `data/res_data.csv` and rerun the pipeline.  
The ČSÚ register is updated twice a month and contains data as of the 15th and last day of the month. The data files are updated several days later.