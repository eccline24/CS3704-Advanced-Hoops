from adapters.nba_api_adapter import NBAApiAdapter
from adapters.bbref_adapter import BBRefAdapter

# Claude AI provided structure with functions and marked TODOs
# prompt: can you give me a data service class outline in java with todos for each method. I want to use an adapter method for multiple data sources
# Central service that decides which adapter to use. 
class DataService:

    def __init__(self, source: str = 'nba_api'):
        if source == 'nba_api':
            self.adapter = NBAApiAdapter()
        elif source == 'bbref':
            self.adapter = BBRefAdapter()
        else:
            raise ValueError(f"Unknown source. Use 'nba_api' or 'bbref'.")

        self.source = source

    # gets players stats
    def get_player_stats(self, player_name: str) -> dict:
        return self.adapter.get_player_stats(player_name)

    # gets team stats
    def get_team_stats(self, team_name: str) -> dict:
        return self.adapter.get_team_stats(team_name)

    # compares two players
    def get_player_comparison(self, player1: str, player2: str) -> dict:
        return self.adapter.get_player_comparison(player1, player2)

    # compares two teams
    def get_team_comparison(self, team1: str, team2: str) -> dict:
        return self.adapter.get_team_comparison(team1, team2)

    # gets team rankings
    def get_team_rankings(self) -> list:
        return self.adapter.get_team_rankings()

    # gets top players by a stat category
    def get_top_players(self, stat_category: str, limit: int = 10) -> list:
        return self.adapter.get_top_players(stat_category, limit)


# Quick manual test
# Claude AI provided to ensure code works
if __name__ == "__main__":
    service = DataService(source='nba_api')

    print("=== Top 5 Scorers ===")
    top = service.get_top_players('PTS', limit=5)
    for p in top:
        print(p)

    print("\n=== LeBron James Stats (last season) ===")
    lebron = service.get_player_stats("LeBron James")
    if 'stats' in lebron:
        print(lebron['stats'][-1])
    else:
        print(lebron)

    print("\n=== Team Rankings ===")
    rankings = service.get_team_rankings()
    for r in rankings[:5]:
        print(r)