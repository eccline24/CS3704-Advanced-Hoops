# CS3704 Advanced Hoops: NBA Stats Dashboard

Designed to be an web based platform to display NBA and college basketball statistics in a clear way

---

## Project Structure

```
CS3704-Advanced-Hoops/
├── pytest.ini
├── README.md
├── backend/
│   ├── app.py
│   └── generate_static.py
├── data/
│   ├── data_service.py
│   └── adapters/
│       ├── __init__.py
│       ├── base_adapter.py
│       ├── bbref_adapter.py
│       └── nba_api_adapter.py
├── frontend/
│   ├── index.html
│   └── charts.js
└── tests/
    ├── conftest.py
    ├── test_bbref_adapter.py
    ├── test_nba_api_adapter.py
    ├── test_generate_static.py
    ├── test_app_routes.py
    └── test_integration.py
```

---

## Requirements

- Python 3.10+
- pip

---

## Setup

**1. Clone the repository**
```bash
git clone https://github.com/your-username/CS3704-Advanced-Hoops.git
cd CS3704-Advanced-Hoops
```

**2. Install dependencies**
```bash
pip install flask nba_api basketball-reference-web-scraper pandas pytest
```

---

## Running the App

### Option A: Live Flask Server

Starts a local Flask development server that fetches data from the NBA API on every request.

```bash
cd backend
python app.py
```

Then open your browser to `http://127.0.0.1:5000`.

### Option B: Static Mode (no server needed)

Fetches data once from the NBA API and embeds it directly into `index.html` as JavaScript globals. After running this you can open the HTML file directly in a browser with no server.

```bash
cd backend
python generate_static.py
```

Then open `frontend/index.html` directly in your browser.

---

## API Endpoints

All endpoints are served by the Flask app at `http://127.0.0.1:5000`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/top-players` | Top 10 players by points scored |
| GET | `/api/team-rankings` | Full league standings |
| GET | `/api/player/<name>` | Career stats for a single player |
| GET | `/api/team/<name>` | Roster for a single team |
| GET | `/api/compare/players?player1=X&player2=Y` | Head-to-head player comparison |
| GET | `/api/compare/teams?team1=X&team2=Y` | Head-to-head team comparison |

**Example requests:**
```
GET /api/player/LeBron James
GET /api/team/Boston Celtics
GET /api/compare/players?player1=LeBron James&player2=Stephen Curry
GET /api/compare/teams?team1=Lakers&team2=Celtics
```

---

## Data Sources

The app uses an adapter pattern so the data source can be swapped without changing any other code. The active source is set in `app.py`:

```python
service = DataService(source='nba_api')   # use NBA API
service = DataService(source='bbref')     # use Basketball Reference
```

### NBA API (`nba_api_adapter.py`)
- Pulls live data from nba.com
- Identifies players and teams by numeric ID
- Returns career stats broken down by season
- Stat categories use NBA abbreviations: `PTS`, `AST`, `REB`, etc.

### Basketball Reference (`bbref_adapter.py`)
- Scrapes data from basketball-reference.com
- Identifies teams using a `Team` enum (e.g. `Team.BOSTON_CELTICS`)
- Returns season schedule data as a proxy for team stats
- Stat categories use full names: `points`, `assists`, `rebounds`, etc.

---

## Running Tests

From the project root:

```bash
pytest
```

Run a specific test file:
```bash
pytest tests/test_bbref_adapter.py
pytest tests/test_integration.py
```

Run with coverage:
```bash
pip install pytest-cov
pytest --cov=data --cov=backend
```

All external API calls are mocked — the test suite runs fully offline and completes in under 5 seconds.

### Test Coverage

| File | What is tested |
|------|---------------|
| `test_bbref_adapter.py` | All BBRefAdapter methods, team enum lookup, error handling |
| `test_nba_api_adapter.py` | All NBAApiAdapter methods, player/team ID lookup, DataFrame mocking |
| `test_generate_static.py` | `build_data_block` output, `inject` replace/anchor/error paths |
| `test_app_routes.py` | All Flask routes, 400 on missing params, 500 on exceptions |
| `test_integration.py` | Adapter to static pipeline, comparison call chain, Flask to service round-trip |

---

## AI Usage

This project used Claude AI (claude.ai) for the following:

- `base_adapter.py` — AI provided the abstract base class structure
- `bbref_adapter.py` — AI provided the file structure with TODOs; student implemented methods
- `nba_api_adapter.py` — AI provided the file structure with TODOs; student implemented methods
- `tests/` — AI generated all test files based on student-provided source code and prompts

All AI-generated code is documented with the prompt used at the top of the relevant file.