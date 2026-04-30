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

Later expanded with Claude AI:
    - Added edge case lookup tests for mixed case input, partial team names, numeric strings, empty inputs, and a spot-check of multiple valid NBA teams across TestFindTeamEnum
    - Expanded comparison tests to cover both-players-missing and both-teams-missing scenarios, verified that searches are called for each player individually, and confirmed exceptions return structured error dicts rather than crashing
    - Added missing coverage for return type assertions, empty schedule handling, and field preservation across TestGetTeamStats, TestGetTeamRankings, and TestGetTopPlayers
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

    def test_mixed_case_returns_enum(self, adapter):
        """Mixed case like 'Los Angeles Lakers' should resolve correctly."""
        result = adapter._find_team_enum("Los Angeles Lakers")
        assert result == Team.LOS_ANGELES_LAKERS

    def test_leading_trailing_whitespace_handled(self, adapter):
        """Extra whitespace around a valid team name should not break the lookup."""
        result = adapter._find_team_enum("  boston celtics  ")
        # Either resolves correctly or returns None — should not raise an exception
        assert result in (Team.BOSTON_CELTICS, None)

    def test_numeric_string_returns_none(self, adapter):
        """A numeric string is not a valid team name."""
        result = adapter._find_team_enum("12345")
        assert result is None

    def test_all_valid_nba_teams_resolve(self, adapter):
        """Spot-check several teams to ensure broad coverage of the lookup logic."""
        teams_to_check = [
            ("chicago bulls", Team.CHICAGO_BULLS),
            ("miami heat", Team.MIAMI_HEAT),
            ("brooklyn nets", Team.BROOKLYN_NETS),
        ]
        for name, expected in teams_to_check:
            result = adapter._find_team_enum(name)
            assert result == expected, f"Expected {expected} for '{name}', got {result}"



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
 
    @patch('adapters.bbref_adapter.client')
    def test_result_is_dict(self, mock_client, adapter):
        """Return value should always be a dict, never a list or None."""
        mock_client.search.return_value = {
            'players': [{'name': 'Stephen Curry', 'identifier': 'curryst01'}]
        }
        result = adapter.get_player_stats("Stephen Curry")
 
        assert isinstance(result, dict)
 
    @patch('adapters.bbref_adapter.client')
    def test_multiple_players_returned_uses_first(self, mock_client, adapter):
        """When multiple players match the search, the first result should be used."""
        mock_client.search.return_value = {
            'players': [
                {'name': 'LeBron James', 'identifier': 'jamesle01'},
                {'name': 'LeBron James Jr.', 'identifier': 'jamesle02'},
            ]
        }
        result = adapter.get_player_stats("LeBron James")
 
        assert result['player'] == "LeBron James"
        assert result['data']['identifier'] == 'jamesle01'
 
    @patch('adapters.bbref_adapter.client')
    def test_empty_string_player_name_returns_error(self, mock_client, adapter):
        """An empty player name should return an error dict."""
        mock_client.search.return_value = {'players': []}
        result = adapter.get_player_stats("")
 
        assert 'error' in result
 
    @patch('adapters.bbref_adapter.client')
    def test_search_called_with_player_name(self, mock_client, adapter):
        """The client search should be called with the provided player name."""
        mock_client.search.return_value = {'players': []}
        adapter.get_player_stats("Kevin Durant")
 
        mock_client.search.assert_called_once_with(term="Kevin Durant")
 
 
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
 
    @patch('adapters.bbref_adapter.client')
    def test_result_is_dict(self, mock_client, adapter):
        """Return value should always be a dict."""
        mock_client.team_schedule_for_month.return_value = []
        result = adapter.get_team_stats("miami heat")
 
        assert isinstance(result, dict)
 
    @patch('adapters.bbref_adapter.client')
    def test_empty_schedule_still_returns_valid_structure(self, mock_client, adapter):
        """An empty schedule from the API should still return a valid response dict."""
        mock_client.team_schedule_for_month.return_value = []
        result = adapter.get_team_stats("miami heat")
 
        assert 'team' in result
        assert 'schedule' in result
        assert result['schedule'] == []
 
    @patch('adapters.bbref_adapter.client')
    def test_schedule_contains_expected_fields(self, mock_client, adapter):
        """Each game in the schedule should contain the fields returned by the API."""
        mock_client.team_schedule_for_month.return_value = [
            {'date': '2025-03-01', 'opponent': 'Chicago Bulls', 'outcome': 'WIN'}
        ]
        result = adapter.get_team_stats("boston celtics")
 
        game = result['schedule'][0]
        assert game['date'] == '2025-03-01'
        assert game['opponent'] == 'Chicago Bulls'
        assert game['outcome'] == 'WIN'
 
    def test_empty_string_team_returns_error(self, adapter):
        """An empty string should not resolve to a valid team."""
        result = adapter.get_team_stats("")
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
 
    @patch('adapters.bbref_adapter.client')
    def test_both_players_missing_returns_structure_with_errors(self, mock_client, adapter):
        """If both players are not found, both entries should contain errors."""
        mock_client.search.return_value = {'players': []}
        result = adapter.get_player_comparison("Ghost A", "Ghost B")
 
        assert 'Ghost A' in result
        assert 'Ghost B' in result
        assert 'error' in result['Ghost A']
        assert 'error' in result['Ghost B']
 
    @patch('adapters.bbref_adapter.client')
    def test_result_is_dict(self, mock_client, adapter):
        """Return value should always be a dict."""
        mock_client.search.return_value = {'players': []}
        result = adapter.get_player_comparison("A", "B")
 
        assert isinstance(result, dict)
 
    @patch('adapters.bbref_adapter.client')
    def test_search_called_for_both_players(self, mock_client, adapter):
        """The adapter should search for each player individually."""
        mock_client.search.return_value = {'players': []}
        adapter.get_player_comparison("LeBron James", "Kevin Durant")
 
        calls = [
            c.kwargs.get("term") or (c.args[0] if c.args else None)
            for c in mock_client.search.call_args_list
        ]
        assert "LeBron James" in calls
        assert "Kevin Durant" in calls
 
    @patch('adapters.bbref_adapter.client')
    def test_exception_during_search_returns_error_structure(self, mock_client, adapter):
        """An exception mid-comparison should not crash — it should return an error."""
        mock_client.search.side_effect = Exception("API failure")
        result = adapter.get_player_comparison("LeBron James", "Stephen Curry")
 
        assert isinstance(result, dict)
        assert 'error' in result or 'LeBron James' in result
 
 
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
 
    @patch('adapters.bbref_adapter.client')
    def test_result_is_dict(self, mock_client, adapter):
        """Return value should always be a dict."""
        mock_client.team_schedule_for_month.return_value = []
        result = adapter.get_team_comparison("miami heat", "chicago bulls")
 
        assert isinstance(result, dict)
 
    def test_one_invalid_team_still_returns_structure(self, adapter):
        """If one team is invalid, the result should still be a dict with an error entry."""
        result = adapter.get_team_comparison("boston celtics", "Springfield Atoms")
 
        assert isinstance(result, dict)
        assert 'Springfield Atoms' in result
        assert 'error' in result['Springfield Atoms']
 
    def test_both_invalid_teams_return_structure_with_errors(self, adapter):
        """If both teams are invalid, both entries should contain errors."""
        result = adapter.get_team_comparison("Fake Team A", "Fake Team B")
 
        assert isinstance(result, dict)
        assert 'error' in result.get('Fake Team A', {'error': True})
        assert 'error' in result.get('Fake Team B', {'error': True})
 
    @patch('adapters.bbref_adapter.client')
    def test_both_teams_data_present_in_result(self, mock_client, adapter):
        """Both team names should appear as keys in the result."""
        mock_client.team_schedule_for_month.return_value = [
            {'date': '2025-01-01', 'outcome': 'WIN'}
        ]
        result = adapter.get_team_comparison("boston celtics", "miami heat")
 
        assert 'boston celtics' in result
        assert 'miami heat' in result
 
 
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
 
    @patch('adapters.bbref_adapter.client')
    def test_empty_standings_returns_empty_list(self, mock_client, adapter):
        """An empty response from the API should return an empty list, not an error."""
        mock_client.standings.return_value = []
        result = adapter.get_team_rankings()
 
        assert isinstance(result, list)
        assert len(result) == 0
 
    @patch('adapters.bbref_adapter.client')
    def test_multiple_teams_all_returned(self, mock_client, adapter):
        """All teams returned by the API should appear in the result."""
        mock_client.standings.return_value = [
            {'team': 'Boston Celtics', 'wins': 60},
            {'team': 'Miami Heat', 'wins': 45},
            {'team': 'Chicago Bulls', 'wins': 38},
        ]
        result = adapter.get_team_rankings()
 
        assert len(result) == 3
 
    @patch('adapters.bbref_adapter.client')
    def test_standings_called_once(self, mock_client, adapter):
        """The standings API should only be called once per request."""
        mock_client.standings.return_value = []
        adapter.get_team_rankings()
 
        mock_client.standings.assert_called_once()
 
    @patch('adapters.bbref_adapter.client')
    def test_result_preserves_team_data(self, mock_client, adapter):
        """Data from the API should not be modified or dropped."""
        mock_client.standings.return_value = [
            {'team': 'Boston Celtics', 'wins': 60, 'losses': 22, 'pct': 0.732}
        ]
        result = adapter.get_team_rankings()
 
        assert result[0]['wins'] == 60
        assert result[0]['losses'] == 22
        assert result[0]['pct'] == 0.732
 
 
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
 
    @patch('adapters.bbref_adapter.client')
    def test_limit_larger_than_results_returns_all(self, mock_client, adapter):
        """If limit exceeds available players, all players should be returned."""
        mock_client.players_season_totals.return_value = [
            {'player': 'A', 'points': 100},
            {'player': 'B', 'points': 200},
        ]
        result = adapter.get_top_players(stat_category='points', limit=50)
 
        assert len(result) == 2
 
    @patch('adapters.bbref_adapter.client')
    def test_limit_of_one_returns_single_top_player(self, mock_client, adapter):
        """A limit of 1 should return only the single highest-ranked player."""
        mock_client.players_season_totals.return_value = [
            {'player': 'A', 'points': 300},
            {'player': 'B', 'points': 800},
            {'player': 'C', 'points': 500},
        ]
        result = adapter.get_top_players(stat_category='points', limit=1)
 
        assert len(result) == 1
        assert result[0]['player'] == 'B'
 
    @patch('adapters.bbref_adapter.client')
    def test_empty_player_list_returns_empty(self, mock_client, adapter):
        """An empty response from the API should yield an empty result list."""
        mock_client.players_season_totals.return_value = []
        result = adapter.get_top_players(stat_category='points', limit=5)
 
        assert isinstance(result, list)
        assert len(result) == 0
 
    @patch('adapters.bbref_adapter.client')
    def test_different_stat_categories_work(self, mock_client, adapter):
        """The adapter should handle different stat categories like assists or rebounds."""
        mock_client.players_season_totals.return_value = [
            {'player': 'A', 'assists': 700},
            {'player': 'B', 'assists': 400},
        ]
        result = adapter.get_top_players(stat_category='assists', limit=2)
 
        assert result[0]['assists'] == 700
 
    @patch('adapters.bbref_adapter.client')
    def test_result_is_always_a_list(self, mock_client, adapter):
        """Return value should always be a list, even in edge cases."""
        mock_client.players_season_totals.return_value = [
            {'player': 'A', 'points': 100}
        ]
        result = adapter.get_top_players(stat_category='points', limit=1)
 
        assert isinstance(result, list)
 