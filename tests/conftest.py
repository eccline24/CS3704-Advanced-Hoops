import sys, os, pytest
from unittest.mock import MagicMock

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'backend'))
sys.path.insert(0, os.path.join(ROOT, 'data'))

@pytest.fixture
def sample_players():
    return [
        {'PLAYER': 'LeBron James', 'TEAM': 'LAL', 'PTS': 30.0},
        {'PLAYER': 'Stephen Curry', 'TEAM': 'GSW', 'PTS': 28.0},
    ]

@pytest.fixture
def sample_rankings():
    return [
        {'TeamName': 'Celtics', 'Conference': 'East', 'PlayoffRank': 1, 'WINS': 60, 'LOSSES': 22, 'WinPCT': 0.73},
    ]