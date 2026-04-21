# coding: utf-8
"""
Unit tests for generate_static.py

AI Usage:
  Tool: Claude AI
  Prompt : "I have two functions in a function called generate_static.py. build_data_block(top_players, team_rankings) 
takes two lists and returns a string containing a tag with 
window.__TOP_PLAYERS__ and window.__TEAM_RANKINGS__ as JSON globals, 
wrapped between comments called SENTINEL_START and SENTINEL_END. 
inject(html, data_block) either replaces an existing block between those sentinels 
using regex, or inserts before a comment called INJECTION_ANCHOR on the first run, 
or raises a RuntimeError if neither marker is found. Generate pytest unit tests 
for both functions covering all paths."
"""

import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))

from generate_static import (
    build_data_block,
    inject,
    SENTINEL_START,
    SENTINEL_END,
    INJECTION_ANCHOR,
)


# ---------------------------------------------------------------------------
# build_data_block
# ---------------------------------------------------------------------------

class TestBuildDataBlock:
    def test_contains_sentinel_markers(self):
        block = build_data_block([], [])
        assert SENTINEL_START in block
        assert SENTINEL_END in block

    def test_embeds_top_players_json(self):
        players = [{'PLAYER': 'LeBron James', 'PTS': 30}]
        block = build_data_block(players, [])
        assert json.dumps(players, separators=(',', ':')) in block

    def test_embeds_team_rankings_json(self):
        rankings = [{'TeamName': 'Celtics', 'WINS': 60}]
        block = build_data_block([], rankings)
        assert json.dumps(rankings, separators=(',', ':')) in block

    def test_uses_compact_json_no_spaces(self):
        # compact separators mean no space after colon or comma
        block = build_data_block([{'a': 1}], [{'b': 2}])
        assert ': ' not in block
        assert ', ' not in block

    def test_script_tag_present(self):
        block = build_data_block([], [])
        assert '<script>' in block
        assert '</script>' in block

    def test_window_globals_present(self):
        block = build_data_block([], [])
        assert 'window.__TOP_PLAYERS__' in block
        assert 'window.__TEAM_RANKINGS__' in block


# ---------------------------------------------------------------------------
# inject - replacement path (sentinel already present)
# ---------------------------------------------------------------------------

class TestInjectReplacement:
    def _html_with_sentinel(self, old_content='old data'):
        return (
            '<html>\n'
            '  ' + SENTINEL_START + '\n'
            '  ' + old_content + '\n'
            '  ' + SENTINEL_END + '\n'
            '</html>'
        )

    def test_replaces_existing_block(self):
        html = self._html_with_sentinel('old data')
        new_block = build_data_block([{'PTS': 99}], [])
        result = inject(html, new_block)

        assert 'old data' not in result
        assert 'PTS' in result

    def test_sentinel_appears_exactly_once_after_replace(self):
        html = self._html_with_sentinel()
        new_block = build_data_block([], [])
        result = inject(html, new_block)

        assert result.count(SENTINEL_START) == 1
        assert result.count(SENTINEL_END) == 1

    def test_surrounding_html_preserved(self):
        html = self._html_with_sentinel()
        result = inject(html, build_data_block([], []))

        assert '<html>' in result
        assert '</html>' in result


# ---------------------------------------------------------------------------
# inject - first-run path (anchor present, no sentinel yet)
# ---------------------------------------------------------------------------

class TestInjectAnchor:
    def _html_with_anchor(self):
        return '<html>\n  ' + INJECTION_ANCHOR + '\n</html>'

    def test_inserts_before_anchor(self):
        html = self._html_with_anchor()
        block = build_data_block([], [])
        result = inject(html, block)

        assert SENTINEL_START in result
        assert INJECTION_ANCHOR in result

    def test_anchor_comes_after_injected_block(self):
        html = self._html_with_anchor()
        block = build_data_block([], [])
        result = inject(html, block)

        start_idx = result.index(SENTINEL_START)
        anchor_idx = result.index(INJECTION_ANCHOR)
        assert start_idx < anchor_idx


# ---------------------------------------------------------------------------
# inject - error path (neither sentinel nor anchor)
# ---------------------------------------------------------------------------

class TestInjectError:
    def test_raises_runtime_error_when_no_markers(self):
        plain_html = '<html><body>No markers here</body></html>'
        with pytest.raises(RuntimeError, match="Could not find"):
            inject(plain_html, build_data_block([], []))