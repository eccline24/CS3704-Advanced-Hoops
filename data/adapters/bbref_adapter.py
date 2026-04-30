from adapters.base_adapter import BaseAdapter
from basketball_reference_web_scraper import client
from basketball_reference_web_scraper.data import Team

# imported as next adapter class
# Claude AI provided structure of the file with TODOs for methods. It also helped debug
# the data structure differences between BBRef and NBA API (name vs first_name/last_name fields)
# prompt: can you give me a structure for an adapter for basketball reference scraper. Include todos for functions
# Can you give me an overview on the client feature in the basketball reference scraper and in general how to use it
# the basketball reference source doesn't work at all , can you give me suggestions for a debug script that would improve this

class BBRefAdapter(BaseAdapter):

    def _find_team_enum(self, team_name: str):
        """Find matching team enum, handling various name formats"""
        if not team_name or not team_name.strip():
            return None

        normalized_input = team_name.lower().strip()

        # Two-pass: exact match is preferred over partial match regardless of list order.
        for team in Team:
            if team.name.lower().replace('_', ' ') == normalized_input:
                return team
        for team in Team:
            if normalized_input in team.name.lower().replace('_', ' '):
                return team

        return None

    def _standardize_player_stats(self, player_data: dict) -> list:
        """Convert BBRef player data to standardized format"""
        
        # Calculate shooting percentages
        fg_pct = 0.0
        if player_data.get('attempted_field_goals', 0) > 0:
            fg_pct = player_data.get('made_field_goals', 0) / player_data.get('attempted_field_goals', 1)
        
        fg3_pct = 0.0
        if player_data.get('attempted_three_point_field_goals', 0) > 0:
            fg3_pct = player_data.get('made_three_point_field_goals', 0) / player_data.get('attempted_three_point_field_goals', 1)
        
        ft_pct = 0.0
        if player_data.get('attempted_free_throws', 0) > 0:
            ft_pct = player_data.get('made_free_throws', 0) / player_data.get('attempted_free_throws', 1)
        
        # Total rebounds = offensive + defensive
        total_rebounds = (player_data.get('offensive_rebounds', 0) or 0) + (player_data.get('defensive_rebounds', 0) or 0)
        
        converted = {
            'PTS': player_data.get('points', 0) or 0,
            'REB': total_rebounds,
            'AST': player_data.get('assists', 0) or 0,
            'BLK': player_data.get('blocks', 0) or 0,
            'STL': player_data.get('steals', 0) or 0,
            'TOV': player_data.get('turnovers', 0) or 0,
            'GP': player_data.get('games_played', 0) or 0,
            'FG_PCT': fg_pct,
            'FG3_PCT': fg3_pct,
            'FT_PCT': ft_pct,
            'SEASON_ID': '2024-25'
        }
        
        return [converted]

    def _get_player_season_totals(self) -> list:
        """Get all players' season totals for current season"""
        try:
            return client.players_season_totals(season_end_year=2025)
        except Exception as e:
            print(f"[BBRef] Error fetching player season totals: {str(e)}")
            return []

    def get_player_stats(self, player_name: str) -> dict:
        """Fetch player stats from Basketball Reference"""
        try:
            if not player_name or not isinstance(player_name, str):
                return {"error": "Invalid player name"}
            
            print(f"[BBRef] Fetching player stats for: {player_name}")
            stats = self._get_player_season_totals()
            
            if not stats:
                return {"error": "No player data available from Basketball Reference"}
            
            print(f"[BBRef] Found {len(stats)} total players")
            
            normalized_input = player_name.lower().strip()
            
            # Search for exact name match
            match = None
            for p in stats:
                player_full_name = p.get('name', '').strip()
                
                if player_full_name.lower() == normalized_input:
                    match = p
                    break
            
            # If no exact match, try partial match
            if not match:
                for p in stats:
                    player_full_name = p.get('name', '').strip()
                    if normalized_input in player_full_name.lower():
                        match = p
                        break
            
            print(f"[BBRef] Found player match: {match.get('name') if match else 'None'}")
            
            if not match:
                return {"error": f"'{player_name}' not found in Basketball Reference database"}
            
            standardized_stats = self._standardize_player_stats(match)
            
            return {
                "player": player_name,
                "source": "basketball_reference",
                "stats": standardized_stats
            }

        except Exception as e:
            print(f"[BBRef] Error in get_player_stats: {str(e)}")
            return {"error": f"Basketball Reference error: {str(e)}"}

    def _get_team_from_players(self, team_name: str) -> dict:
        """Extract team stats by aggregating player stats for that team"""
        try:
            team_enum = self._find_team_enum(team_name)
            if not team_enum:
                return {"error": f"Team '{team_name}' not found"}
            
            stats = self._get_player_season_totals()
            
            # Filter players on this team
            team_players = [p for p in stats if p.get('team') == team_enum]
            
            if not team_players:
                return {"error": f"No players found for {team_name}"}
            
            # Aggregate team stats
            team_stats = {
                'PTS': sum(p.get('points', 0) for p in team_players),
                'REB': sum((p.get('offensive_rebounds', 0) or 0) + (p.get('defensive_rebounds', 0) or 0) for p in team_players),
                'AST': sum(p.get('assists', 0) for p in team_players),
                'BLK': sum(p.get('blocks', 0) for p in team_players),
                'STL': sum(p.get('steals', 0) for p in team_players),
                'TOV': sum(p.get('turnovers', 0) for p in team_players),
                'players_count': len(team_players),
                'SEASON_ID': '2024-25'
            }
            
            # Calculate team shooting percentages
            total_fg = sum(p.get('made_field_goals', 0) for p in team_players)
            total_fga = sum(p.get('attempted_field_goals', 0) for p in team_players)
            team_stats['FG_PCT'] = (total_fg / total_fga) if total_fga > 0 else 0.0
            
            total_fg3 = sum(p.get('made_three_point_field_goals', 0) for p in team_players)
            total_fg3a = sum(p.get('attempted_three_point_field_goals', 0) for p in team_players)
            team_stats['FG3_PCT'] = (total_fg3 / total_fg3a) if total_fg3a > 0 else 0.0
            
            total_ft = sum(p.get('made_free_throws', 0) for p in team_players)
            total_fta = sum(p.get('attempted_free_throws', 0) for p in team_players)
            team_stats['FT_PCT'] = (total_ft / total_fta) if total_fta > 0 else 0.0
            
            return team_stats
            
        except Exception as e:
            print(f"[BBRef] Error getting team stats: {str(e)}")
            return {"error": str(e)}

    def get_team_stats(self, team_name: str) -> dict:
        """Fetch team stats from Basketball Reference"""
        try:
            if not team_name or not isinstance(team_name, str):
                return {"error": "Invalid team name"}
            
            print(f"[BBRef] Fetching team stats for: {team_name}")
            
            team_stats = self._get_team_from_players(team_name)
            
            if "error" in team_stats:
                return team_stats
            
            return {
                "team": team_name,
                "source": "basketball_reference",
                "roster": [team_stats]
            }
            
        except Exception as e:
            print(f"[BBRef] Error in get_team_stats: {str(e)}")
            return {"error": f"Basketball Reference error: {str(e)}"}

    def get_player_comparison(self, player1: str, player2: str) -> dict:
        """Compare two players"""
        stats1 = self.get_player_stats(player1)
        stats2 = self.get_player_stats(player2)

        return {
            "comparison": "player",
            "source": "basketball_reference",
            player1: stats1,
            player2: stats2
        }

    def get_team_comparison(self, team1: str, team2: str) -> dict:
        """Compare two teams"""
        stats1 = self.get_team_stats(team1)
        stats2 = self.get_team_stats(team2)

        return {
            "comparison": "team",
            "source": "basketball_reference",
            team1: stats1,
            team2: stats2
        }

    def get_team_rankings(self) -> list:
        """Fetch team standings"""
        try:
            standings = client.standings(season_end_year=2025)
            
            if not standings:
                return [{"error": "No standings data available"}]
            
            return standings
        except Exception as e:
            return [{"error": f"Basketball Reference error: {str(e)}"}]

    def get_top_players(self, stat_category: str = 'points', limit: int = 10) -> list:
        """Fetch top players by stat"""
        try:
            stats = self._get_player_season_totals()
            
            if not stats:
                return [{"error": "No player data available"}]
            
            # Map stat_category to BBRef field names
            field_mapping = {
                'points': 'points',
                'PTS': 'points',
                'rebounds': 'offensive_rebounds',
                'REB': 'offensive_rebounds',
                'assists': 'assists',
                'AST': 'assists'
            }
            
            bbref_field = field_mapping.get(stat_category, 'points')
            
            # Filter and sort
            valid_stats = [s for s in stats if s.get(bbref_field) is not None]
            sorted_stats = sorted(valid_stats, key=lambda x: x.get(bbref_field, 0), reverse=True)
            
            # Standardize and return top N
            standardized = []
            for player in sorted_stats[:limit]:
                std = self._standardize_player_stats(player)
                standardized.extend(std)
            
            return standardized
        except Exception as e:
            return [{"error": f"Basketball Reference error: {str(e)}"}]
        
    def get_player_advanced_stats(self, player_name: str) -> dict:
        try:
            if not player_name or not isinstance(player_name, str):
                return {"error": "Invalid player name"}

            stats = self._get_player_season_totals()
        
            if not stats:
                return {"error": "No player data available"}

            normalized_input = player_name.lower().strip()
            match = None
        
            for p in stats:
                if p.get('name', '').strip().lower() == normalized_input:
                    match = p
                    break

            if not match:
                return {"error": f"'{player_name}' not found"}

            # BBRef has limited advanced stats in players_season_totals
            # Extract what's available
            advanced = {
                'SEASON_ID': '2024-25',
                'PER': match.get('player_efficiency_rating'),
                'TS_PCT': match.get('true_shooting_percentage'),
                'USG_PCT': match.get('usage_percentage'),
                'WS': match.get('win_shares')
            }

            return {
                "player": player_name,
                "source": "basketball_reference",
                "advanced_stats": [advanced]
            }
        except Exception as e:
            return {"error": f"Basketball Reference error: {str(e)}"}