// Render the top scorers bar chart
function renderTopPlayers(data) {
    const labels = data.map(p => p.PLAYER);
    const pts = data.map(p => p.PTS);

    new Chart(document.getElementById('topPlayersChart'), {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Points',
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

// Render the team standings chart
function renderTeamRankings(data) {
    const labels = data.map(t => t.TeamName);
    const winPct = data.map(t => Number(t.WinPCT));

    new Chart(document.getElementById('teamRankingsChart'), {
        type: 'bar',
        data: {
            labels,
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

// Initialize charts on page load
document.addEventListener('DOMContentLoaded', () => {

    // Use injected/static data if available, otherwise fetch from API
    const topPlayersPromise = window.__TOP_PLAYERS__
        ? Promise.resolve(window.__TOP_PLAYERS__)
        : fetch('/api/top-players').then(res => res.json());

    const teamRankingsPromise = window.__TEAM_RANKINGS__
        ? Promise.resolve(window.__TEAM_RANKINGS__)
        : fetch('/api/team-rankings').then(res => res.json());

    topPlayersPromise
        .then(renderTopPlayers)
        .catch(err => console.error('Top players error:', err));

    teamRankingsPromise
        .then(renderTeamRankings)
        .catch(err => console.error('Team rankings error:', err));
});

// Fetch and display comparison between NBA API and Basketball Reference
async function fetchSourceComparison() {
    const name = document.getElementById('compare-source-input').value.trim();
    const type = document.getElementById('compare-source-type').value;
    const resultDiv = document.getElementById('source-comparison-result');

    // Validate input
    if (!name) {
        resultDiv.innerHTML = `<p style="color:red;">Please enter a player or team name.</p>`;
        return;
    }

    const endpoint = `/api/compare/sources/${type}/${encodeURIComponent(name)}`;

    try {
        resultDiv.innerHTML = `<p>Loading...</p>`;

        const resp = await fetch(endpoint);
        const data = await resp.json();

        // Handle overall API error
        if (data.error) {
            resultDiv.innerHTML = `<p style="color:red;">Error: ${data.error}</p>`;
            return;
        }

        // Format NBA API section
        const nbaHTML = `
            <h3>NBA API</h3>
            <pre>${JSON.stringify(data.nba_api, null, 2)}</pre>
        `;

        // Format Basketball Reference section with error handling
        let bbrefHTML;
        if (data.bbref && data.bbref.error) {
            bbrefHTML = `
                <h3>Basketball Reference</h3>
                <p style="color:red;">${data.bbref.error}</p>
            `;
        } else {
            bbrefHTML = `
                <h3>Basketball Reference</h3>
                <pre>${JSON.stringify(data.bbref, null, 2)}</pre>
            `;
        }

        // Display both sources side by side
        resultDiv.innerHTML = `
            <div style="display:flex; gap:2rem; align-items:flex-start;">
                <div style="flex:1;">
                    ${nbaHTML}
                </div>
                <div style="flex:1;">
                    ${bbrefHTML}
                </div>
            </div>
        `;

    } catch (err) {
        resultDiv.innerHTML = `
            <p style="color:red;">Failed to fetch comparison data: ${err}</p>
        `;
    }
}
async function fetchPlayerComparison() {
    const p1 = document.getElementById('player1-input').value.trim();
    const p2 = document.getElementById('player2-input').value.trim();
    const resultDiv = document.getElementById('player-comparison-result');

    if (!p1 || !p2) {
        resultDiv.innerHTML = `<p style="color:red;">Please enter both player names.</p>`;
        return;
    }

    const endpoint = `/api/compare/players/${encodeURIComponent(p1)}/${encodeURIComponent(p2)}`;

    try {
        resultDiv.innerHTML = `<p>Loading...</p>`;

        const resp = await fetch(endpoint);
        const data = await resp.json();

        if (data.error) {
            resultDiv.innerHTML = `<p style="color:red;">Error: ${data.error}</p>`;
            return;
        }

        // Format each player
        const players = data.players;

        if (!players || players.length < 2) {
            resultDiv.innerHTML = `<p style="color:red;">Invalid comparison data.</p>`;
            return;
        }

        const playerHTML = players.map(p => `
    <div style="flex:1;">
        <h3>${p.name}</h3>

        <h4>NBA API</h4>
        <pre>${JSON.stringify(p.nba_api, null, 2)}</pre>

        <h4>Basketball Reference</h4>
        ${p.bbref && p.bbref.error
                ? `<p style="color:red;">${p.bbref.error}</p>`
                : `<pre>${JSON.stringify(p.bbref, null, 2)}</pre>`
            }
    </div>
`).join('');

        resultDiv.innerHTML = `
    <div style="display:flex; gap:2rem;">
        ${playerHTML}
    </div>
`;

    } catch (err) {
        resultDiv.innerHTML = `<p style="color:red;">Failed to fetch: ${err}</p>`;
    }
}