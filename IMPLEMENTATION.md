# Ethan Avery

## Features Implemented

### Adapters: Python Data layer
Files:
base_adapter.py
nba_api_adapter.py
bbref_adapter.pu
data_service.py

The Data layer uses the adapter design patter to implement two external data sources. These are from the nba_api package, which pulls from nba.com, and from the basketball_reference_web_scraper package, which scrapes the Basketball reference website.

The Base Adapter class defines an abstract base class with methods that all adapters have to implement. These involve getting player and team stats, comparisons, and rankings.

The NBA api and BBref adapters implement each of these methods using their own packages.

The data service is a entry point, which excepts some source parameter and creates the appropriate adapter so that the rest of the application doesn't need to know which data source is being used

### Does it do what was expected

Yes, so far the adapter method successfully works as intended.

## AI Tools Used

Claude AI was used in general to give at first a general idea of how the project should be structured, and also gave file suggestions. From there, it was used to give structure to files with TODOs, and sometimes just generate full files. It cases where full files were generated, no code has currently been modified from what was given. Where just the strucure was given, some small extra comments were added in various spots, and the methods themselves were implemented without changing the structure of the file. It is noted in files when extra help is used when struggling. Prompts are given at the top of each file of what was used to help create each file. These prompts were used before those to help give context to the problem:

I am looking to create a web application that aims to implement multiple online basketball sources and combine stats into one spot. I would like to start creating this from relatively scratch. What is a good starting point for this?

I would like to focus on obtaining data for now. What would this look if I wanted to start coding this? The libraries I would like to use are in python.



# Evan Cline

## Features Implemented

### Frontend Features
I started to implemented the frontend for our web app. The index.html file is the home page for the application and will display general staistics from the data adapters, with links to other frontend pages that will be developed.

### Does it do what is expected
Not quite yet, the file still needs to be implemented to be compatible with and "talk to" the data adapter python files. It also needs to add links to the other feature frontend files.

## AI Tools Used
I used ChatGPT to help me generate the index.html file. The code was slightly modified from what was given, just changing variable names to reflect our context. 

Prompt used: "I am creating a college basketball web application that displays college basketball statistics from different API data sources. Could you help me start on the frontend by creating an index.html file for the home page of the web application"

# Ragav

## Features Implemented

### Frontend Charts and Static Data Pipeline
Files:
frontend/charts.js
frontend/index.html
backend/generate_static.py

I added interactive bar charts to the home page using Chart.js. The first chart displays the top 10 NBA scorers by total points, and the second displays all 30 teams ranked by win percentage. Both charts are rendered dynamically from real data.

A dual-mode data loading system was implemented in `charts.js`: on page load it checks for `window.__TOP_PLAYERS__` and `window.__TEAM_RANKINGS__` (pre-baked static data), and falls back to fetching from the live `/api/top-players` and `/api/team-rankings` Flask endpoints if those globals are not present. This means the page works both when opened directly as a static file and when served through the Flask backend.

`generate_static.py` was written to support the static file mode. It fetches live data from the NBA API via the existing `DataService`, serializes it to JSON, and injects it into `index.html` between `<!-- BEGIN_STATIC_DATA -->` and `<!-- END_STATIC_DATA -->` sentinel markers. On subsequent runs it replaces the existing block rather than duplicating it, using a regex replacement. The script also supports a first-run mode where it inserts the block before a `<!-- DATA_INJECTION_POINT -->` anchor comment.

The `index.html` file was updated to include the Chart.js CDN script tag, the two `<canvas>` elements for the charts, the `DATA_INJECTION_POINT` anchor, and the `<script src="charts.js">` tag.

### Does it do what was expected

Yes. Running `generate_static.py` once embeds current NBA data into `index.html` so it can be opened directly in a browser without a server. When the Flask server is running instead, `charts.js` falls back to the live API endpoints automatically. Both paths render the same two charts correctly.

## AI Tools Used

Claude AI was used to help design and implement the static data injection pipeline and the dual-mode loading logic in `charts.js`.

Prompt used:
"How can I embed live NBA API data into a static HTML file so it works without a server, while also supporting live API calls when a Flask backend is running?"

Modifications made:
The injection script and sentinel marker approach were adapted to fit the existing `index.html` structure. The fallback fetch logic in `charts.js` was written to match the exact field names (`PLAYER`, `PTS`, `TeamName`, `WinPCT`) returned by the NBA API adapter.


# Ramya

## Features Implemented

### Code Comments, Backend Support, and Documentation
Files:
backend/app.py
IMPLEMENTATION.md

Added inline comments throughout the backend and frontend files to explain the purpose of functions, routes, and data flow. Contributed to backend development and helped maintain the project documentation in `IMPLEMENTATION.md`.

### Does it do what was expected

Yes. The comments improve readability and make it easier for teammates to understand the codebase.

## AI Tools Used

No AI tools noted for this section.


# Sharlette Vijoy

## Features Implemented

### Backend API Endpoints
Files:
backend/app.py

The backend is built using Flask and serves as the bridge between the frontend and the data adapter layer. It exposes six REST API
endpoints that the frontend can call to retrieve live basketball data from the NBA API adapter.

Four REST API endpoints were added to the Flask backend to expose player and team data to the frontend:

- GET /api/player/<name> - accepts a player name in the URL and returns that player's stats by calling get_player_stats() on the data service.
- GET /api/team/<name> - accepts a team name in the URL and returns that team's stats by calling get_team_stats().
- GET /api/compare/players?player1=X&player2=Y - accepts two player names as query parameters and returns a side-by-side comparison by calling get_player_comparison(). Returns a 400 error if fewer than two players are provided.
- GET /api/compare/teams?team1=X&team2=Y - accepts two team names as query parameters and returns a side-by-side comparison by calling get_team_comparison(). Returns a 400 error if fewer than two teams are provided.

All endpoints return JSON and handle exceptions by returning a descriptive error message rather than crashing.

### Does it do what was expected

Yes. They connect directly to the existing DataService adapter layer, so no changes to the data layer were needed. The endpoints are ready for the frontend to integrate in PM5.

## AI Tools Used

Claude AI was used to help implement these endpoints.

Prompt used:
"Can you write the Flask routes for player stats, team stats, player comparison, and team comparison endpoints that connect to the existing DataService adapter?"

Modifications made:
The basic Flask server structure and static file serving were already present in app.py. The four new endpoints (/api/player, /api/team, /api/compare/players, /api/compare/teams) were added and adapted to match the existing DataService method names `request` was also added to the Flask import to support query parameters in the comparison endpoints. 

