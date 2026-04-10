import sys
import os
import json
import re

# Allow importing from data/ directory (same as app.py)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data'))

from data_service import DataService

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(SCRIPT_DIR, '..', 'frontend', 'index.html')

SENTINEL_START = '<!-- BEGIN_STATIC_DATA -->'
SENTINEL_END = '<!-- END_STATIC_DATA -->'
INJECTION_ANCHOR = '<!-- DATA_INJECTION_POINT -->'

def build_data_block(top_players, team_rankings):
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
    # Replace existing block if present
    if SENTINEL_START in html:
        pattern = re.compile(
            re.escape(SENTINEL_START) + r'.*?' + re.escape(SENTINEL_END),
            re.DOTALL
        )
        return pattern.sub(data_block, html)

    # First run: insert before the injection anchor
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

    with open(HTML_PATH, 'r', encoding='utf-8') as f:
        html = f.read()

    updated_html = inject(html, data_block)

    with open(HTML_PATH, 'w', encoding='utf-8') as f:
        f.write(updated_html)

    print(f"Done. Embedded {len(top_players)} players and {len(team_rankings)} teams into frontend/index.html.")
    print("You can now open frontend/index.html directly in a browser.")

if __name__ == '__main__':
    main()
