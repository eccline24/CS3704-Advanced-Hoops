"""
Unit tests for data_service.py

AI Usage:
  Tool: Claude AI
  Prompt: "Generate unit tests for a DataService class that takes a source 
  parameter ('nba_api' or 'bbref') and delegates to the appropriate adapter. 
  Test that the correct adapter is selected, that an invalid source raises 
  ValueError, and that all methods correctly delegate to the adapter."

Later expanded with Claude AI:
    - Added edge case initialization tests covering invalid inputs such as empty strings, incorrect casing, and None as a source, while also verifying that only the correct adapter is instantiated depending on the selected source
    - Expanded delegation tests to confirm the service returns adapter responses without modification, preserves argument order for comparisons, and correctly passes different stat categories
    - Added a brand new TestDataServiceErrorHandling class verifying that adapter exceptions propagate to the caller and that edge case return values like None, empty lists, and empty dicts are passed through unchanged
"""

import pytest
from unittest.mock import MagicMock, patch, call
import sys, os
 
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data'))
 
from data_service import DataService
 
 
# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
 
@pytest.fixture
def mock_nba_service():
    with patch('data_service.NBAApiAdapter') as mock:
        mock.return_value = MagicMock()
        yield DataService(source='nba_api'), mock.return_value
 
@pytest.fixture
def mock_bbref_service():
    with patch('data_service.BBRefAdapter') as mock:
        mock.return_value = MagicMock()
        yield DataService(source='bbref'), mock.return_value
 
 
# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------
 
class TestDataServiceInit:
    def test_nba_api_source_creates_nba_adapter(self):
        with patch('data_service.NBAApiAdapter') as mock_nba:
            DataService(source='nba_api')
            mock_nba.assert_called_once()
 
    def test_bbref_source_creates_bbref_adapter(self):
        with patch('data_service.BBRefAdapter') as mock_bbref:
            DataService(source='bbref')
            mock_bbref.assert_called_once()
 
    def test_invalid_source_raises_value_error(self):
        with pytest.raises(ValueError):
            DataService(source='invalid_source')
 
    def test_unknown_source_error_message(self):
        with pytest.raises(ValueError, match="Unknown source"):
            DataService(source='espn')
 
    def test_default_source_is_nba_api(self):
        with patch('data_service.NBAApiAdapter') as mock_nba:
            DataService()
            mock_nba.assert_called_once()
 
    def test_empty_string_source_raises_value_error(self):
        """Empty string should not be treated as a valid source."""
        with pytest.raises(ValueError):
            DataService(source='')
 
    def test_case_sensitive_source_raises_value_error(self):
        """Source names should be case-sensitive; 'NBA_API' is not valid."""
        with pytest.raises(ValueError):
            DataService(source='NBA_API')
 
    def test_none_source_raises_error(self):
        """Passing None explicitly should raise an error."""
        with pytest.raises((ValueError, TypeError)):
            DataService(source=None)
 
    def test_nba_adapter_not_created_for_bbref_source(self):
        """When using bbref, the NBA adapter should never be instantiated."""
        with patch('data_service.NBAApiAdapter') as mock_nba, \
             patch('data_service.BBRefAdapter'):
            DataService(source='bbref')
            mock_nba.assert_not_called()
 
    def test_bbref_adapter_not_created_for_nba_source(self):
        """When using nba_api, the BBRef adapter should never be instantiated."""
        with patch('data_service.BBRefAdapter') as mock_bbref, \
             patch('data_service.NBAApiAdapter'):
            DataService(source='nba_api')
            mock_bbref.assert_not_called()
 
 
# ---------------------------------------------------------------------------
# Delegation — NBA API adapter
# ---------------------------------------------------------------------------
 
class TestDataServiceDelegation:
    def test_get_player_stats_delegates_to_adapter(self, mock_nba_service):
        service, adapter = mock_nba_service
        adapter.get_player_stats.return_value = {'player': 'LeBron James'}
 
        result = service.get_player_stats('LeBron James')
 
        adapter.get_player_stats.assert_called_once_with('LeBron James')
        assert result['player'] == 'LeBron James'
 
    def test_get_team_stats_delegates_to_adapter(self, mock_nba_service):
        service, adapter = mock_nba_service
        adapter.get_team_stats.return_value = {'team': 'Lakers'}
 
        result = service.get_team_stats('Lakers')
 
        adapter.get_team_stats.assert_called_once_with('Lakers')
        assert result['team'] == 'Lakers'
 
    def test_get_player_comparison_delegates_to_adapter(self, mock_nba_service):
        service, adapter = mock_nba_service
        adapter.get_player_comparison.return_value = {'comparison': 'player'}
 
        result = service.get_player_comparison('LeBron James', 'Stephen Curry')
 
        adapter.get_player_comparison.assert_called_once_with('LeBron James', 'Stephen Curry')
        assert result['comparison'] == 'player'
 
    def test_get_team_comparison_delegates_to_adapter(self, mock_nba_service):
        service, adapter = mock_nba_service
        adapter.get_team_comparison.return_value = {'comparison': 'team'}
 
        result = service.get_team_comparison('Lakers', 'Celtics')
 
        adapter.get_team_comparison.assert_called_once_with('Lakers', 'Celtics')
        assert result['comparison'] == 'team'
 
    def test_get_team_rankings_delegates_to_adapter(self, mock_nba_service):
        service, adapter = mock_nba_service
        adapter.get_team_rankings.return_value = [{'TeamName': 'Celtics'}]
 
        result = service.get_team_rankings()
 
        adapter.get_team_rankings.assert_called_once()
        assert result[0]['TeamName'] == 'Celtics'
 
    def test_get_top_players_delegates_to_adapter(self, mock_nba_service):
        service, adapter = mock_nba_service
        adapter.get_top_players.return_value = [{'PLAYER': 'LeBron James'}]
 
        result = service.get_top_players('PTS', limit=5)
 
        adapter.get_top_players.assert_called_once_with('PTS', 5)
        assert result[0]['PLAYER'] == 'LeBron James'
 
    def test_get_player_stats_returns_exact_adapter_response(self, mock_nba_service):
        """The service should return the adapter's response without modification."""
        service, adapter = mock_nba_service
        expected = {'player': 'Stephen Curry', 'PTS': 29.4, 'AST': 6.1}
        adapter.get_player_stats.return_value = expected
 
        result = service.get_player_stats('Stephen Curry')
 
        assert result is expected
 
    def test_get_team_stats_returns_exact_adapter_response(self, mock_nba_service):
        """The service should return the adapter's response without modification."""
        service, adapter = mock_nba_service
        expected = {'team': 'Celtics', 'wins': 60, 'losses': 22}
        adapter.get_team_stats.return_value = expected
 
        result = service.get_team_stats('Celtics')
 
        assert result is expected
 
    def test_get_top_players_different_stat_categories(self, mock_nba_service):
        """get_top_players should correctly pass different stat category strings."""
        service, adapter = mock_nba_service
        adapter.get_top_players.return_value = [{'PLAYER': 'Rudy Gobert'}]
 
        service.get_top_players('REB', limit=3)
 
        adapter.get_top_players.assert_called_once_with('REB', 3)
 
    def test_get_top_players_default_limit(self, mock_nba_service):
        """Verify behavior when no limit is provided (uses default)."""
        service, adapter = mock_nba_service
        adapter.get_top_players.return_value = []
 
        service.get_top_players('AST')
 
        assert adapter.get_top_players.called
 
    def test_get_player_comparison_argument_order(self, mock_nba_service):
        """Player names should be passed to the adapter in the same order."""
        service, adapter = mock_nba_service
        adapter.get_player_comparison.return_value = {}
 
        service.get_player_comparison('Player A', 'Player B')
 
        adapter.get_player_comparison.assert_called_once_with('Player A', 'Player B')
 
    def test_get_team_comparison_argument_order(self, mock_nba_service):
        """Team names should be passed to the adapter in the same order."""
        service, adapter = mock_nba_service
        adapter.get_team_comparison.return_value = {}
 
        service.get_team_comparison('Team A', 'Team B')
 
        adapter.get_team_comparison.assert_called_once_with('Team A', 'Team B')
 
    def test_get_team_rankings_returns_full_list(self, mock_nba_service):
        """The full list of team rankings should be returned unchanged."""
        service, adapter = mock_nba_service
        expected = [{'TeamName': 'Celtics'}, {'TeamName': 'Lakers'}, {'TeamName': 'Warriors'}]
        adapter.get_team_rankings.return_value = expected
 
        result = service.get_team_rankings()
 
        assert result == expected
        assert len(result) == 3
 
 
# ---------------------------------------------------------------------------
# BBRef adapter delegation
# ---------------------------------------------------------------------------
 
class TestDataServiceBBRef:
    def test_get_player_stats_uses_bbref_adapter(self, mock_bbref_service):
        service, adapter = mock_bbref_service
        adapter.get_player_stats.return_value = {'source': 'basketball_reference'}
 
        result = service.get_player_stats('LeBron James')
 
        adapter.get_player_stats.assert_called_once_with('LeBron James')
        assert result['source'] == 'basketball_reference'
 
    def test_get_team_rankings_uses_bbref_adapter(self, mock_bbref_service):
        service, adapter = mock_bbref_service
        adapter.get_team_rankings.return_value = [{'team': 'Celtics'}]
 
        result = service.get_team_rankings()
 
        adapter.get_team_rankings.assert_called_once()
        assert result[0]['team'] == 'Celtics'
 
    def test_get_team_stats_uses_bbref_adapter(self, mock_bbref_service):
        """Team stats should be fetched from the BBRef adapter when that source is selected."""
        service, adapter = mock_bbref_service
        adapter.get_team_stats.return_value = {'team': 'Bulls', 'wins': 45}
 
        result = service.get_team_stats('Bulls')
 
        adapter.get_team_stats.assert_called_once_with('Bulls')
        assert result['team'] == 'Bulls'
 
    def test_get_player_comparison_uses_bbref_adapter(self, mock_bbref_service):
        """Player comparisons should be delegated to the BBRef adapter."""
        service, adapter = mock_bbref_service
        adapter.get_player_comparison.return_value = {'comparison': 'bbref_player'}
 
        result = service.get_player_comparison('Michael Jordan', 'Kobe Bryant')
 
        adapter.get_player_comparison.assert_called_once_with('Michael Jordan', 'Kobe Bryant')
        assert result['comparison'] == 'bbref_player'
 
    def test_get_top_players_uses_bbref_adapter(self, mock_bbref_service):
        """Top players query should be delegated to the BBRef adapter."""
        service, adapter = mock_bbref_service
        adapter.get_top_players.return_value = [{'PLAYER': 'Michael Jordan'}]
 
        result = service.get_top_players('PTS', limit=10)
 
        adapter.get_top_players.assert_called_once_with('PTS', 10)
        assert result[0]['PLAYER'] == 'Michael Jordan'
 
 
# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
 
class TestDataServiceErrorHandling:
    def test_adapter_exception_propagates_on_get_player_stats(self, mock_nba_service):
        """Exceptions from the adapter should not be silently swallowed."""
        service, adapter = mock_nba_service
        adapter.get_player_stats.side_effect = Exception("API error")
 
        with pytest.raises(Exception, match="API error"):
            service.get_player_stats('LeBron James')
 
    def test_adapter_exception_propagates_on_get_team_stats(self, mock_nba_service):
        """Exceptions from the adapter should not be silently swallowed."""
        service, adapter = mock_nba_service
        adapter.get_team_stats.side_effect = RuntimeError("Network timeout")
 
        with pytest.raises(RuntimeError, match="Network timeout"):
            service.get_team_stats('Lakers')
 
    def test_adapter_exception_propagates_on_get_team_rankings(self, mock_nba_service):
        """Exceptions from the adapter should propagate to the caller."""
        service, adapter = mock_nba_service
        adapter.get_team_rankings.side_effect = ConnectionError("Service unavailable")
 
        with pytest.raises(ConnectionError):
            service.get_team_rankings()
 
    def test_adapter_returns_none_is_passed_through(self, mock_nba_service):
        """If the adapter returns None, the service should not alter it."""
        service, adapter = mock_nba_service
        adapter.get_player_stats.return_value = None
 
        result = service.get_player_stats('Unknown Player')
 
        assert result is None
 
    def test_adapter_returns_empty_list_is_passed_through(self, mock_nba_service):
        """An empty list from the adapter should be returned as-is."""
        service, adapter = mock_nba_service
        adapter.get_top_players.return_value = []
 
        result = service.get_top_players('PTS', limit=5)
 
        assert result == []
 
    def test_adapter_returns_empty_dict_is_passed_through(self, mock_nba_service):
        """An empty dict from the adapter should be returned as-is."""
        service, adapter = mock_nba_service
        adapter.get_team_stats.return_value = {}
 
        result = service.get_team_stats('Lakers')
 
        assert result == {}