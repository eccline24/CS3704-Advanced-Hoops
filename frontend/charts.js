/*

Used github Copilot to update this file

Now can you create the chart.js file that aligns with the index.html file. Id like the two charts to be bar charts of the top players and team rankings, make sure its the same theme as the index.html file,
creates functions "renderTopPlayers", and "renderTeamRankings". Also need it to check for static data and if it doesnt exists to get it from /api/top-players and /api/team-rankings. 
Also would like it to have functions fetchSourceComparison() and fetchPlayerComparison(). Format the results in a modern way that doesnt just list numbers. Have had problems with errors also so extra error handling
would be good. Can add any extra features you feel will be useful for this as well.

My team source comparisons arent working. Can you give me a debug script to help figure out the issue

Id like to add a button to toggle the player stats and give advanced stats as well. What would you suggest for this
*/
// Render the top scorers bar chart
const comparisonCache = new Map();

function setButtonLoading(buttonId, isLoading, loadingText, defaultText) {
    const btn = document.getElementById(buttonId);
    if (!btn) return;
    btn.disabled = isLoading;
    btn.style.opacity = isLoading ? '0.7' : '1';
    btn.style.cursor = isLoading ? 'wait' : 'pointer';
    btn.textContent = isLoading ? loadingText : defaultText;
}

function swapPlayers() {
    const p1Input = document.getElementById('player1-input');
    const p2Input = document.getElementById('player2-input');
    if (!p1Input || !p2Input) return;

    const temp = p1Input.value;
    p1Input.value = p2Input.value;
    p2Input.value = temp;

    if (p1Input.value.trim() && p2Input.value.trim()) {
        fetchPlayerComparison();
    }
}

function renderTopPlayers(data) {
    console.log('Rendering top players with data:', data);

    const labels = data.map(p => p.PLAYER);
    const pts = data.map(p => p.PTS);

    const ctx = document.getElementById('topPlayersChart');
    if (!ctx) {
        console.error('Canvas element topPlayersChart not found');
        return;
    }

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Points',
                data: pts,
                backgroundColor: '#60a5fa',
                borderColor: '#3b82f6',
                borderWidth: 2,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: false,
                    ticks: {
                        color: '#e2e8f0'
                    },
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: '#e2e8f0'
                    },
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    }
                }
            }
        }
    });
}

// Render the team standings chart
function renderTeamRankings(data) {
    console.log('Rendering team rankings with data:', data);

    const labels = data.map(t => t.TeamName);
    const winPct = data.map(t => Number(t.WinPCT));

    const ctx = document.getElementById('teamRankingsChart');
    if (!ctx) {
        console.error('Canvas element teamRankingsChart not found');
        return;
    }

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Win %',
                data: winPct,
                backgroundColor: '#f87171',
                borderColor: '#dc2626',
                borderWidth: 2,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    max: 1,
                    ticks: {
                        color: '#e2e8f0',
                        callback: function (value) {
                            return (value * 100) + '%';
                        }
                    },
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    }
                },
                x: {
                    ticks: {
                        color: '#e2e8f0'
                    },
                    grid: {
                        color: 'rgba(148, 163, 184, 0.1)'
                    }
                }
            }
        }
    });
}

function renderTopAssists(data) {
    const labels = data.map(p => p.PLAYER);
    const ast = data.map(p => p.AST);

    const ctx = document.getElementById('topAssistsChart');
    if (!ctx) return;

    new Chart(ctx, {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Assists',
                data: ast,
                backgroundColor: '#34d399',
                borderColor: '#10b981',
                borderWidth: 2,
                borderRadius: 6
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: { legend: { display: false } },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: { color: '#e2e8f0' },
                    grid: { color: 'rgba(148, 163, 184, 0.1)' }
                },
                x: {
                    ticks: { color: '#e2e8f0' },
                    grid: { color: 'rgba(148, 163, 184, 0.1)' }
                }
            }
        }
    });
}

function renderConferenceWinSplit(rankings) {
    const ctx = document.getElementById('conferenceWinChart');
    if (!ctx || !rankings?.length) return;

    const grouped = rankings.reduce((acc, team) => {
        const conf = team.Conference || 'Unknown';
        acc[conf] = acc[conf] || { sum: 0, count: 0 };
        acc[conf].sum += Number(team.WinPCT || 0);
        acc[conf].count += 1;
        return acc;
    }, {});

    const labels = Object.keys(grouped);
    const values = labels.map(conf => {
        const { sum, count } = grouped[conf];
        return count ? (sum / count) * 100 : 0;
    });

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data: values,
                backgroundColor: ['#60a5fa', '#f87171', '#a78bfa'],
                borderColor: '#0f172a',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: { labels: { color: '#e2e8f0' } },
                tooltip: {
                    callbacks: {
                        label(context) {
                            return `${context.label}: ${context.parsed.toFixed(1)}% avg win rate`;
                        }
                    }
                }
            }
        }
    });
}

// Initialize charts on page load
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOMContentLoaded event fired');
    console.log('Static data available:', !!window.__TOP_PLAYERS__, !!window.__TEAM_RANKINGS__);

    // Use injected/static data if available, otherwise fetch from API
    const topPlayersPromise = window.__TOP_PLAYERS__
        ? Promise.resolve(window.__TOP_PLAYERS__)
        : fetch('/api/top-players').then(res => res.json());
    const topAssistsPromise = fetch('/api/top-players?stat=AST').then(res => res.json());

    const teamRankingsPromise = window.__TEAM_RANKINGS__
        ? Promise.resolve(window.__TEAM_RANKINGS__)
        : fetch('/api/team-rankings').then(res => res.json());

    topPlayersPromise
        .then(data => {
            console.log('Top players data loaded:', data);
            renderTopPlayers(data);
        })
        .catch(err => console.error('Top players error:', err));

    teamRankingsPromise
        .then(data => {
            console.log('Team rankings data loaded:', data);
            renderTeamRankings(data);
            renderConferenceWinSplit(data);
        })
        .catch(err => console.error('Team rankings error:', err));

    topAssistsPromise
        .then(data => {
            console.log('Top assists data loaded:', data);
            renderTopAssists(data);
        })
        .catch(err => console.error('Top assists error:', err));

    const sourceInput = document.getElementById('compare-source-input');
    if (sourceInput) {
        sourceInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') fetchSourceComparison();
        });
    }

    const player1Input = document.getElementById('player1-input');
    const player2Input = document.getElementById('player2-input');
    [player1Input, player2Input].forEach(input => {
        if (!input) return;
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') fetchPlayerComparison();
        });
    });
});

// Format stats for display
function formatPlayerStats(stats) {
    if (!stats || stats.length === 0) {
        return '<p class="error">No stats available</p>';
    }

    // Group by season and create table rows
    const rows = stats.map(s => `
        <tr>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2);">${s.SEASON_ID}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${s.GP}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center; color: #fbbf24;">${s.PTS}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${s.REB}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${s.AST}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${(s.FG_PCT * 100).toFixed(1)}%</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${(s.FG3_PCT * 100).toFixed(1)}%</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${(s.FT_PCT * 100).toFixed(1)}%</td>
        </tr>
    `).join('');

    return `
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                <thead>
                    <tr style="background: rgba(96, 165, 250, 0.1); border-bottom: 2px solid rgba(96, 165, 250, 0.3);">
                        <th style="padding: 0.75rem; text-align: left; color: #93c5fd;">Season</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">GP</th>
                        <th style="padding: 0.75rem; text-align: center; color: #fbbf24;">PTS</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">REB</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">AST</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">FG%</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">3P%</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">FT%</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows}
                </tbody>
            </table>
        </div>
    `;
}

// Calculate career averages
function getCareerAverages(stats) {
    if (!stats || stats.length === 0) return null;

    const validStats = stats.filter(s => s.PTS && s.GP && s.GP > 0); // Only valid seasons with games played

    if (validStats.length === 0) return null;

    // Calculate per-game totals first
    const perGameStats = validStats.map(s => ({
        PPG: s.PTS / s.GP,
        RPG: s.REB / s.GP,
        APG: s.AST / s.GP,
        BPG: s.BLK / s.GP,
        SPG: s.STL / s.GP,
        FG_PCT: s.FG_PCT,
        FG3_PCT: s.FG3_PCT,
        FT_PCT: s.FT_PCT
    }));

    // Average the per-game stats across all seasons
    const count = perGameStats.length;
    const totals = perGameStats.reduce((acc, s) => ({
        PPG: acc.PPG + s.PPG,
        RPG: acc.RPG + s.RPG,
        APG: acc.APG + s.APG,
        BPG: acc.BPG + s.BPG,
        SPG: acc.SPG + s.SPG,
        FG_PCT: acc.FG_PCT + s.FG_PCT,
        FG3_PCT: acc.FG3_PCT + s.FG3_PCT,
        FT_PCT: acc.FT_PCT + s.FT_PCT
    }), { PPG: 0, RPG: 0, APG: 0, BPG: 0, SPG: 0, FG_PCT: 0, FG3_PCT: 0, FT_PCT: 0 });

    return {
        PPG: (totals.PPG / count).toFixed(1),
        RPG: (totals.RPG / count).toFixed(1),
        APG: (totals.APG / count).toFixed(1),
        BPG: (totals.BPG / count).toFixed(1),
        SPG: (totals.SPG / count).toFixed(1),
        FG_PCT: ((totals.FG_PCT / count) * 100).toFixed(1),
        FG3_PCT: ((totals.FG3_PCT / count) * 100).toFixed(1),
        FT_PCT: ((totals.FT_PCT / count) * 100).toFixed(1)
    };
}

// Format career stats card
function formatCareerCard(player, stats) {
    const avg = getCareerAverages(stats);
    if (!avg) return '';

    return `
        <div style="background: rgba(96, 165, 250, 0.1); border: 1px solid rgba(96, 165, 250, 0.3); border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem;">
            <h4 style="color: #93c5fd; margin-bottom: 1rem; font-size: 1.1rem;">Career Averages</h4>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem;">
                <div style="text-align: center;">
                    <div style="color: #fbbf24; font-size: 1.5rem; font-weight: 700;">${avg.PPG}</div>
                    <div style="color: #94a3b8; font-size: 0.85rem;">Points Per Game</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #60a5fa; font-size: 1.5rem; font-weight: 700;">${avg.RPG}</div>
                    <div style="color: #94a3b8; font-size: 0.85rem;">Rebounds Per Game</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #34d399; font-size: 1.5rem; font-weight: 700;">${avg.APG}</div>
                    <div style="color: #94a3b8; font-size: 0.85rem;">Assists Per Game</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #a78bfa; font-size: 1.5rem; font-weight: 700;">${avg.FG_PCT}%</div>
                    <div style="color: #94a3b8; font-size: 0.85rem;">Field Goal %</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #f87171; font-size: 1.5rem; font-weight: 700;">${avg.FG3_PCT}%</div>
                    <div style="color: #94a3b8; font-size: 0.85rem;">3-Point %</div>
                </div>
                <div style="text-align: center;">
                    <div style="color: #fb923c; font-size: 1.5rem; font-weight: 700;">${avg.FT_PCT}%</div>
                    <div style="color: #94a3b8; font-size: 0.85rem;">Free Throw %</div>
                </div>
            </div>
        </div>
    `;
}

// Fetch and display comparison between NBA API and Basketball Reference
async function fetchSourceComparison() {
    const name = document.getElementById('compare-source-input').value.trim();
    const type = document.getElementById('compare-source-type').value;
    const resultDiv = document.getElementById('source-comparison-result');

    if (!name) {
        resultDiv.innerHTML = `<p class="error">Please enter a player or team name.</p>`;
        return;
    }

    const endpoint = `/api/compare/sources/${type}/${encodeURIComponent(name)}`;
    const cacheKey = `source:${endpoint}`;

    try {
        setButtonLoading('compare-source-btn', true, 'Comparing...', 'Compare');
        resultDiv.innerHTML = `<p class="loading">Loading...</p>`;

        let data = comparisonCache.get(cacheKey);
        if (!data) {
            const resp = await fetch(endpoint);
            data = await resp.json();
            comparisonCache.set(cacheKey, data);
        }

        if (data.error) {
            resultDiv.innerHTML = `<p class="error">Error: ${data.error}</p>`;
            return;
        }

        // Handle both player and team data
        let nbaHTML = `<h5>NBA API</h5>`;
        if (data.nba_api && data.nba_api.stats) {
            nbaHTML += formatCareerCard(name, data.nba_api.stats);
            nbaHTML += formatPlayerStats(data.nba_api.stats);
        } else if (data.nba_api && data.nba_api.roster) {
            nbaHTML += formatTeamStats(data.nba_api.roster);
        } else if (data.nba_api && data.nba_api.error) {
            nbaHTML += `<p class="error">${data.nba_api.error}</p>`;
        } else {
            nbaHTML += `<p class="error">No data available</p>`;
        }

        let bbrefHTML = `<h5>Basketball Reference</h5>`;
        if (data.bbref && data.bbref.stats) {
            bbrefHTML += formatCareerCard(name, data.bbref.stats);
            bbrefHTML += formatPlayerStats(data.bbref.stats);
        } else if (data.bbref && data.bbref.roster) {
            bbrefHTML += formatTeamStats(data.bbref.roster);
        } else if (data.bbref && data.bbref.error) {
            bbrefHTML += `<p class="error">${data.bbref.error}</p>`;
        } else {
            bbrefHTML += `<p class="error">No data available</p>`;
        }

        resultDiv.innerHTML = `
            <div class="comparison-grid">
                <div class="comparison-item">
                    ${nbaHTML}
                </div>
                <div class="comparison-item">
                    ${bbrefHTML}
                </div>
            </div>
        `;

    } catch (err) {
        resultDiv.innerHTML = `<p class="error">Failed to fetch comparison data: ${err.message}</p>`;
    } finally {
        setButtonLoading('compare-source-btn', false, 'Comparing...', 'Compare');
    }
}

// Format team stats display
function formatTeamStats(roster) {
    if (!roster || roster.length === 0) {
        return '<p class="error">No roster data available</p>';
    }

    const team = roster[0];
    
    // Handle aggregated team stats
    if (team.players_count !== undefined) {
        return `
            <div style="background: rgba(96, 165, 250, 0.1); border: 1px solid rgba(96, 165, 250, 0.3); border-radius: 8px; padding: 1.5rem; margin-bottom: 1.5rem;">
                <h4 style="color: #93c5fd; margin-bottom: 1rem;">Team Totals</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(120px, 1fr)); gap: 1rem;">
                    <div style="text-align: center;">
                        <div style="color: #fbbf24; font-size: 1.5rem; font-weight: 700;">${team.players_count}</div>
                        <div style="color: #94a3b8; font-size: 0.85rem;">Players</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="color: #fbbf24; font-size: 1.5rem; font-weight: 700;">${team.PTS}</div>
                        <div style="color: #94a3b8; font-size: 0.85rem;">Total Points</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="color: #60a5fa; font-size: 1.5rem; font-weight: 700;">${team.REB}</div>
                        <div style="color: #94a3b8; font-size: 0.85rem;">Total Rebounds</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="color: #34d399; font-size: 1.5rem; font-weight: 700;">${team.AST}</div>
                        <div style="color: #94a3b8; font-size: 0.85rem;">Total Assists</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="color: #a78bfa; font-size: 1.5rem; font-weight: 700;">${(team.FG_PCT * 100).toFixed(1)}%</div>
                        <div style="color: #94a3b8; font-size: 0.85rem;">FG%</div>
                    </div>
                    <div style="text-align: center;">
                        <div style="color: #f87171; font-size: 1.5rem; font-weight: 700;">${(team.FG3_PCT * 100).toFixed(1)}%</div>
                        <div style="color: #94a3b8; font-size: 0.85rem;">3P%</div>
                    </div>
                </div>
            </div>
        `;
    }
    
    // Handle player roster
    const rows = roster.map(p => `
        <tr>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2);">${p.PLAYER}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${p.NUM || '-'}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${p.POSITION || '-'}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${p.HEIGHT || '-'}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${p.WEIGHT || '-'}</td>
        </tr>
    `).join('');

    return `
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                <thead>
                    <tr style="background: rgba(96, 165, 250, 0.1); border-bottom: 2px solid rgba(96, 165, 250, 0.3);">
                        <th style="padding: 0.75rem; text-align: left; color: #93c5fd;">Player</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">#</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">Position</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">Height</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">Weight</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows}
                </tbody>
            </table>
        </div>
    `;
}
let showAdvancedStats = false;

function toggleAdvancedStats(buttonEl) {
    showAdvancedStats = !showAdvancedStats;
    const btn = buttonEl || document.getElementById('advanced-stats-toggle');
    if (btn) {
        btn.style.background = showAdvancedStats ? 'rgba(96, 165, 250, 0.8)' : 'rgba(96, 165, 250, 0.5)';
        btn.textContent = showAdvancedStats ? '📊 Hide Advanced Stats' : '📊 Show Advanced Stats';
    }

    // Re-fetch comparison with advanced stats if already loaded
    const p1 = document.getElementById('player1-input').value.trim();
    const p2 = document.getElementById('player2-input').value.trim();
    if (p1 && p2) {
        fetchPlayerComparison();
    }
}

function toggleStatsHelp() {
    const helpBox = document.getElementById('stats-help-box');
    helpBox.style.display = helpBox.style.display === 'none' ? 'block' : 'none';
}

async function fetchPlayerComparison() {
    const p1 = document.getElementById('player1-input').value.trim();
    const p2 = document.getElementById('player2-input').value.trim();
    const resultDiv = document.getElementById('player-comparison-result');

    if (!p1 || !p2) {
        resultDiv.innerHTML = `<p class="error">Please enter both player names.</p>`;
        return;
    }
    if (p1.toLowerCase() === p2.toLowerCase()) {
        resultDiv.innerHTML = `<p class="error">Choose two different players for a useful comparison.</p>`;
        return;
    }

    // Use advanced endpoint if toggle is on
    const endpoint = showAdvancedStats
        ? `/api/compare/players/${encodeURIComponent(p1)}/${encodeURIComponent(p2)}/advanced`
        : `/api/compare/players/${encodeURIComponent(p1)}/${encodeURIComponent(p2)}`;
    const cacheKey = `players:${endpoint}`;

    try {
        setButtonLoading('compare-players-btn', true, 'Comparing...', 'Compare Players');
        resultDiv.innerHTML = `<p class="loading">Loading...</p>`;

        let data = comparisonCache.get(cacheKey);
        if (!data) {
            const resp = await fetch(endpoint);
            data = await resp.json();
            comparisonCache.set(cacheKey, data);
        }

        if (data.error) {
            resultDiv.innerHTML = `<p class="error">Error: ${data.error}</p>`;
            return;
        }

        const players = data.players;

        if (!players || players.length < 2) {
            resultDiv.innerHTML = `<p class="error">Invalid comparison data.</p>`;
            return;
        }

        const playerHTML = players.map(p => {
            let statsHTML = '';

            if (showAdvancedStats) {
                // Advanced stats display
                if (p.nba_api && p.nba_api.advanced_stats) {
                    statsHTML += `<h5 style="margin-top: 1rem;">NBA API Advanced Stats</h5>`;
                    statsHTML += formatAdvancedStats(p.nba_api.advanced_stats);
                } else if (p.nba_api && p.nba_api.error) {
                    statsHTML += `<h5 style="margin-top: 1rem;">NBA API Advanced Stats</h5><p class="error">${p.nba_api.error}</p>`;
                }
                if (p.bbref && p.bbref.advanced_stats) {
                    statsHTML += `<h5 style="margin-top: 1rem;">BBRef Advanced Stats</h5>`;
                    statsHTML += formatAdvancedStats(p.bbref.advanced_stats);
                } else if (p.bbref && p.bbref.error) {
                    statsHTML += `<h5 style="margin-top: 1rem;">BBRef Advanced Stats</h5><p class="error">${p.bbref.error}</p>`;
                }
            } else {
                // Regular stats display
                if (p.nba_api && p.nba_api.stats) {
                    statsHTML += `<h5 style="margin-top: 1rem;">NBA API Stats</h5>`;
                    statsHTML += formatCareerCard(p.name, p.nba_api.stats);
                    statsHTML += formatPlayerStats(p.nba_api.stats);
                }
                if (p.bbref && p.bbref.stats) {
                    statsHTML += `<h5 style="margin-top: 1rem;">Basketball Reference Stats</h5>`;
                    statsHTML += formatCareerCard(p.name, p.bbref.stats);
                    statsHTML += formatPlayerStats(p.bbref.stats);
                }
            }

            return `
                <div class="comparison-item">
                    <h4>${p.name}</h4>
                    ${statsHTML}
                </div>
            `;
        }).join('');

        resultDiv.innerHTML = `<div class="comparison-grid">${playerHTML}</div>`;

    } catch (err) {
        resultDiv.innerHTML = `<p class="error">Failed to fetch: ${err.message}</p>`;
    } finally {
        setButtonLoading('compare-players-btn', false, 'Comparing...', 'Compare Players');
    }
}

function formatAdvancedStats(stats) {
    if (!stats || stats.length === 0) {
        return '<p class="error">No advanced stats available</p>';
    }

    const fmtDecimal = (value, digits = 2) => {
        if (value === null || value === undefined || Number.isNaN(Number(value))) return 'N/A';
        return Number(value).toFixed(digits);
    };

    const fmtPercent = value => {
        if (value === null || value === undefined || Number.isNaN(Number(value))) return 'N/A';
        return `${(Number(value) * 100).toFixed(1)}%`;
    };

    const rows = stats.map(s => `
        <tr>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2);">${s.SEASON_ID}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${fmtDecimal(s.PER, 2)}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${fmtPercent(s.TS_PCT)}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${fmtPercent(s.AST_PCT)}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${fmtPercent(s.STL_PCT)}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${fmtPercent(s.BLK_PCT)}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${fmtPercent(s.USG_PCT)}</td>
            <td style="padding: 0.75rem; border-bottom: 1px solid rgba(148, 163, 184, 0.2); text-align: center;">${fmtDecimal(s.WS, 1)}</td>
        </tr>
    `).join('');

    return `
        <div style="overflow-x: auto;">
            <table style="width: 100%; border-collapse: collapse; font-size: 0.85rem;">
                <thead>
                    <tr style="background: rgba(96, 165, 250, 0.1); border-bottom: 2px solid rgba(96, 165, 250, 0.3);">
                        <th style="padding: 0.75rem; text-align: left; color: #93c5fd;">Season</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">PER</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">TS%</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">AST%</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">STL%</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">BLK%</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">USG%</th>
                        <th style="padding: 0.75rem; text-align: center; color: #93c5fd;">WS</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows}
                </tbody>
            </table>
        </div>
    `;
}