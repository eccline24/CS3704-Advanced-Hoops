"""
Unit tests for NBAApiAdapter.

AI ATTRIBUTION (per course policy):
  Tool   : Claude (claude-sonnet-4-20250514 via claude.ai)
  Prompt : "I have an NBAApiAdapter class that wraps the nba_api library. It has
_find_player_id(player_name) which searches players.get_players(),
_find_team_id(team_name) which matches by full_name, abbreviation, or nickname
from teams.get_teams(), get_player_stats() which calls PlayerCareerStats and
returns a dataframe converted to records with keys SEASON_ID, GP, PTS, REB, AST,
STL, BLK, TOV, FG_PCT, FG3_PCT, FT_PCT, get_team_stats() which calls
CommonTeamRoster and returns PLAYER, NUM, POSITION, HEIGHT, WEIGHT, SEASON_EXP,
get_player_comparison(), get_team_comparison(), get_team_rankings() using
LeagueStandings, and get_top_players() using LeagueLeaders. All endpoints return
pandas DataFrames by get_data_frames()[0]. Generate pytest unit tests for
all nba_api calls. At least one test per method."

Later expanded with Claude AI to:
  - share fixtures across classes (DRY the duplicated player/team lists and DataFrames)
  - cover edge cases (empty-string lookups, multi-season stats, get_top_players
    default args / limit=0 / limit > available, get_team_rankings error path)
  - assert time.sleep(0.6) is called on rate-limited endpoints and skipped on
    early returns (player/team not found)\

Later expanded with Claude AI:
    - Added lookup tests verifying exact numeric IDs are returned, that partial names do not match, that all-uppercase input resolves correctly, and that empty player and team lists always return None
    - Expanded comparison tests to confirm that PlayerCareerStats and CommonTeamRoster are each called once per player or team, and that one or both invalid inputs return structured error dictionaries
    - Fixed two failing tests where mock DataFrames were missing required columns — adding SEASON_EXP for the team comparison roster lookup and creating a dedicated AST DataFrame for the stat category forwarding test
"""

import pytest
from unittest.mock import patch, MagicMock, call
import pandas as pd
import sys, os
 
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data'))
 
from adapters.nba_api_adapter import NBAApiAdapter
 
 
# ---------------------------------------------------------------------------
# Helpers / shared fixtures
# ---------------------------------------------------------------------------
 
def _make_df(data: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(data)
 
 
@pytest.fixture
def adapter():
    return NBAApiAdapter()
 
 
@pytest.fixture
def lebron():
    return {'full_name': 'LeBron James', 'id': 2544}
 
 
@pytest.fixture
def curry():
    return {'full_name': 'Stephen Curry', 'id': 201939}
 
 
@pytest.fixture
def player_list(lebron, curry):
    return [lebron, curry]
 
 
@pytest.fixture
def lakers():
    return {'full_name': 'Los Angeles Lakers', 'abbreviation': 'LAL',
            'nickname': 'Lakers', 'id': 1610612747}
 
 
@pytest.fixture
def celtics():
    return {'full_name': 'Boston Celtics', 'abbreviation': 'BOS',
            'nickname': 'Celtics', 'id': 1610612738}
 
 
@pytest.fixture
def team_list(lakers, celtics):
    return [lakers, celtics]
 
 
@pytest.fixture
def career_row():
    """One season's worth of career stats (all columns the adapter selects)."""
    return {
        'SEASON_ID': '2023-24', 'GP': 71, 'PTS': 25.7, 'REB': 7.3,
        'AST': 8.3, 'STL': 1.3, 'BLK': 0.6, 'TOV': 3.5,
        'FG_PCT': 0.54, 'FG3_PCT': 0.41, 'FT_PCT': 0.75
    }
 
 
@pytest.fixture
def career_df(career_row):
    return _make_df([career_row])
 
 
@pytest.fixture
def multi_season_career_df(career_row):
    return _make_df([
        {**career_row, 'SEASON_ID': '2021-22', 'PTS': 30.3},
        {**career_row, 'SEASON_ID': '2022-23', 'PTS': 28.9},
        {**career_row, 'SEASON_ID': '2023-24', 'PTS': 25.7},
    ])
 
 
@pytest.fixture
def roster_df():
    return _make_df([{
        'PLAYER': 'LeBron James', 'NUM': '23', 'POSITION': 'F',
        'HEIGHT': '6-9', 'WEIGHT': '250', 'SEASON_EXP': 21
    }])
 
 
@pytest.fixture
def multi_player_roster_df():
    return _make_df([
        {'PLAYER': 'LeBron James', 'NUM': '23', 'POSITION': 'F',
         'HEIGHT': '6-9', 'WEIGHT': '250', 'SEASON_EXP': 21},
        {'PLAYER': 'Anthony Davis', 'NUM': '3', 'POSITION': 'C',
         'HEIGHT': '6-10', 'WEIGHT': '253', 'SEASON_EXP': 12},
    ])
 
 
# ---------------------------------------------------------------------------
# _find_player_id
# ---------------------------------------------------------------------------
 
class TestFindPlayerId:
    @patch('adapters.nba_api_adapter.players')
    def test_known_player_returns_id(self, mock_players, adapter, player_list):
        mock_players.get_players.return_value = player_list
        assert adapter._find_player_id("LeBron James") == 2544
 
    @patch('adapters.nba_api_adapter.players')
    def test_case_insensitive_lookup(self, mock_players, adapter, player_list):
        mock_players.get_players.return_value = player_list
        assert adapter._find_player_id("lebron james") == 2544
 
    @patch('adapters.nba_api_adapter.players')
    def test_unknown_player_returns_none(self, mock_players, adapter, player_list):
        mock_players.get_players.return_value = player_list
        assert adapter._find_player_id("Fake Person") is None
 
    @patch('adapters.nba_api_adapter.players')
    def test_empty_string_returns_none(self, mock_players, adapter, player_list):
        mock_players.get_players.return_value = player_list
        assert adapter._find_player_id("") is None
 
    @patch('adapters.nba_api_adapter.players')
    def test_second_player_in_list_found(self, mock_players, adapter, player_list):
        """Lookup should work for players beyond just the first in the list."""
        mock_players.get_players.return_value = player_list
        assert adapter._find_player_id("Stephen Curry") == 201939
 
    @patch('adapters.nba_api_adapter.players')
    def test_upper_case_input_resolves(self, mock_players, adapter, player_list):
        """All-uppercase input should still resolve correctly."""
        mock_players.get_players.return_value = player_list
        assert adapter._find_player_id("LEBRON JAMES") == 2544
 
    @patch('adapters.nba_api_adapter.players')
    def test_empty_player_list_returns_none(self, mock_players, adapter):
        """An empty player list should always return None."""
        mock_players.get_players.return_value = []
        assert adapter._find_player_id("LeBron James") is None
 
    @patch('adapters.nba_api_adapter.players')
    def test_partial_name_returns_none(self, mock_players, adapter, player_list):
        """A partial name like 'LeBron' should not match 'LeBron James'."""
        mock_players.get_players.return_value = player_list
        assert adapter._find_player_id("LeBron") is None
 
    @patch('adapters.nba_api_adapter.players')
    def test_returns_correct_id_not_just_truthy(self, mock_players, adapter, player_list):
        """Verify the exact numeric ID is returned, not just any truthy value."""
        mock_players.get_players.return_value = player_list
        result = adapter._find_player_id("LeBron James")
        assert result == 2544
        assert isinstance(result, int)
 
 
# ---------------------------------------------------------------------------
# _find_team_id
# ---------------------------------------------------------------------------
 
class TestFindTeamId:
    @patch('adapters.nba_api_adapter.teams')
    def test_full_name_match(self, mock_teams, adapter, team_list):
        mock_teams.get_teams.return_value = team_list
        assert adapter._find_team_id("Los Angeles Lakers") == 1610612747
 
    @patch('adapters.nba_api_adapter.teams')
    def test_abbreviation_match(self, mock_teams, adapter, team_list):
        mock_teams.get_teams.return_value = team_list
        assert adapter._find_team_id("LAL") == 1610612747
 
    @patch('adapters.nba_api_adapter.teams')
    def test_abbreviation_case_insensitive(self, mock_teams, adapter, team_list):
        mock_teams.get_teams.return_value = team_list
        assert adapter._find_team_id("lal") == 1610612747
 
    @patch('adapters.nba_api_adapter.teams')
    def test_nickname_match(self, mock_teams, adapter, team_list):
        mock_teams.get_teams.return_value = team_list
        assert adapter._find_team_id("Lakers") == 1610612747
 
    @patch('adapters.nba_api_adapter.teams')
    def test_unknown_team_returns_none(self, mock_teams, adapter, team_list):
        mock_teams.get_teams.return_value = team_list
        assert adapter._find_team_id("Springfield Atoms") is None
 
    @patch('adapters.nba_api_adapter.teams')
    def test_empty_string_returns_none(self, mock_teams, adapter, team_list):
        mock_teams.get_teams.return_value = team_list
        assert adapter._find_team_id("") is None
 
    @patch('adapters.nba_api_adapter.teams')
    def test_second_team_in_list_found(self, mock_teams, adapter, team_list):
        """Lookup should work for teams beyond just the first in the list."""
        mock_teams.get_teams.return_value = team_list
        assert adapter._find_team_id("Boston Celtics") == 1610612738
 
    @patch('adapters.nba_api_adapter.teams')
    def test_celtics_abbreviation_match(self, mock_teams, adapter, team_list):
        mock_teams.get_teams.return_value = team_list
        assert adapter._find_team_id("BOS") == 1610612738
 
    @patch('adapters.nba_api_adapter.teams')
    def test_empty_team_list_returns_none(self, mock_teams, adapter):
        """An empty team list should always return None."""
        mock_teams.get_teams.return_value = []
        assert adapter._find_team_id("Lakers") is None
 
    @patch('adapters.nba_api_adapter.teams')
    def test_returns_correct_id_not_just_truthy(self, mock_teams, adapter, team_list):
        """Verify the exact numeric ID is returned, not just any truthy value."""
        mock_teams.get_teams.return_value = team_list
        result = adapter._find_team_id("Los Angeles Lakers")
        assert result == 1610612747
        assert isinstance(result, int)
 
    @patch('adapters.nba_api_adapter.teams')
    def test_full_name_case_insensitive(self, mock_teams, adapter, team_list):
        """Full name lookup should be case-insensitive."""
        mock_teams.get_teams.return_value = team_list
        assert adapter._find_team_id("los angeles lakers") == 1610612747
 
 
# ---------------------------------------------------------------------------
# get_player_stats
# ---------------------------------------------------------------------------
 
class TestGetPlayerStats:
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.playercareerstats')
    @patch('adapters.nba_api_adapter.players')
    def test_returns_stats_dict(
        self, mock_players, mock_career, mock_time, adapter, player_list, career_df
    ):
        mock_players.get_players.return_value = player_list
        mock_career.PlayerCareerStats.return_value.get_data_frames.return_value = [career_df]
 
        result = adapter.get_player_stats("LeBron James")
 
        assert result['player'] == "LeBron James"
        assert result['source'] == "nba_api"
        assert isinstance(result['stats'], list)
        assert result['stats'][0]['SEASON_ID'] == '2023-24'
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.playercareerstats')
    @patch('adapters.nba_api_adapter.players')
    def test_returns_all_seasons(
        self, mock_players, mock_career, mock_time,
        adapter, player_list, multi_season_career_df,
    ):
        """Every season row should appear in the response, not just the latest."""
        mock_players.get_players.return_value = player_list
        mock_career.PlayerCareerStats.return_value.get_data_frames.return_value = [
            multi_season_career_df
        ]
 
        result = adapter.get_player_stats("LeBron James")
 
        season_ids = [s['SEASON_ID'] for s in result['stats']]
        assert season_ids == ['2021-22', '2022-23', '2023-24']
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.playercareerstats')
    @patch('adapters.nba_api_adapter.players')
    def test_sleeps_for_rate_limit(
        self, mock_players, mock_career, mock_time,
        adapter, player_list, career_df,
    ):
        mock_players.get_players.return_value = player_list
        mock_career.PlayerCareerStats.return_value.get_data_frames.return_value = [career_df]
 
        adapter.get_player_stats("LeBron James")
 
        mock_time.sleep.assert_called_once_with(0.6)
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.players')
    def test_unknown_player_returns_error(
        self, mock_players, mock_time, adapter
    ):
        mock_players.get_players.return_value = []
        result = adapter.get_player_stats("Ghost")
 
        assert 'error' in result
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.players')
    def test_unknown_player_skips_sleep(
        self, mock_players, mock_time, adapter
    ):
        """Early return means no API call, so no rate-limit sleep either."""
        mock_players.get_players.return_value = []
        adapter.get_player_stats("Ghost")
 
        mock_time.sleep.assert_not_called()
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.playercareerstats')
    @patch('adapters.nba_api_adapter.players')
    def test_result_is_always_dict(
        self, mock_players, mock_career, mock_time, adapter, player_list, career_df
    ):
        """Return value should always be a dict."""
        mock_players.get_players.return_value = player_list
        mock_career.PlayerCareerStats.return_value.get_data_frames.return_value = [career_df]
 
        result = adapter.get_player_stats("LeBron James")
 
        assert isinstance(result, dict)
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.playercareerstats')
    @patch('adapters.nba_api_adapter.players')
    def test_stats_contain_expected_keys(
        self, mock_players, mock_career, mock_time, adapter, player_list, career_df
    ):
        """Each stat row should contain core expected fields."""
        mock_players.get_players.return_value = player_list
        mock_career.PlayerCareerStats.return_value.get_data_frames.return_value = [career_df]
 
        result = adapter.get_player_stats("LeBron James")
 
        stat = result['stats'][0]
        for key in ('SEASON_ID', 'GP', 'PTS', 'REB', 'AST'):
            assert key in stat, f"Expected key '{key}' missing from stats"
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.playercareerstats')
    @patch('adapters.nba_api_adapter.players')
    def test_career_stats_called_with_correct_player_id(
        self, mock_players, mock_career, mock_time, adapter, player_list, career_df
    ):
        """PlayerCareerStats should be called with LeBron's correct player ID."""
        mock_players.get_players.return_value = player_list
        mock_career.PlayerCareerStats.return_value.get_data_frames.return_value = [career_df]
 
        adapter.get_player_stats("LeBron James")
 
        call_kwargs = mock_career.PlayerCareerStats.call_args
        assert call_kwargs is not None
        called_with = call_kwargs.kwargs if call_kwargs.kwargs else call_kwargs.args
        # Player ID 2544 should appear somewhere in the call
        assert 2544 in (called_with.values() if isinstance(called_with, dict) else called_with)
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.playercareerstats')
    @patch('adapters.nba_api_adapter.players')
    def test_pts_value_preserved_correctly(
        self, mock_players, mock_career, mock_time, adapter, player_list, career_df
    ):
        """Numeric stat values should be passed through without modification."""
        mock_players.get_players.return_value = player_list
        mock_career.PlayerCareerStats.return_value.get_data_frames.return_value = [career_df]
 
        result = adapter.get_player_stats("LeBron James")
 
        assert result['stats'][0]['PTS'] == 25.7
 
 
# ---------------------------------------------------------------------------
# get_team_stats
# ---------------------------------------------------------------------------
 
class TestGetTeamStats:
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.commonteamroster')
    @patch('adapters.nba_api_adapter.teams')
    def test_returns_roster_dict(
        self, mock_teams, mock_roster, mock_time,
        adapter, team_list, roster_df,
    ):
        mock_teams.get_teams.return_value = team_list
        mock_roster.CommonTeamRoster.return_value.get_data_frames.return_value = [roster_df]
 
        result = adapter.get_team_stats("Los Angeles Lakers")
 
        assert result['team'] == "Los Angeles Lakers"
        assert result['source'] == "nba_api"
        assert isinstance(result['roster'], list)
        assert result['roster'][0]['PLAYER'] == 'LeBron James'
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.commonteamroster')
    @patch('adapters.nba_api_adapter.teams')
    def test_sleeps_for_rate_limit(
        self, mock_teams, mock_roster, mock_time,
        adapter, team_list, roster_df,
    ):
        mock_teams.get_teams.return_value = team_list
        mock_roster.CommonTeamRoster.return_value.get_data_frames.return_value = [roster_df]
 
        adapter.get_team_stats("Lakers")
 
        mock_time.sleep.assert_called_once_with(0.6)
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.teams')
    def test_unknown_team_returns_error(self, mock_teams, mock_time, adapter):
        mock_teams.get_teams.return_value = []
        result = adapter.get_team_stats("Fake Team")
 
        assert 'error' in result
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.teams')
    def test_unknown_team_skips_sleep(self, mock_teams, mock_time, adapter):
        mock_teams.get_teams.return_value = []
        adapter.get_team_stats("Fake Team")
 
        mock_time.sleep.assert_not_called()
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.commonteamroster')
    @patch('adapters.nba_api_adapter.teams')
    def test_result_is_always_dict(
        self, mock_teams, mock_roster, mock_time, adapter, team_list, roster_df
    ):
        """Return value should always be a dict."""
        mock_teams.get_teams.return_value = team_list
        mock_roster.CommonTeamRoster.return_value.get_data_frames.return_value = [roster_df]
 
        result = adapter.get_team_stats("Los Angeles Lakers")
 
        assert isinstance(result, dict)
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.commonteamroster')
    @patch('adapters.nba_api_adapter.teams')
    def test_multi_player_roster_all_returned(
        self, mock_teams, mock_roster, mock_time,
        adapter, team_list, multi_player_roster_df
    ):
        """All players on the roster should appear in the result."""
        mock_teams.get_teams.return_value = team_list
        mock_roster.CommonTeamRoster.return_value.get_data_frames.return_value = [
            multi_player_roster_df
        ]
 
        result = adapter.get_team_stats("Los Angeles Lakers")
 
        assert len(result['roster']) == 2
        player_names = [p['PLAYER'] for p in result['roster']]
        assert 'LeBron James' in player_names
        assert 'Anthony Davis' in player_names
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.commonteamroster')
    @patch('adapters.nba_api_adapter.teams')
    def test_roster_player_fields_preserved(
        self, mock_teams, mock_roster, mock_time,
        adapter, team_list, roster_df
    ):
        """Player fields like NUM and POSITION should be passed through unchanged."""
        mock_teams.get_teams.return_value = team_list
        mock_roster.CommonTeamRoster.return_value.get_data_frames.return_value = [roster_df]
 
        result = adapter.get_team_stats("Los Angeles Lakers")
 
        player = result['roster'][0]
        assert player['NUM'] == '23'
        assert player['POSITION'] == 'F'
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.commonteamroster')
    @patch('adapters.nba_api_adapter.teams')
    def test_lookup_by_abbreviation(
        self, mock_teams, mock_roster, mock_time,
        adapter, team_list, roster_df
    ):
        """Team lookup by abbreviation should work end-to-end."""
        mock_teams.get_teams.return_value = team_list
        mock_roster.CommonTeamRoster.return_value.get_data_frames.return_value = [roster_df]
 
        result = adapter.get_team_stats("LAL")
 
        assert result['team'] == "LAL"
        assert 'roster' in result
 
 
# ---------------------------------------------------------------------------
# get_player_comparison
# ---------------------------------------------------------------------------
 
class TestGetPlayerComparison:
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.playercareerstats')
    @patch('adapters.nba_api_adapter.players')
    def test_comparison_has_both_players(
        self, mock_players, mock_career, mock_time,
        adapter, player_list, career_df,
    ):
        mock_players.get_players.return_value = player_list
        mock_career.PlayerCareerStats.return_value.get_data_frames.return_value = [career_df]
 
        result = adapter.get_player_comparison("LeBron James", "Stephen Curry")
 
        assert result['comparison'] == 'player'
        assert result['source'] == 'nba_api'
        assert 'LeBron James' in result
        assert 'Stephen Curry' in result
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.playercareerstats')
    @patch('adapters.nba_api_adapter.players')
    def test_result_is_dict(
        self, mock_players, mock_career, mock_time,
        adapter, player_list, career_df,
    ):
        """Return value should always be a dict."""
        mock_players.get_players.return_value = player_list
        mock_career.PlayerCareerStats.return_value.get_data_frames.return_value = [career_df]
 
        result = adapter.get_player_comparison("LeBron James", "Stephen Curry")
 
        assert isinstance(result, dict)
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.players')
    def test_one_unknown_player_still_returns_structure(
        self, mock_players, mock_time, adapter, player_list
    ):
        """If one player is not found, the result should still be a dict with an error entry."""
        mock_players.get_players.return_value = player_list
 
        result = adapter.get_player_comparison("LeBron James", "Ghost Player")
 
        assert isinstance(result, dict)
        assert 'Ghost Player' in result
        assert 'error' in result['Ghost Player']
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.players')
    def test_both_unknown_players_return_errors(
        self, mock_players, mock_time, adapter
    ):
        """If both players are unknown, both entries should contain errors."""
        mock_players.get_players.return_value = []
 
        result = adapter.get_player_comparison("Ghost A", "Ghost B")
 
        assert isinstance(result, dict)
        assert 'Ghost A' in result
        assert 'Ghost B' in result
        assert 'error' in result['Ghost A']
        assert 'error' in result['Ghost B']
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.playercareerstats')
    @patch('adapters.nba_api_adapter.players')
    def test_career_stats_fetched_for_both_players(
        self, mock_players, mock_career, mock_time,
        adapter, player_list, career_df,
    ):
        """The career stats API should be called once per player."""
        mock_players.get_players.return_value = player_list
        mock_career.PlayerCareerStats.return_value.get_data_frames.return_value = [career_df]
 
        adapter.get_player_comparison("LeBron James", "Stephen Curry")
 
        assert mock_career.PlayerCareerStats.call_count == 2
 
 
# ---------------------------------------------------------------------------
# get_team_comparison
# ---------------------------------------------------------------------------
 
class TestGetTeamComparison:
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.commonteamroster')
    @patch('adapters.nba_api_adapter.teams')
    def test_comparison_has_both_teams(
        self, mock_teams, mock_roster, mock_time,
        adapter, team_list, roster_df,
    ):
        mock_teams.get_teams.return_value = team_list
        mock_roster.CommonTeamRoster.return_value.get_data_frames.return_value = [roster_df]
 
        result = adapter.get_team_comparison("Los Angeles Lakers", "Boston Celtics")
 
        assert result['comparison'] == 'team'
        assert 'Los Angeles Lakers' in result
        assert 'Boston Celtics' in result
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.commonteamroster')
    @patch('adapters.nba_api_adapter.teams')
    def test_result_is_dict(
        self, mock_teams, mock_roster, mock_time,
        adapter, team_list, roster_df,
    ):
        """Return value should always be a dict."""
        mock_teams.get_teams.return_value = team_list
        mock_roster.CommonTeamRoster.return_value.get_data_frames.return_value = [roster_df]
 
        result = adapter.get_team_comparison("Los Angeles Lakers", "Boston Celtics")
 
        assert isinstance(result, dict)
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.commonteamroster')
    @patch('adapters.nba_api_adapter.teams')
    def test_one_invalid_team_still_returns_structure(
        self, mock_teams, mock_roster, mock_time, adapter, team_list, roster_df
    ):
        """If one team is invalid, the result should still be a structured dict."""
        mock_teams.get_teams.return_value = team_list
        mock_roster.CommonTeamRoster.return_value.get_data_frames.return_value = [roster_df]
 
        result = adapter.get_team_comparison("Los Angeles Lakers", "Fake Team")
 
        assert isinstance(result, dict)
        assert 'Fake Team' in result
        assert 'error' in result['Fake Team']
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.teams')
    def test_both_invalid_teams_return_errors(
        self, mock_teams, mock_time, adapter
    ):
        """If both teams are invalid, both entries should contain errors."""
        mock_teams.get_teams.return_value = []
 
        result = adapter.get_team_comparison("Fake A", "Fake B")
 
        assert isinstance(result, dict)
        assert 'Fake A' in result
        assert 'Fake B' in result
        assert 'error' in result['Fake A']
        assert 'error' in result['Fake B']
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.commonteamroster')
    @patch('adapters.nba_api_adapter.teams')
    def test_roster_fetched_for_both_teams(
        self, mock_teams, mock_roster, mock_time,
        adapter, team_list, roster_df,
    ):
        """CommonTeamRoster should be called once per team."""
        mock_teams.get_teams.return_value = team_list
        mock_roster.CommonTeamRoster.return_value.get_data_frames.return_value = [roster_df]
 
        adapter.get_team_comparison("Los Angeles Lakers", "Boston Celtics")
 
        assert mock_roster.CommonTeamRoster.call_count == 2
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.commonteamroster')
    @patch('adapters.nba_api_adapter.teams')
    def test_source_is_nba_api(
        self, mock_teams, mock_roster, mock_time,
        adapter, team_list, roster_df,
    ):
        mock_teams.get_teams.return_value = team_list
        mock_roster.CommonTeamRoster.return_value.get_data_frames.return_value = [roster_df]
 
        result = adapter.get_team_comparison("Los Angeles Lakers", "Boston Celtics")
 
        assert result.get('source') == 'nba_api'
 
 
# ---------------------------------------------------------------------------
# get_team_rankings
# ---------------------------------------------------------------------------
 
class TestGetTeamRankings:
    @pytest.fixture
    def standings_df(self):
        return _make_df([{
            'TeamName': 'Celtics', 'Conference': 'East',
            'PlayoffRank': 1, 'WINS': 60, 'LOSSES': 22, 'WinPCT': 0.73
        }])
 
    @pytest.fixture
    def multi_team_standings_df(self):
        return _make_df([
            {'TeamName': 'Celtics', 'Conference': 'East', 'PlayoffRank': 1,
             'WINS': 60, 'LOSSES': 22, 'WinPCT': 0.73},
            {'TeamName': 'Lakers', 'Conference': 'West', 'PlayoffRank': 3,
             'WINS': 45, 'LOSSES': 37, 'WinPCT': 0.55},
        ])
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leaguestandings')
    def test_returns_list_of_dicts(
        self, mock_standings, mock_time, adapter, standings_df
    ):
        mock_standings.LeagueStandings.return_value.get_data_frames.return_value = [standings_df]
 
        result = adapter.get_team_rankings()
 
        assert isinstance(result, list)
        assert result[0]['TeamName'] == 'Celtics'
        assert result[0]['WINS'] == 60
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leaguestandings')
    def test_sleeps_for_rate_limit(
        self, mock_standings, mock_time, adapter, standings_df
    ):
        mock_standings.LeagueStandings.return_value.get_data_frames.return_value = [standings_df]
 
        adapter.get_team_rankings()
 
        mock_time.sleep.assert_called_once_with(0.6)
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leaguestandings')
    def test_api_exception_propagates(self, mock_standings, mock_time, adapter):
        """The adapter intentionally doesn't swallow errors — the Flask route does."""
        mock_standings.LeagueStandings.side_effect = Exception("nba.com down")
 
        with pytest.raises(Exception, match="nba.com down"):
            adapter.get_team_rankings()
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leaguestandings')
    def test_all_teams_returned(
        self, mock_standings, mock_time, adapter, multi_team_standings_df
    ):
        """All teams from the API response should appear in the result."""
        mock_standings.LeagueStandings.return_value.get_data_frames.return_value = [
            multi_team_standings_df
        ]
 
        result = adapter.get_team_rankings()
 
        assert len(result) == 2
        team_names = [t['TeamName'] for t in result]
        assert 'Celtics' in team_names
        assert 'Lakers' in team_names
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leaguestandings')
    def test_standings_fields_preserved(
        self, mock_standings, mock_time, adapter, standings_df
    ):
        """All fields from the standings data should be passed through unchanged."""
        mock_standings.LeagueStandings.return_value.get_data_frames.return_value = [standings_df]
 
        result = adapter.get_team_rankings()
 
        team = result[0]
        assert team['Conference'] == 'East'
        assert team['WinPCT'] == 0.73
        assert team['LOSSES'] == 22
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leaguestandings')
    def test_leaguestandings_called_once(
        self, mock_standings, mock_time, adapter, standings_df
    ):
        """The standings API should only be called once per request."""
        mock_standings.LeagueStandings.return_value.get_data_frames.return_value = [standings_df]
 
        adapter.get_team_rankings()
 
        mock_standings.LeagueStandings.assert_called_once()
 
 
# ---------------------------------------------------------------------------
# get_top_players
# ---------------------------------------------------------------------------
 
class TestGetTopPlayers:
    @pytest.fixture
    def leaders_df(self):
        return _make_df([
            {'PLAYER': f'Player{i}', 'TEAM': 'LAL', 'PTS': 30 - i}
            for i in range(15)
        ])
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leagueleaders')
    def test_returns_correct_number_of_players(
        self, mock_leaders, mock_time, adapter, leaders_df
    ):
        mock_leaders.LeagueLeaders.return_value.get_data_frames.return_value = [leaders_df]
 
        result = adapter.get_top_players(stat_category='PTS', limit=5)
 
        assert len(result) == 5
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leagueleaders')
    def test_contains_expected_columns(self, mock_leaders, mock_time, adapter):
        df = _make_df([{'PLAYER': 'LeBron James', 'TEAM': 'LAL', 'PTS': 30.0}])
        mock_leaders.LeagueLeaders.return_value.get_data_frames.return_value = [df]
 
        result = adapter.get_top_players(stat_category='PTS', limit=1)
 
        assert 'PLAYER' in result[0]
        assert 'TEAM' in result[0]
        assert 'PTS' in result[0]
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leagueleaders')
    def test_default_args_use_pts_and_limit_ten(
        self, mock_leaders, mock_time, adapter, leaders_df
    ):
        """Called with no args, the adapter should default to 'PTS' and return 10 rows."""
        mock_leaders.LeagueLeaders.return_value.get_data_frames.return_value = [leaders_df]
 
        result = adapter.get_top_players()
 
        mock_leaders.LeagueLeaders.assert_called_once_with(
            stat_category_abbreviation='PTS'
        )
        assert len(result) == 10
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leagueleaders')
    def test_limit_larger_than_available_returns_all(
        self, mock_leaders, mock_time, adapter
    ):
        df = _make_df([
            {'PLAYER': 'A', 'TEAM': 'LAL', 'PTS': 30},
            {'PLAYER': 'B', 'TEAM': 'BOS', 'PTS': 28},
        ])
        mock_leaders.LeagueLeaders.return_value.get_data_frames.return_value = [df]
 
        result = adapter.get_top_players(stat_category='PTS', limit=50)
 
        assert len(result) == 2
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leagueleaders')
    def test_limit_zero_returns_empty(
        self, mock_leaders, mock_time, adapter, leaders_df
    ):
        mock_leaders.LeagueLeaders.return_value.get_data_frames.return_value = [leaders_df]
 
        result = adapter.get_top_players(stat_category='PTS', limit=0)
 
        assert result == []
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leagueleaders')
    def test_sleeps_for_rate_limit(
        self, mock_leaders, mock_time, adapter, leaders_df
    ):
        mock_leaders.LeagueLeaders.return_value.get_data_frames.return_value = [leaders_df]
 
        adapter.get_top_players(stat_category='PTS', limit=1)
 
        mock_time.sleep.assert_called_once_with(0.6)
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leagueleaders')
    def test_api_exception_propagates(self, mock_leaders, mock_time, adapter):
        mock_leaders.LeagueLeaders.side_effect = Exception("nba.com down")
 
        with pytest.raises(Exception, match="nba.com down"):
            adapter.get_top_players(stat_category='PTS', limit=5)
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leagueleaders')
    def test_result_is_list(self, mock_leaders, mock_time, adapter, leaders_df):
        """Return value should always be a list."""
        mock_leaders.LeagueLeaders.return_value.get_data_frames.return_value = [leaders_df]
 
        result = adapter.get_top_players(stat_category='PTS', limit=3)
 
        assert isinstance(result, list)
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leagueleaders')
    def test_different_stat_category_passed_to_api(
        self, mock_leaders, mock_time, adapter
    ):
        """The stat category string should be forwarded to the LeagueLeaders API call."""
        ast_df = _make_df([
            {'PLAYER': f'Player{i}', 'TEAM': 'LAL', 'AST': 10 - i}
            for i in range(10)
        ])
        mock_leaders.LeagueLeaders.return_value.get_data_frames.return_value = [ast_df]
 
        adapter.get_top_players(stat_category='AST', limit=5)
 
        mock_leaders.LeagueLeaders.assert_called_once_with(
            stat_category_abbreviation='AST'
        )
 
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leagueleaders')
    def test_stat_values_preserved(self, mock_leaders, mock_time, adapter):
        """Numeric stat values should not be modified."""
        df = _make_df([{'PLAYER': 'LeBron James', 'TEAM': 'LAL', 'PTS': 29.4}])
        mock_leaders.LeagueLeaders.return_value.get_data_frames.return_value = [df]
 
        result = adapter.get_top_players(stat_category='PTS', limit=1)
 
        assert result[0]['PTS'] == 29.4