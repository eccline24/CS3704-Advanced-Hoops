"""
Unit tests for data_service.py

AI Usage:
  Tool: Claude AI
  Prompt: "Generate unit tests for a DataService class that takes a source 
  parameter ('nba_api' or 'bbref') and delegates to the appropriate adapter. 
  Test that the correct adapter is selected, that an invalid source raises 
  ValueError, and that all methods correctly delegate to the adapter."
"""

import pytest
from unittest.mock import MagicMock, patch
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