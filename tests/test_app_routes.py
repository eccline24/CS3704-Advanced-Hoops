"""
Unit tests for app.py.

AI Usage: 
  Tool: Claude AI. Used it to generate this test file
  Prompt: "Generate  unit tests for every Flask route in my python file. Dont make any actual data calls. The main functions are top_players(), team_rankings(), player_stats(), team_stats(), compare_players, compare_teams(). At least one test per function"
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import sys, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'backend'))
sys.path.insert(0, os.path.join(ROOT, 'data'))


@pytest.fixture(scope='module')
def flask_app_module():
    mock_service = MagicMock()
    with patch('data_service.DataService', return_value=mock_service):
        import app as flask_app
        flask_app.service = mock_service
        flask_app.app.config['TESTING'] = True
        yield flask_app, mock_service


@pytest.fixture
def client(flask_app_module):
    flask_app, mock_service = flask_app_module
    mock_service.reset_mock()
    with flask_app.app.test_client() as c:
        yield c, mock_service


class TestTopPlayers:
    def test_returns_200_with_list(self, client):
        c, svc = client
        svc.get_top_players.return_value = [{'PLAYER': 'LeBron James', 'PTS': 30}]
        resp = c.get('/api/top-players')
        assert resp.status_code == 200
        assert json.loads(resp.data)[0]['PLAYER'] == 'LeBron James'

    def test_returns_500_on_exception(self, client):
        c, svc = client
        svc.get_top_players.side_effect = Exception("API down")
        resp = c.get('/api/top-players')
        assert resp.status_code == 500
        assert 'error' in json.loads(resp.data)


class TestTeamRankings:
    def test_returns_200_with_list(self, client):
        c, svc = client
        svc.get_team_rankings.return_value = [{'TeamName': 'Celtics', 'WINS': 60}]
        resp = c.get('/api/team-rankings')
        assert resp.status_code == 200
        assert json.loads(resp.data)[0]['TeamName'] == 'Celtics'

    def test_returns_500_on_exception(self, client):
        c, svc = client
        svc.get_team_rankings.side_effect = Exception("oops")
        resp = c.get('/api/team-rankings')
        assert resp.status_code == 500


class TestPlayerStats:
    def test_returns_stats_for_known_player(self, client):
        c, svc = client
        svc.get_player_stats.return_value = {'player': 'LeBron James', 'source': 'nba_api', 'stats': []}
        resp = c.get('/api/player/LeBron James')
        assert resp.status_code == 200
        assert json.loads(resp.data)['player'] == 'LeBron James'

    def test_returns_500_on_exception(self, client):
        c, svc = client
        svc.get_player_stats.side_effect = Exception("error")
        resp = c.get('/api/player/LeBron James')
        assert resp.status_code == 500


class TestTeamStats:
    def test_returns_roster_for_known_team(self, client):
        c, svc = client
        svc.get_team_stats.return_value = {'team': 'Los Angeles Lakers', 'source': 'nba_api', 'roster': []}
        resp = c.get('/api/team/Los Angeles Lakers')
        assert resp.status_code == 200

    def test_returns_500_on_exception(self, client):
        c, svc = client
        svc.get_team_stats.side_effect = Exception("down")
        resp = c.get('/api/team/Lakers')
        assert resp.status_code == 500


class TestComparePlayers:
    def test_returns_comparison(self, client):
        c, svc = client
        svc.get_player_comparison.return_value = {
            'comparison': 'player', 'source': 'nba_api',
            'LeBron James': {}, 'Stephen Curry': {}
        }
        resp = c.get('/api/compare/players?player1=LeBron James&player2=Stephen Curry')
        assert resp.status_code == 200
        assert json.loads(resp.data)['comparison'] == 'player'

    def test_missing_params_returns_400(self, client):
        c, svc = client
        resp = c.get('/api/compare/players?player1=LeBron James')
        assert resp.status_code == 400
        assert 'error' in json.loads(resp.data)

    def test_both_params_missing_returns_400(self, client):
        c, svc = client
        resp = c.get('/api/compare/players')
        assert resp.status_code == 400

    def test_returns_500_on_exception(self, client):
        c, svc = client
        svc.get_player_comparison.side_effect = Exception("crash")
        resp = c.get('/api/compare/players?player1=A&player2=B')
        assert resp.status_code == 500


class TestCompareTeams:
    def test_returns_comparison(self, client):
        c, svc = client
        svc.get_team_comparison.return_value = {
            'comparison': 'team', 'source': 'nba_api',
            'Lakers': {}, 'Celtics': {}
        }
        resp = c.get('/api/compare/teams?team1=Lakers&team2=Celtics')
        assert resp.status_code == 200
        assert json.loads(resp.data)['comparison'] == 'team'

    def test_missing_params_returns_400(self, client):
        c, svc = client
        resp = c.get('/api/compare/teams?team1=Lakers')
        assert resp.status_code == 400

    def test_returns_500_on_exception(self, client):
        c, svc = client
        svc.get_team_comparison.side_effect = Exception("crash")
        resp = c.get('/api/compare/teams?team1=A&team2=B')
        assert resp.status_code == 500