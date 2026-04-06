from adapters.base_adapter import BaseAdapter
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import (
    playercareerstats,
    commonteamroster,
    leaguestandings,
    leagueleaders
)
import time

# imported as next adapter class
# Claude AI provided structure of the file with TODOs for methods. It also ended up giving extra hints on how to implement methods
# prompt: I now want to implement the nba_api adapter. Can you give me another structure for the file with todos for each method

class NBAApiAdapter(BaseAdapter):

    def _find_player_id(self, player_name: str):
        all_players = players.get_players()
        matches = [p for p in all_players if p['full_name'].lower() == player_name.lower()]
        if not matches:
            return None
        return matches[0]['id']

    def _find_team_id(self, team_name: str):
        all_teams = teams.get_teams()
        matches = [t for t in all_teams if
                   t['full_name'].lower() == team_name.lower() or
                   t['abbreviation'].lower() == team_name.lower() or
                   t['nickname'].lower() == team_name.lower()]
        if not matches:
            return None
        return matches[0]['id']

    def get_player_stats(self, player_name: str) -> dict:
        player_id = self._find_player_id(player_name)
        if not player_id:
            return {"error": f"'{player_name}' not found."}
        time.sleep(0.6)
        career = playercareerstats.PlayerCareerStats(player_id=player_id)
        df = career.get_data_frames()[0]
        stats = df[['SEASON_ID', 'GP', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'FG_PCT', 'FG3_PCT', 'FT_PCT']].to_dict(orient='records')
        return {"player": player_name, "source": "nba_api", "stats": stats}

    def get_team_stats(self, team_name: str) -> dict:
        team_id = self._find_team_id(team_name)
        if not team_id:
            return {"error": f"Team '{team_name}' not found."}
        time.sleep(0.6)
        roster = commonteamroster.CommonTeamRoster(team_id=team_id)
        df = roster.get_data_frames()[0]
        players_list = df[['PLAYER', 'NUM', 'POSITION', 'HEIGHT', 'WEIGHT', 'SEASON_EXP']].to_dict(orient='records')
        return {"team": team_name, "source": "nba_api", "roster": players_list}

    def get_player_comparison(self, player1: str, player2: str) -> dict:
        return {"comparison": "player", "source": "nba_api",
                player1: self.get_player_stats(player1),
                player2: self.get_player_stats(player2)}

    def get_team_comparison(self, team1: str, team2: str) -> dict:
        return {"comparison": "team", "source": "nba_api",
                team1: self.get_team_stats(team1),
                team2: self.get_team_stats(team2)}

    def get_team_rankings(self) -> list:
        time.sleep(0.6)
        standings = leaguestandings.LeagueStandings()
        df = standings.get_data_frames()[0]
        return df[['TeamName', 'Conference', 'PlayoffRank', 'WINS', 'LOSSES', 'WinPCT']].to_dict(orient='records')

    def get_top_players(self, stat_category: str = 'PTS', limit: int = 10) -> list:
        time.sleep(0.6)
        leaders = leagueleaders.LeagueLeaders(stat_category_abbreviation=stat_category)
        df = leaders.get_data_frames()[0]
        return df.head(limit)[['PLAYER', 'TEAM', stat_category]].to_dict(orient='records')