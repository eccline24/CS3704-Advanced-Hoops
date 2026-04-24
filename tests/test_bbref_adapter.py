"""
Unit tests for bbref_adapter.py.
AI Usage:
  Tool: Claude AI. Used it to generate this test file
  Prompt: "I have a BBRefAdapter class that wraps the basketball_reference_web_scraper 
library. It has these methods: _find_team_enum(team_name) which converts a 
string to a Team enum, get_player_stats(player_name) which calls client.search(), 
get_team_stats(team_name) which calls client.team_schedule_for_month(), 
get_player_comparison(player1, player2), get_team_comparison(team1, team2), 
get_team_rankings() which calls client.standings(), and get_top_players(stat_category, limit) 
which calls client.players_season_totals() and sorts the results. All methods 
return dicts with an 'error' key on failure. Generate pytest unit tests for 
all client calls. At least one test per method."
"""

import pytest
from unittest.mock import patch, MagicMock
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data'))

from adapters.bbref_adapter import BBRefAdapter
from basketball_reference_web_scraper.data import Team


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def adapter():
    return BBRefAdapter()


# ---------------------------------------------------------------------------
# _find_team_enum
# ---------------------------------------------------------------------------

class TestFindTeamEnum:
    def test_valid_team_returns_enum(self, adapter):
        """Exact match (case-insensitive, spaces vs underscores)."""
        result = adapter._find_team_enum("golden state warriors")
        assert result == Team.GOLDEN_STATE_WARRIORS

    def test_case_insensitive_match(self, adapter):
        """Upper-case input still resolves."""
        result = adapter._find_team_enum("BOSTON CELTICS")
        assert result == Team.BOSTON_CELTICS

    def test_invalid_team_returns_none(self, adapter):
        """Bogus team name returns None, not an exception."""
        result = adapter._find_team_enum("Springfield Atoms")
        assert result is None

    def test_empty_string_returns_none(self, adapter):
        result = adapter._find_team_enum("")
        assert result is None

    def test_partial_name_returns_enum(self, adapter):
        """Substring of a team's normalized name resolves via partial match."""
        result = adapter._find_team_enum("golden state")
        assert result == Team.GOLDEN_STATE_WARRIORS

    def test_partial_city_name_returns_enum(self, adapter):
        result = adapter._find_team_enum("boston")
        assert result == Team.BOSTON_CELTICS

    def test_exact_match_preferred_over_partial(self, adapter):
        """Exact match wins even when another team's name contains the query as a substring."""
        result = adapter._find_team_enum("los angeles lakers")
        assert result == Team.LOS_ANGELES_LAKERS


# ---------------------------------------------------------------------------
# get_player_stats
# ---------------------------------------------------------------------------

class TestGetPlayerStats:
    @patch('adapters.bbref_adapter.client')
    def test_found_player_returns_data(self, mock_client, adapter):
        mock_client.search.return_value = {
            'players': [{'name': 'LeBron James', 'identifier': 'jamesle01'}]
        }
        result = adapter.get_player_stats("LeBron James")

        assert result['player'] == "LeBron James"
        assert result['source'] == "basketball_reference"
        assert 'data' in result
        assert result['data']['name'] == 'LeBron James'

    @patch('adapters.bbref_adapter.client')
    def test_player_not_found_returns_error(self, mock_client, adapter):
        mock_client.search.return_value = {'players': []}
        result = adapter.get_player_stats("Fake Player")

        assert 'error' in result

    @patch('adapters.bbref_adapter.client')
    def test_none_response_returns_error(self, mock_client, adapter):
        mock_client.search.return_value = None
        result = adapter.get_player_stats("LeBron James")

        assert 'error' in result

    @patch('adapters.bbref_adapter.client')
    def test_exception_returns_error_dict(self, mock_client, adapter):
        mock_client.search.side_effect = Exception("network timeout")
        result = adapter.get_player_stats("LeBron James")

        assert 'error' in result
        assert "network timeout" in result['error']


# ---------------------------------------------------------------------------
# get_team_stats
# ---------------------------------------------------------------------------

class TestGetTeamStats:
    @patch('adapters.bbref_adapter.client')
    def test_valid_team_returns_schedule(self, mock_client, adapter):
        mock_client.team_schedule_for_month.return_value = [
            {'date': '2025-01-01', 'opponent': 'lakers'}
        ]
        result = adapter.get_team_stats("boston celtics")

        assert result['team'] == "boston celtics"
        assert result['source'] == "basketball_reference"
        assert isinstance(result['schedule'], list)
        assert len(result['schedule']) == 1

    def test_invalid_team_returns_error(self, adapter):
        result = adapter.get_team_stats("Springfield Atoms")
        assert 'error' in result

    @patch('adapters.bbref_adapter.client')
    def test_api_exception_returns_error(self, mock_client, adapter):
        mock_client.team_schedule_for_month.side_effect = Exception("bbref down")
        result = adapter.get_team_stats("boston celtics")

        assert 'error' in result


# ---------------------------------------------------------------------------
# get_player_comparison
# ---------------------------------------------------------------------------

class TestGetPlayerComparison:
    @patch('adapters.bbref_adapter.client')
    def test_comparison_structure(self, mock_client, adapter):
        mock_client.search.return_value = {
            'players': [{'name': 'Player', 'identifier': 'abc'}]
        }
        result = adapter.get_player_comparison("LeBron James", "Stephen Curry")

        assert result['comparison'] == 'player'
        assert result['source'] == 'basketball_reference'
        assert 'LeBron James' in result
        assert 'Stephen Curry' in result

    @patch('adapters.bbref_adapter.client')
    def test_one_player_missing_still_returns_structure(self, mock_client, adapter):
        """Even if one lookup fails, the comparison dict is still returned."""
        def side_effect(term):
            if term == "LeBron James":
                return {'players': [{'name': 'LeBron James', 'identifier': 'jamesle01'}]}
            return {'players': []}

        mock_client.search.side_effect = side_effect
        result = adapter.get_player_comparison("LeBron James", "Ghost Player")

        assert 'LeBron James' in result
        assert 'Ghost Player' in result
        assert 'error' in result['Ghost Player']


# ---------------------------------------------------------------------------
# get_team_comparison
# ---------------------------------------------------------------------------

class TestGetTeamComparison:
    @patch('adapters.bbref_adapter.client')
    def test_comparison_structure(self, mock_client, adapter):
        mock_client.team_schedule_for_month.return_value = []
        result = adapter.get_team_comparison("boston celtics", "los angeles lakers")

        assert result['comparison'] == 'team'
        assert result['source'] == 'basketball_reference'
        assert 'boston celtics' in result
        assert 'los angeles lakers' in result


# ---------------------------------------------------------------------------
# get_team_rankings
# ---------------------------------------------------------------------------

class TestGetTeamRankings:
    @patch('adapters.bbref_adapter.client')
    def test_returns_list(self, mock_client, adapter):
        mock_client.standings.return_value = [
            {'team': 'Boston Celtics', 'wins': 60}
        ]
        result = adapter.get_team_rankings()

        assert isinstance(result, list)
        assert result[0]['team'] == 'Boston Celtics'

    @patch('adapters.bbref_adapter.client')
    def test_exception_returns_list_with_error(self, mock_client, adapter):
        mock_client.standings.side_effect = Exception("timeout")
        result = adapter.get_team_rankings()

        assert isinstance(result, list)
        assert 'error' in result[0]


# ---------------------------------------------------------------------------
# get_top_players
# ---------------------------------------------------------------------------

class TestGetTopPlayers:
    @patch('adapters.bbref_adapter.client')
    def test_returns_correct_limit(self, mock_client, adapter):
        mock_client.players_season_totals.return_value = [
            {'player': f'Player{i}', 'points': 100 - i} for i in range(20)
        ]
        result = adapter.get_top_players(stat_category='points', limit=5)

        assert len(result) == 5

    @patch('adapters.bbref_adapter.client')
    def test_sorted_descending(self, mock_client, adapter):
        mock_client.players_season_totals.return_value = [
            {'player': 'A', 'points': 500},
            {'player': 'B', 'points': 1500},
            {'player': 'C', 'points': 1000},
        ]
        result = adapter.get_top_players(stat_category='points', limit=3)

        assert result[0]['points'] == 1500
        assert result[1]['points'] == 1000
        assert result[2]['points'] == 500

    @patch('adapters.bbref_adapter.client')
    def test_missing_stat_key_treated_as_zero(self, mock_client, adapter):
        """Players missing the stat key should sort below players who have it."""
        mock_client.players_season_totals.return_value = [
            {'player': 'A', 'points': 100},
            {'player': 'B'},           # no 'points' key
        ]
        result = adapter.get_top_players(stat_category='points', limit=2)
        assert result[0]['player'] == 'A'

    @patch('adapters.bbref_adapter.client')
    def test_exception_returns_list_with_error(self, mock_client, adapter):
        mock_client.players_season_totals.side_effect = Exception("boom")
        result = adapter.get_top_players()

        assert isinstance(result, list)
        assert 'error' in result[0]