from abc import ABC, abstractmethod

# Abstract base class for all data source adapters
# Claude AI provided this file as the general idea was still slightly confusing
# prompt: can you provide base adapter method that will be used for multiple data source adapters?

# ABC (Abstract Base Class) enforces that every adapter implements all required methods.
class BaseAdapter(ABC):
    """
    Abstract base class for all data source adapters.
    Each adapter must implement these methods so the rest
    of the app can call them without knowing the data source.
    """

    # @abstractmethod prevents this class from being instantiated directly
    @abstractmethod
    def get_player_stats(self, player_name: str) -> dict:
        """Fetch stats for a single player by name."""
        pass

    @abstractmethod
    def get_team_stats(self, team_name: str) -> dict:
        """Fetch stats for a single team by name."""
        pass

    # Takes two player names and returns their stats together
    @abstractmethod
    def get_player_comparison(self, player1: str, player2: str) -> dict:
        """Fetch and compare stats for two players."""
        pass

    # Same idea as get_player_comparison but for teams.
    @abstractmethod
    def get_team_comparison(self, team1: str, team2: str) -> dict:
        """Fetch and compare stats for two teams."""
        pass

    @abstractmethod
    def get_team_rankings(self) -> list:
        """Fetch current team standings/rankings for all teams."""
        pass

    # stat_category lets the caller choose which stat to rank by 
    # limit defaults to 10 so callers don't have to specify it unless they want a different count.
    @abstractmethod
    def get_top_players(self, stat_category: str, limit: int = 10) -> list:
        """Fetch top players sorted by the given stat category."""
        pass

    @abstractmethod
    def get_player_advanced_stats(self, player_name: str) -> dict:
        """Fetch advanced stats for a single player by name."""
        pass