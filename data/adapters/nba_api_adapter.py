from adapters.base_adapter import BaseAdapter
from nba_api.stats.static import players, teams
from nba_api.stats.endpoints import (
    playercareerstats,
    commonteamroster,
    leaguestandings,
    leagueleaders,
    teamestimatedmetrics,
    leaguedashplayerstats
)
import time

# imported as next adapter class
# Claude AI provided structure of the file with TODOs for methods. It also ended up giving extra hints on how to implement methods
# prompt: I now want to implement the nba_api adapter. Can you give me another structure for the file with todos for each method

# Implements BaseAdapter using the nba_api package, which pulls live data from nba.com.
# All API calls go through the nba_api endpoints and return pandas DataFrames,
# which are then converted to plain dicts/lists for easy JSON serialization.
class NBAApiAdapter(BaseAdapter):

    # Helper: looks up a player's numeric NBA ID by their full name (case-insensitive).
    # The nba_api requires an ID rather than a name for most endpoint calls.
    def _find_player_id(self, player_name: str):
        all_players = players.get_players()
        matches = [p for p in all_players if p['full_name'].lower() == player_name.lower()]
        if not matches:
            return None
        return matches[0]['id']  # Return the first match's ID

    # Helper: looks up a team's numeric NBA ID by full name, abbreviation, or nickname.
    # Supports multiple formats (e.g. "Los Angeles Lakers", "LAL", or "Lakers").
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
        try:
            player_id = self._find_player_id(player_name)
            if not player_id:
                return {"error": f"'{player_name}' not found."}

            # nba.com rate-limits requests, so sleep briefly to avoid getting blocked.
            time.sleep(0.6)

            # PlayerCareerStats returns one row per season; index [0] is the season totals table.
            career = playercareerstats.PlayerCareerStats(player_id=player_id)
            df = career.get_data_frames()[0]

            # Select only the columns relevant for display and convert to a list of dicts.
            stats = df[['SEASON_ID', 'GP', 'PTS', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'FG_PCT', 'FG3_PCT', 'FT_PCT']].to_dict(orient='records')
            return {"player": player_name, "source": "nba_api", "stats": stats}
        except Exception as e:
            return {"error": f"NBA API error: {str(e)}"}

    def get_team_stats(self, team_name: str) -> dict:
        try:
            team_id = self._find_team_id(team_name)
            if not team_id:
                return {"error": f"Team '{team_name}' not found."}

            time.sleep(0.6)

            # Get team roster info
            roster = commonteamroster.CommonTeamRoster(team_id=team_id)
            df = roster.get_data_frames()[0]
            
            # Check available columns and select what exists
            available_cols = df.columns.tolist()
            cols_to_use = ['PLAYER', 'NUM', 'POSITION']
            
            # Add optional columns if they exist
            if 'HEIGHT' in available_cols:
                cols_to_use.append('HEIGHT')
            if 'WEIGHT' in available_cols:
                cols_to_use.append('WEIGHT')
            if 'SEASON_EXP' in available_cols:
                cols_to_use.append('SEASON_EXP')
            
            players_list = df[cols_to_use].to_dict(orient='records')
            
            return {
                "team": team_name,
                "source": "nba_api",
                "roster": players_list,
                "roster_count": len(players_list)
            }
        except Exception as e:
            return {"error": f"NBA API error: {str(e)}"}

    # Reuses get_player_stats for each player and nests the results under their names.
    def get_player_comparison(self, player1: str, player2: str) -> dict:
        return {"comparison": "player", "source": "nba_api",
                player1: self.get_player_stats(player1),
                player2: self.get_player_stats(player2)}

    # Same pattern as get_player_comparison but for teams.
    def get_team_comparison(self, team1: str, team2: str) -> dict:
        return {"comparison": "team", "source": "nba_api",
                team1: self.get_team_stats(team1),
                team2: self.get_team_stats(team2)}

    def get_team_rankings(self) -> list:
        try:
            time.sleep(0.6)

            # LeagueStandings returns current standings; index [0] is the main standings table.
            standings = leaguestandings.LeagueStandings()
            df = standings.get_data_frames()[0]
            return df[['TeamName', 'Conference', 'PlayoffRank', 'WINS', 'LOSSES', 'WinPCT']].to_dict(orient='records')
        except Exception as e:
            return [{"error": f"NBA API error: {str(e)}"}]

    def get_top_players(self, stat_category: str = 'PTS', limit: int = 10) -> list:
        try:
            time.sleep(0.6)

            # LeagueLeaders returns players ranked by the given stat abbreviation (e.g. 'PTS', 'AST').
            leaders = leagueleaders.LeagueLeaders(stat_category_abbreviation=stat_category)
            df = leaders.get_data_frames()[0]

            # .head(limit) takes only the top N rows before converting to a list of dicts.
            return df.head(limit)[['PLAYER', 'TEAM', stat_category]].to_dict(orient='records')
        except Exception as e:
            return [{"error": f"NBA API error: {str(e)}"}]

    def get_player_advanced_stats(self, player_name: str) -> dict:
        try:
            player_id = self._find_player_id(player_name)
            if not player_id:
                return {"error": f"'{player_name}' not found."}

            time.sleep(0.6)

            # LeagueDashPlayerStats with Advanced measure is the reliable source
            # for season-level advanced metrics in nba_api.
            advanced = leaguedashplayerstats.LeagueDashPlayerStats(
                measure_type_detailed_defense='Advanced',
                season='2024-25',
                per_mode_detailed='PerGame'
            )
            df = advanced.get_data_frames()[0]

            player_row = df[df['PLAYER_ID'] == player_id]
            if player_row.empty:
                return {"error": f"No advanced stats found for '{player_name}' in 2024-25."}

            row = player_row.iloc[0]
            stats = [{
                'SEASON_ID': '2024-25',
                'PER': row.get('PIE'),
                'TS_PCT': row.get('TS_PCT'),
                'AST_PCT': row.get('AST_PCT'),
                'STL_PCT': row.get('STL_PCT'),
                'BLK_PCT': row.get('BLK_PCT'),
                'USG_PCT': row.get('USG_PCT'),
                'WS': row.get('WS')
            }]
            return {"player": player_name, "source": "nba_api", "advanced_stats": stats}
        except Exception as e:
            return {"error": f"NBA API error: {str(e)}"}