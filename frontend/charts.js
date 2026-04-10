document.addEventListener('DOMContentLoaded', function () {

    fetch('/api/top-players')
        .then(res => res.json())
        .then(data => {
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
        })
        .catch(err => console.error('Failed to load top players:', err));

    fetch('/api/team-rankings')
        .then(res => res.json())
        .then(data => {
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
        })
        .catch(err => console.error('Failed to load team rankings:', err));

});
