from adapters.base_adapter import BaseAdapter
from basketball_reference_web_scraper import client
from basketball_reference_web_scraper.data import Team

# implemented after data service file created
# Claude AI provided structure of the file with TODOs for methods. Also gave some helpful hints using client functions from bbref scraper
# prompt: can you give me a strcuture for an adapter for basketball reference scraper. Include todos for functions
# propmt: Can you give me an overview on the client feature in the basketbal reference scraper and in general how to use it

# Implements BaseAdapter using the basketball_reference_web_scraper package,
# which scrapes data from basketball-reference.com.
# Unlike the NBA API adapter, BBRef uses enum values (Team.LAKERS, etc.) to identify teams
# rather than numeric IDs, so a lookup helper is needed to convert a string name to that enum.
class BBRefAdapter(BaseAdapter):

    # BBRef's scraper identifies teams by a Team enum (e.g. Team.GOLDEN_STATE_WARRIORS).
    # This helper converts a plain string like "golden state warriors" into that enum
    # by normalizing underscores and comparing case-insensitively.
    def _find_team_enum(self, team_name: str):
        for team in Team:
            if team.name.lower().replace('_', ' ') == team_name.lower():
                return team
        return None  # No match found

    # Searches Basketball Reference for the player by name and returns their profile data.
    # client.search() returns a dict with a 'players' key; we take the first result.
    def get_player_stats(self, player_name: str) -> dict:
        try:
            results = client.search(term=player_name)
            if not results or not results.get('players'):
                return {"error": f"'{player_name}' not found on Basketball Reference."}

            player_data = results['players'][0]  # Use the best match

            return {
                "player": player_name,
                "source": "basketball_reference",
                "data": player_data
            }
        except Exception as e:
            return {"error": str(e)}

    # Returns the team's game schedule for the 2024-25 season (season_end_year=2025).
    # Note: BBRef doesn't have a direct "team stats" endpoint, so the schedule is used
    # as a proxy for team activity data.
    def get_team_stats(self, team_name: str) -> dict:
        try:
            team_enum = self._find_team_enum(team_name)
            if not team_enum:
                return {"error": f"'{team_name}' not found."}

            schedule = client.team_schedule_for_month(
                team=team_enum,
                season_end_year=2025
            )

            return {
                "team": team_name,
                "source": "basketball_reference",
                "schedule": schedule
            }
        except Exception as e:
            return {"error": str(e)}

    # Fetches each player's stats independently and nests them under their names.
    def get_player_comparison(self, player1: str, player2: str) -> dict:
        stats1 = self.get_player_stats(player1)
        stats2 = self.get_player_stats(player2)

        return {
            "comparison": "player",
            "source": "basketball_reference",
            player1: stats1,
            player2: stats2
        }

    # Same pattern as get_player_comparison but for teams.
    def get_team_comparison(self, team1: str, team2: str) -> dict:
        stats1 = self.get_team_stats(team1)
        stats2 = self.get_team_stats(team2)

        return {
            "comparison": "team",
            "source": "basketball_reference",
            team1: stats1,
            team2: stats2
        }

    # client.standings() returns a list of team standing dicts for the given season.
    def get_team_rankings(self) -> list:
        try:
            standings = client.standings(season_end_year=2025)
            return standings
        except Exception as e:
            return [{"error": str(e)}]

    # client.players_season_totals() returns all players for the season as a list of dicts.
    # We sort by the given stat_category (e.g. 'points') descending and return the top N.
    # Note: stat_category uses BBRef key names like 'points', not NBA API abbreviations like 'PTS'.
    def get_top_players(self, stat_category: str = 'points', limit: int = 10) -> list:
        try:
            stats = client.players_season_totals(season_end_year=2025)
            sorted_stats = sorted(stats, key=lambda x: x.get(stat_category, 0), reverse=True)
            return sorted_stats[:limit]
        except Exception as e:
            return [{"error": str(e)}]