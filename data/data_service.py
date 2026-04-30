from adapters.nba_api_adapter import NBAApiAdapter
from adapters.bbref_adapter import BBRefAdapter
from cache import TTLCache, cached

# Claude AI provided structure with functions and marked TODOs
# prompt: can you give me a data service class outline in java with todos for each method. I want to use an adapter method for multiple data sources

# DataService is the single entry point for the rest of the app (backend, tests, etc.).
# It hides which data source is active — callers just call get_player_stats() etc.
# without caring whether it goes to NBA API or Basketball Reference.
class DataService:

    # source controls which adapter gets created. Defaults to 'nba_api'.
    # Raises ValueError immediately if an unsupported source is passed,
    # so misconfiguration is caught at startup rather than at the first API call.
    def __init__(self, source: str = 'nba_api'):
        if source == 'nba_api':
            self.adapter = NBAApiAdapter()
        elif source == 'bbref':
            self.adapter = BBRefAdapter()
        else:
            raise ValueError(f"Unknown source. Use 'nba_api' or 'bbref'.")

        self.source = source
        self._cache = TTLCache()
        self._cache_enabled = True

    def clear_cache(self) -> None:
        self._cache.clear()

    # All methods below delegate to whichever adapter was selected at init,
    # wrapped in @cached so repeat calls with the same args skip the adapter
    # entirely (and therefore skip the rate-limit sleeps inside NBAApiAdapter).
    # TTLs reflect how often each dataset realistically changes.

    @cached(ttl=86400)  # career stats — effectively static intra-day
    def get_player_stats(self, player_name: str) -> dict:
        return self.adapter.get_player_stats(player_name)

    @cached(ttl=86400)  # roster — changes rarely mid-season
    def get_team_stats(self, team_name: str) -> dict:
        return self.adapter.get_team_stats(team_name)

    @cached(ttl=3600)
    def get_player_comparison(self, player1: str, player2: str) -> dict:
        return self.adapter.get_player_comparison(player1, player2)

    @cached(ttl=3600)
    def get_team_comparison(self, team1: str, team2: str) -> dict:
        return self.adapter.get_team_comparison(team1, team2)

    @cached(ttl=3600)  # standings update after each game day
    def get_team_rankings(self) -> list:
        return self.adapter.get_team_rankings()

    @cached(ttl=3600)  # leaderboards update after each game day
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