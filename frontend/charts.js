// Draws the top scorers bar chart
function renderTopPlayers(data) {
    const labels = data.map(p => p.PLAYER);
    const pts = data.map(p => p.PTS);

    new Chart(document.getElementById('topPlayersChart'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Points Per Game',
                data: pts,
                backgroundColor: 'rgba(54, 162, 235, 0.7)'
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: false } }
        }
    });
}

// Draws the team standings bar chart
function renderTeamRankings(data) {
    const labels = data.map(t => t.TeamName);
    const winPct = data.map(t => parseFloat(t.WinPCT));

    new Chart(document.getElementById('teamRankingsChart'), {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Win %',
                data: winPct,
                backgroundColor: 'rgba(255, 99, 132, 0.7)'
            }]
        },
        options: {
            responsive: true,
            plugins: { legend: { display: false } },
            scales: { y: { beginAtZero: true, max: 1 } }
        }
    });
}

// On page load, render charts from injected data or fall back to API
document.addEventListener('DOMContentLoaded', function () {

    // Top players: use static data if present, else fetch from API
    if (window.__TOP_PLAYERS__) {
        renderTopPlayers(window.__TOP_PLAYERS__);
    } else {
        fetch('/api/top-players')
            .then(res => res.json())
            .then(renderTopPlayers)
            .catch(err => console.error('Failed to load top players:', err));
    }

    // Team rankings: use static data if present, else fetch from API
    if (window.__TEAM_RANKINGS__) {
        renderTeamRankings(window.__TEAM_RANKINGS__);
    } else {
        fetch('/api/team-rankings')
            .then(res => res.json())
            .then(renderTeamRankings)
            .catch(err => console.error('Failed to load team rankings:', err));
    }

});