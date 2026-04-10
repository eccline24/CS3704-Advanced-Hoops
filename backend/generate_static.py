import sys
import os
import json
import re

# Allow importing from data/ directory (same as app.py)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data'))

from data_service import DataService

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# Resolve the path to index.html relative to this script's location.
HTML_PATH = os.path.join(SCRIPT_DIR, '..', 'frontend', 'index.html')

# Sentinel comments mark the start and end of the injected data block inside index.html.
# This allows the script to replace the block on subsequent runs without duplicating it.
SENTINEL_START = '<!-- BEGIN_STATIC_DATA -->'
SENTINEL_END = '<!-- END_STATIC_DATA -->'

# On the very first run, this anchor comment tells the script where to insert the data block.
INJECTION_ANCHOR = '<!-- DATA_INJECTION_POINT -->'

# Builds the <script> block that embeds JSON data directly into the HTML as global variables.
# Using window.__TOP_PLAYERS__ and window.__TEAM_RANKINGS__ lets charts.js read the data
# instantly without making a network request to the Flask backend.
def build_data_block(top_players, team_rankings):
    # separators=(',', ':') produces compact JSON with no extra whitespace.
    top_json = json.dumps(top_players, separators=(',', ':'))
    rankings_json = json.dumps(team_rankings, separators=(',', ':'))
    return (
        f'{SENTINEL_START}\n'
        f'    <script>\n'
        f'        window.__TOP_PLAYERS__ = {top_json};\n'
        f'        window.__TEAM_RANKINGS__ = {rankings_json};\n'
        f'    </script>\n'
        f'    {SENTINEL_END}'
    )

def inject(html, data_block):
    # If a previous data block exists, replace it using a regex that matches everything
    # between the sentinel comments (re.DOTALL makes . match newlines too).
    if SENTINEL_START in html:
        pattern = re.compile(
            re.escape(SENTINEL_START) + r'.*?' + re.escape(SENTINEL_END),
            re.DOTALL
        )
        return pattern.sub(data_block, html)

    # First run: no existing block, so insert before the injection anchor placeholder.
    if INJECTION_ANCHOR in html:
        return html.replace(INJECTION_ANCHOR, data_block + '\n    ' + INJECTION_ANCHOR)

    raise RuntimeError(
        f"Could not find '{INJECTION_ANCHOR}' or '{SENTINEL_START}' in index.html. "
        "Make sure frontend/index.html has the <!-- DATA_INJECTION_POINT --> comment."
    )

def main():
    service = DataService(source='nba_api')

    print("Fetching data from NBA API...")
    try:
        top_players = service.get_top_players('PTS', limit=10)
        team_rankings = service.get_team_rankings()
    except Exception as e:
        print(f"ERROR: Failed to fetch data from NBA API: {e}")
        sys.exit(1)

    data_block = build_data_block(top_players, team_rankings)

    # Read the current HTML, inject the new data block, then write it back.
    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    updated_html = inject(html, data_block)

    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(updated_html)

    print(f"Done. Embedded {len(top_players)} players and {len(team_rankings)} teams into frontend/index.html.")
    print("You can now open frontend/index.html directly in a browser.")

if __name__ == '__main__':
    main()
