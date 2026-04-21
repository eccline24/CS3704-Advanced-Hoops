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
"""

import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
import sys, os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data'))

from adapters.nba_api_adapter import NBAApiAdapter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_df(data: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(data)


@pytest.fixture
def adapter():
    return NBAApiAdapter()


# ---------------------------------------------------------------------------
# _find_player_id
# ---------------------------------------------------------------------------

class TestFindPlayerId:
    @patch('adapters.nba_api_adapter.players')
    def test_known_player_returns_id(self, mock_players, adapter):
        mock_players.get_players.return_value = [
            {'full_name': 'LeBron James', 'id': 2544}
        ]
        assert adapter._find_player_id("LeBron James") == 2544

    @patch('adapters.nba_api_adapter.players')
    def test_case_insensitive_lookup(self, mock_players, adapter):
        mock_players.get_players.return_value = [
            {'full_name': 'LeBron James', 'id': 2544}
        ]
        assert adapter._find_player_id("lebron james") == 2544

    @patch('adapters.nba_api_adapter.players')
    def test_unknown_player_returns_none(self, mock_players, adapter):
        mock_players.get_players.return_value = [
            {'full_name': 'LeBron James', 'id': 2544}
        ]
        assert adapter._find_player_id("Fake Person") is None


# ---------------------------------------------------------------------------
# _find_team_id
# ---------------------------------------------------------------------------

class TestFindTeamId:
    def _team_list(self):
        return [{'full_name': 'Los Angeles Lakers', 'abbreviation': 'LAL',
                 'nickname': 'Lakers', 'id': 1610612747}]

    @patch('adapters.nba_api_adapter.teams')
    def test_full_name_match(self, mock_teams, adapter):
        mock_teams.get_teams.return_value = self._team_list()
        assert adapter._find_team_id("Los Angeles Lakers") == 1610612747

    @patch('adapters.nba_api_adapter.teams')
    def test_abbreviation_match(self, mock_teams, adapter):
        mock_teams.get_teams.return_value = self._team_list()
        assert adapter._find_team_id("LAL") == 1610612747

    @patch('adapters.nba_api_adapter.teams')
    def test_nickname_match(self, mock_teams, adapter):
        mock_teams.get_teams.return_value = self._team_list()
        assert adapter._find_team_id("Lakers") == 1610612747

    @patch('adapters.nba_api_adapter.teams')
    def test_unknown_team_returns_none(self, mock_teams, adapter):
        mock_teams.get_teams.return_value = self._team_list()
        assert adapter._find_team_id("Springfield Atoms") is None


# ---------------------------------------------------------------------------
# get_player_stats
# ---------------------------------------------------------------------------

class TestGetPlayerStats:
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.playercareerstats')
    @patch('adapters.nba_api_adapter.players')
    def test_returns_stats_dict(self, mock_players, mock_career, mock_time, adapter):
        mock_players.get_players.return_value = [
            {'full_name': 'LeBron James', 'id': 2544}
        ]
        df = _make_df([{
            'SEASON_ID': '2023-24', 'GP': 71, 'PTS': 25.7, 'REB': 7.3,
            'AST': 8.3, 'STL': 1.3, 'BLK': 0.6, 'TOV': 3.5,
            'FG_PCT': 0.54, 'FG3_PCT': 0.41, 'FT_PCT': 0.75
        }])
        mock_career.PlayerCareerStats.return_value.get_data_frames.return_value = [df]

        result = adapter.get_player_stats("LeBron James")

        assert result['player'] == "LeBron James"
        assert result['source'] == "nba_api"
        assert isinstance(result['stats'], list)
        assert result['stats'][0]['SEASON_ID'] == '2023-24'

    @patch('adapters.nba_api_adapter.players')
    def test_unknown_player_returns_error(self, mock_players, adapter):
        mock_players.get_players.return_value = []
        result = adapter.get_player_stats("Ghost")

        assert 'error' in result


# ---------------------------------------------------------------------------
# get_team_stats
# ---------------------------------------------------------------------------

class TestGetTeamStats:
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.commonteamroster')
    @patch('adapters.nba_api_adapter.teams')
    def test_returns_roster_dict(self, mock_teams, mock_roster, mock_time, adapter):
        mock_teams.get_teams.return_value = [
            {'full_name': 'Los Angeles Lakers', 'abbreviation': 'LAL',
             'nickname': 'Lakers', 'id': 1610612747}
        ]
        df = _make_df([{
            'PLAYER': 'LeBron James', 'NUM': '23', 'POSITION': 'F',
            'HEIGHT': '6-9', 'WEIGHT': '250', 'SEASON_EXP': 21
        }])
        mock_roster.CommonTeamRoster.return_value.get_data_frames.return_value = [df]

        result = adapter.get_team_stats("Los Angeles Lakers")

        assert result['team'] == "Los Angeles Lakers"
        assert result['source'] == "nba_api"
        assert isinstance(result['roster'], list)
        assert result['roster'][0]['PLAYER'] == 'LeBron James'

    @patch('adapters.nba_api_adapter.teams')
    def test_unknown_team_returns_error(self, mock_teams, adapter):
        mock_teams.get_teams.return_value = []
        result = adapter.get_team_stats("Fake Team")

        assert 'error' in result


# ---------------------------------------------------------------------------
# get_player_comparison
# ---------------------------------------------------------------------------

class TestGetPlayerComparison:
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.playercareerstats')
    @patch('adapters.nba_api_adapter.players')
    def test_comparison_has_both_players(self, mock_players, mock_career, mock_time, adapter):
        mock_players.get_players.return_value = [
            {'full_name': 'LeBron James', 'id': 2544},
            {'full_name': 'Stephen Curry', 'id': 201939},
        ]
        df = _make_df([{
            'SEASON_ID': '2023-24', 'GP': 70, 'PTS': 25.0, 'REB': 7.0,
            'AST': 8.0, 'STL': 1.0, 'BLK': 0.5, 'TOV': 3.0,
            'FG_PCT': 0.50, 'FG3_PCT': 0.35, 'FT_PCT': 0.75
        }])
        mock_career.PlayerCareerStats.return_value.get_data_frames.return_value = [df]

        result = adapter.get_player_comparison("LeBron James", "Stephen Curry")

        assert result['comparison'] == 'player'
        assert result['source'] == 'nba_api'
        assert 'LeBron James' in result
        assert 'Stephen Curry' in result


# ---------------------------------------------------------------------------
# get_team_comparison
# ---------------------------------------------------------------------------

class TestGetTeamComparison:
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.commonteamroster')
    @patch('adapters.nba_api_adapter.teams')
    def test_comparison_has_both_teams(self, mock_teams, mock_roster, mock_time, adapter):
        mock_teams.get_teams.return_value = [
            {'full_name': 'Los Angeles Lakers', 'abbreviation': 'LAL',
             'nickname': 'Lakers', 'id': 1610612747},
            {'full_name': 'Boston Celtics', 'abbreviation': 'BOS',
             'nickname': 'Celtics', 'id': 1610612738},
        ]
        df = _make_df([{
            'PLAYER': 'A', 'NUM': '0', 'POSITION': 'G',
            'HEIGHT': '6-3', 'WEIGHT': '190', 'SEASON_EXP': 5
        }])
        mock_roster.CommonTeamRoster.return_value.get_data_frames.return_value = [df]

        result = adapter.get_team_comparison("Los Angeles Lakers", "Boston Celtics")

        assert result['comparison'] == 'team'
        assert 'Los Angeles Lakers' in result
        assert 'Boston Celtics' in result


# ---------------------------------------------------------------------------
# get_team_rankings
# ---------------------------------------------------------------------------

class TestGetTeamRankings:
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leaguestandings')
    def test_returns_list_of_dicts(self, mock_standings, mock_time, adapter):
        df = _make_df([{
            'TeamName': 'Celtics', 'Conference': 'East',
            'PlayoffRank': 1, 'WINS': 60, 'LOSSES': 22, 'WinPCT': 0.73
        }])
        mock_standings.LeagueStandings.return_value.get_data_frames.return_value = [df]

        result = adapter.get_team_rankings()

        assert isinstance(result, list)
        assert result[0]['TeamName'] == 'Celtics'
        assert result[0]['WINS'] == 60


# ---------------------------------------------------------------------------
# get_top_players
# ---------------------------------------------------------------------------

class TestGetTopPlayers:
    @patch('adapters.nba_api_adapter.time')
    @patch('adapters.nba_api_adapter.leagueleaders')
    def test_returns_correct_number_of_players(self, mock_leaders, mock_time, adapter):
        df = _make_df([
            {'PLAYER': f'Player{i}', 'TEAM': 'LAL', 'PTS': 30 - i}
            for i in range(15)
        ])
        mock_leaders.LeagueLeaders.return_value.get_data_frames.return_value = [df]

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