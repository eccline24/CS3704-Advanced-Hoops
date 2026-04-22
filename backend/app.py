import sys
import os

# Allow importing from data/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data'))

from flask import Flask, jsonify, send_from_directory, request
from data_service import DataService

app = Flask(__name__, static_folder='../frontend')

# Default service (NBA API)
nba_service = DataService(source='nba_api')
bbref_service = DataService(source='bbref')


# ------------------------
# Static frontend
# ------------------------

@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)


# ------------------------
# Charts endpoints
# ------------------------

@app.route('/api/top-players')
def top_players():
    try:
        return jsonify(nba_service.get_top_players('PTS', limit=10))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/team-rankings')
def team_rankings():
    try:
        return jsonify(nba_service.get_team_rankings())
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ------------------------
# Single entity endpoints
# ------------------------

@app.route('/api/player/<name>')
def player_stats(name):
    try:
        return jsonify(nba_service.get_player_stats(name))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/team/<name>')
def team_stats(name):
    try:
        return jsonify(nba_service.get_team_stats(name))
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ------------------------
# Player comparison (SAME SOURCE)
# ------------------------

@app.route('/api/compare/players')
def compare_players():
    try:
        p1 = request.args.get('player1')
        p2 = request.args.get('player2')

        if not p1 or not p2:
            return jsonify({'error': 'Two players required'}), 400

        result = nba_service.get_player_comparison(p1, p2)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ------------------------
# Team comparison (SAME SOURCE)
# ------------------------

@app.route('/api/compare/teams')
def compare_teams():
    try:
        t1 = request.args.get('team1')
        t2 = request.args.get('team2')

        if not t1 or not t2:
            return jsonify({'error': 'Two teams required'}), 400

        result = nba_service.get_team_comparison(t1, t2)
        return jsonify(result)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ------------------------
# Cross-source comparison (YOUR FEATURE)
# ------------------------

@app.route('/api/compare/sources/player/<name>')
def compare_sources_player(name):
    try:
        return jsonify({
            'player': name,
            'nba_api': nba_service.get_player_stats(name),
            'bbref': bbref_service.get_player_stats(name)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compare/sources/team/<name>')
def compare_sources_team(name):
    try:
        return jsonify({
            'team': name,
            'nba_api': nba_service.get_team_stats(name),
            'bbref': bbref_service.get_team_stats(name)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ------------------------
# Player comparison (CROSS-SOURCE)
# ------------------------

@app.route('/api/compare/players/<p1>/<p2>')
def compare_players_cross(p1, p2):
    return jsonify({
        "players": [
            {
                "name": p1,
                "nba_api": nba_service.get_player_stats(p1),
                "bbref": bbref_service.get_player_stats(p1)
            },
            {
                "name": p2,
                "nba_api": nba_service.get_player_stats(p2),
                "bbref": bbref_service.get_player_stats(p2)
            }
        ]
    })


# ------------------------
# Run server
# ------------------------

if __name__ == '__main__':
    app.run(debug=True)