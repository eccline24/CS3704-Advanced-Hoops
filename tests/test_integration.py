"""
Integration tests

AI Usage
  Tool: Claude AI
  Prompt: "I have a project with a BBRefAdapter and NBAApiAdapter that both implement 
get_player_stats, get_team_stats, get_player_comparison, get_team_comparison, 
get_team_rankings, and get_top_players. I also have build_data_block and inject 
functions in generate_static.py, and a Flask app with a service layer in between. 
Write integration tests that chain multiple components together"
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import pandas as pd
import sys, os
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data'))

from adapters.bbref_adapter import BBRefAdapter
from adapters.nba_api_adapter import NBAApiAdapter
from generate_static import build_data_block, inject, SENTINEL_START, SENTINEL_END, INJECTION_ANCHOR


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _make_df(data):
    return pd.DataFrame(data)


# ===========================================================================
# INTEGRATION 1
# BBRefAdapter.get_top_players + get_team_rankings -> build_data_block -> inject
# ===========================================================================

class TestBBRefToStaticPipeline:
    @patch('adapters.bbref_adapter.client')
    def test_full_pipeline_produces_valid_html(self, mock_client):
        mock_client.players_season_totals.return_value = [
            {'first_name': 'LeBron', 'last_name': 'James', 'points': 2000},
            {'first_name': 'Stephen', 'last_name': 'Curry', 'points': 1800},
        ]
        mock_client.standings.return_value = [
            {'team': 'Boston Celtics', 'wins': 60},
            {'team': 'Los Angeles Lakers', 'wins': 55},
        ]

        adapter = BBRefAdapter()
        top_players = adapter.get_top_players(stat_category='points', limit=2)
        team_rankings = adapter.get_team_rankings()

        assert len(top_players) == 2
        assert top_players[0]['points'] == 2000
        assert team_rankings[0]['team'] == 'Boston Celtics'

        block = build_data_block(top_players, team_rankings)
        assert 'LeBron' in block
        assert 'Boston Celtics' in block

        html = '<html><head>' + INJECTION_ANCHOR + '</head><body></body></html>'
        result = inject(html, block)

        assert SENTINEL_START in result
        assert SENTINEL_END in result
        assert 'LeBron' in result
        assert 'Boston Celtics' in result
        assert '<body>' in result

    @patch('adapters.bbref_adapter.client')
    def test_second_run_replaces_old_data(self, mock_client):
        mock_client.players_season_totals.return_value = [
            {'first_name': 'Old', 'last_name': 'Player', 'points': 500}
        ]
        mock_client.standings.return_value = []

        adapter = BBRefAdapter()
        old_players = adapter.get_top_players(stat_category='points', limit=1)
        old_block = build_data_block(old_players, [])

        html = '<html><head>' + INJECTION_ANCHOR + '</head></html>'
        html_after_first_run = inject(html, old_block)

        mock_client.players_season_totals.return_value = [
            {'first_name': 'New', 'last_name': 'Player', 'points': 999}
        ]
        new_players = adapter.get_top_players(stat_category='points', limit=1)
        new_block = build_data_block(new_players, [])
        html_after_second_run = inject(html_after_first_run, new_block)

        assert html_after_second_run.count(SENTINEL_START) == 1
        assert 'Old' not in html_after_second_run
        assert 'New' in html_after_second_run


# ===========================================================================
# INTEGRATION 2
# NBAApiAdapter.get_player_comparison chains _find_player_id + get_player_stats x2
# ===========================================================================

class TestNBAAdapterComparisonChain:
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.playercareerstats')
    @patch('adapters.nba_api_adapter.players')
    def test_comparison_uses_real_adapter_methods(
        self, mock_players, mock_career, mock_time
    ):
        mock_players.get_players.return_value = [
            {'full_name': 'LeBron James', 'id': 2544},
            {'full_name': 'Stephen Curry', 'id': 201939},
        ]
        df = _make_df([{
            'SEASON_ID': '2023-24', 'GP': 71, 'PTS': 25.7, 'REB': 7.3,
            'AST': 8.3, 'STL': 1.3, 'BLK': 0.6, 'TOV': 3.5,
            'FG_PCT': 0.54, 'FG3_PCT': 0.41, 'FT_PCT': 0.75
        }])
        mock_career.PlayerCareerStats.return_value.get_data_frames.return_value = [df]

        adapter = NBAApiAdapter()
        result = adapter.get_player_comparison("LeBron James", "Stephen Curry")

        assert result['comparison'] == 'player'
        assert result['source'] == 'nba_api'
        assert result['LeBron James']['source'] == 'nba_api'
        assert result['Stephen Curry']['source'] == 'nba_api'
        assert isinstance(result['LeBron James']['stats'], list)
        assert mock_career.PlayerCareerStats.call_count == 2

    @patch('adapters.nba_api_adapter.players')
    def test_comparison_with_one_unknown_player(self, mock_players):
        mock_players.get_players.return_value = [
            {'full_name': 'LeBron James', 'id': 2544}
        ]

        with patch('adapters.nba_api_adapter.time'), \
             patch('adapters.nba_api_adapter.playercareerstats') as mock_career:
            df = _make_df([{
                'SEASON_ID': '2023-24', 'GP': 71, 'PTS': 25.7, 'REB': 7.3,
                'AST': 8.3, 'STL': 1.3, 'BLK': 0.6, 'TOV': 3.5,
                'FG_PCT': 0.54, 'FG3_PCT': 0.41, 'FT_PCT': 0.75
            }])
            mock_career.PlayerCareerStats.return_value.get_data_frames.return_value = [df]

            adapter = NBAApiAdapter()
            result = adapter.get_player_comparison("LeBron James", "Ghost Player")

        assert 'error' not in result['LeBron James']
        assert 'error' in result['Ghost Player']


# ===========================================================================
# INTEGRATION 3
# Flask route -> service mock -> response -> build_data_block -> inject
# ===========================================================================

class TestFlaskToAdapterIntegration:
    @pytest.fixture
    def flask_client(self):
        import app as flask_app
        mock_service = MagicMock()
        with patch.object(flask_app, 'service', mock_service):
            flask_app.app.config['TESTING'] = True
            with flask_app.app.test_client() as c:
                yield c, mock_service

    def test_compare_players_route_to_service(self, flask_client):
        c, mock_service = flask_client
        mock_service.get_player_comparison.return_value = {
            'comparison': 'player',
            'source': 'nba_api',
            'LeBron James': {'stats': [{'PTS': 25}]},
            'Stephen Curry': {'stats': [{'PTS': 28}]},
        }

        resp = c.get('/api/compare/players?player1=LeBron James&player2=Stephen Curry')
        assert resp.status_code == 200

        data = json.loads(resp.data)
        mock_service.get_player_comparison.assert_called_once_with(
            'LeBron James', 'Stephen Curry'
        )
        assert 'LeBron James' in data
        assert 'Stephen Curry' in data
        assert data['LeBron James']['stats'][0]['PTS'] == 25

    def test_top_players_and_build_block_round_trip(self, flask_client):
        c, mock_service = flask_client
        mock_service.get_top_players.return_value = [
            {'PLAYER': 'LeBron James', 'TEAM': 'LAL', 'PTS': 30},
            {'PLAYER': 'Stephen Curry', 'TEAM': 'GSW', 'PTS': 28},
        ]
        mock_service.get_team_rankings.return_value = [
            {'TeamName': 'Celtics', 'WINS': 60}
        ]

        players_resp = c.get('/api/top-players')
        rankings_resp = c.get('/api/team-rankings')
        assert players_resp.status_code == 200
        assert rankings_resp.status_code == 200

        top_players = json.loads(players_resp.data)
        team_rankings = json.loads(rankings_resp.data)

        block = build_data_block(top_players, team_rankings)
        html = '<html><head>' + INJECTION_ANCHOR + '</head></html>'
        result = inject(html, block)

        assert 'LeBron James' in result
        assert 'Stephen Curry' in result
        assert 'Celtics' in result
        assert result.count(SENTINEL_START) == 1


# ===========================================================================
# INTEGRATION 4
# DataService caching — repeat calls hit the cache, not the adapter.
# Verifies the @cached decorator wired in data_service.py correctly skips
# the adapter on cache hits, which is what makes the dashboard reloads fast
# and what prevents the NBA API rate-limit sleeps from firing twice.
# ===========================================================================

class TestDataServiceCaching:
    def test_repeat_call_uses_cache(self):
        from unittest.mock import patch, MagicMock
        from data_service import DataService

        with patch('data_service.NBAApiAdapter') as mock_adapter_cls:
            mock_adapter = MagicMock()
            mock_adapter.get_top_players.return_value = [
                {'PLAYER': 'LeBron James', 'PTS': 30}
            ]
            mock_adapter_cls.return_value = mock_adapter

            service = DataService(source='nba_api')

            first = service.get_top_players('PTS', limit=10)
            second = service.get_top_players('PTS', limit=10)

            assert first == second
            # Adapter hit exactly once despite two service calls
            assert mock_adapter.get_top_players.call_count == 1

    def test_distinct_args_skip_cache(self):
        from unittest.mock import patch, MagicMock
        from data_service import DataService

        with patch('data_service.NBAApiAdapter') as mock_adapter_cls:
            mock_adapter = MagicMock()
            mock_adapter.get_top_players.side_effect = lambda stat, limit: [
                {'stat': stat, 'limit': limit}
            ]
            mock_adapter_cls.return_value = mock_adapter

            service = DataService(source='nba_api')
            service.get_top_players('PTS', limit=10)
            service.get_top_players('REB', limit=10)

            assert mock_adapter.get_top_players.call_count == 2

    def test_clear_cache_forces_adapter_call(self):
        from unittest.mock import patch, MagicMock
        from data_service import DataService

        with patch('data_service.NBAApiAdapter') as mock_adapter_cls:
            mock_adapter = MagicMock()
            mock_adapter.get_team_rankings.return_value = [{'TeamName': 'Celtics'}]
            mock_adapter_cls.return_value = mock_adapter

            service = DataService(source='nba_api')
            service.get_team_rankings()
            service.clear_cache()
            service.get_team_rankings()

            assert mock_adapter.get_team_rankings.call_count == 2