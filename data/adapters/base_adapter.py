from abc import ABC, abstractmethod

# Abstract base class for all data source adapters
# Claude AI provided this file as the general idea was still slightly confusing
# prompt: can you provide base adapter method that will be used for multiple data source adapters?

class BaseAdapter(ABC):
    """
    Abstract base class for all data source adapters.
    Each adapter must implement these methods so the rest
    of the app can call them without knowing the data source.
    """

    @abstractmethod
    def get_player_stats(self, player_name: str) -> dict:
        """Fetch stats for a single player by name."""
        pass

    @abstractmethod
    def get_team_stats(self, team_name: str) -> dict:
        """Fetch stats for a single team by name."""
        pass

    @abstractmethod
    def get_player_comparison(self, player1: str, player2: str) -> dict:
        """Fetch and compare stats for two players."""
        pass

    @abstractmethod
    def get_team_comparison(self, team1: str, team2: str) -> dict:
        """Fetch and compare stats for two teams."""
        pass

    @abstractmethod
    def get_team_rankings(self) -> list:
        """Fetch current team rankings."""
        pass

    @abstractmethod
    def get_top_players(self, stat_category: str, limit: int = 10) -> list:
        """Fetch top players by a given stat category."""
        pass