# SafeStep

Neighborhood safety intelligence for NYC. Click any neighborhood on the map to get a real-time risk assessment, AI-generated briefing, and safer nearby alternatives — all powered by live NYPD crime data.

![SafeStep Map](https://placehold.co/1200x600?text=SafeStep+Screenshot)

## Features

- **Interactive choropleth map** — 262 NYC neighborhoods colored by risk band (Low / Moderate / Elevated / High)
- **Time-of-day filter** — Morning, Afternoon, Evening, Late Night each produce different risk scores
- **Traveler profiles** — Solo, Couple, Family, Nightlife — briefings adapt to who's asking
- **AI safety briefings** — Gemini 1.5 Flash generates a 4-sentence neighborhood summary from crime stats, news, and community signals
- **Compare mode** — Side-by-side risk comparison of two neighborhoods
- **Live news alerts** — 72-hour alert banner from NewsAPI + NYT
- **Community sentiment** — Reddit signal classification for safety-relevant local posts
- **Nearby safer alternatives** — Automatically suggests lower-risk neighborhoods in the same borough

## Tech Stack

**Frontend**
- React 18 + TypeScript + Vite
- MapLibre GL JS + MapTiler (interactive map)
- Tailwind CSS + Recharts

**Backend**
- Python 3.9 + FastAPI + asyncpg
- SQLAlchemy (async) + GeoAlchemy2
- PostgreSQL 16 + PostGIS 3.4
- APScheduler (cron jobs for data refresh)

**AI / Data**
- Google Gemini 1.5 Flash (safety briefings + Reddit classification)
- NYC Open Data / Socrata (887k+ NYPD crime incidents)
- NewsAPI + NYT Article Search API
- Reddit PRAW + Census ACS

## Local Development

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker Desktop

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/safestep.git
cd safestep
```

**Backend:**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm install
```

### 2. Start the database

```bash
docker compose up -d
```

### 3. Configure environment variables

```bash
# backend/.env
cp backend/.env.example backend/.env
# fill in your keys

# frontend/.env
cp frontend/.env.example frontend/.env
# fill in VITE_MAPTILER_KEY
```

### 4. Load NYC data

```bash
cd backend
.venv\Scripts\python ingestion/load_nyc_neighborhoods.py   # ~30 seconds
.venv\Scripts\python ingestion/nyc_crime.py                # ~3 minutes, 887k records
.venv\Scripts\python -c "import asyncio; from services.scoring import recompute_all_scores; from database import get_db; ..."
```

### 5. Run

```bash
# Terminal 1 — backend
cd backend && .venv\Scripts\python -m uvicorn main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## API Keys

| Key | Where to get it | Free? |
|---|---|---|
| `VITE_MAPTILER_KEY` | [cloud.maptiler.com](https://cloud.maptiler.com) | Yes |
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) | Yes |
| `REDDIT_CLIENT_ID` + `SECRET` | [reddit.com/prefs/apps](https://reddit.com/prefs/apps) | Yes |
| `NYT_API_KEY` | [developer.nytimes.com](https://developer.nytimes.com) | Yes |
| `NEWS_API_KEY` | [newsapi.org](https://newsapi.org) | Free tier |
| `CENSUS_API_KEY` | [api.census.gov/data/key_signup.html](https://api.census.gov/data/key_signup.html) | Yes |
| `SOCRATA_APP_TOKEN` | [data.cityofnewyork.us](https://data.cityofnewyork.us) | Yes |

The app runs without any keys — Gemini falls back to rule-based briefings, news/Reddit sections show empty.

## API Endpoints

```
GET /api/neighborhoods/{city}/geojson?time_bucket=evening
GET /api/safety/{city}/{neighborhood}?time_bucket=evening&traveler_type=solo
GET /api/safety/compare?city=nyc&areas=Harlem,Astoria&time_bucket=morning
GET /api/alerts/{city}
```

## Scoring Model

Each neighborhood gets a composite score per time bucket:

```
composite = (violent × 3.0) + (theft × 1.5) + (property × 1.0)
normalized = composite / 95th_percentile × 100
```

| Score | Band |
|---|---|
| 0–25 | Low |
| 25–50 | Moderate |
| 50–75 | Elevated |
| 75–100 | High |

## Data Sources

- **NYPD Historic Crime Data** — NYC Open Data, dataset `5uac-w243` (887k+ incidents)
- **NYC Neighborhood Tabulation Areas** — dataset `9nt8-h7nd` (262 NTA boundaries)
- **NewsAPI** + **NYT Article Search** — 72-hour news alerts
- **Reddit PRAW** — r/nyc, r/AskNYC community safety signals
- **Census ACS** — population estimates for per-capita rate normalization

## License

MIT
