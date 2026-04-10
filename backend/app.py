import sys
import os

# Allow importing from data/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data'))

from flask import Flask, jsonify, send_from_directory, request
from data_service import DataService

app = Flask(__name__, static_folder='../frontend')

service = DataService(source='nba_api')


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)


@app.route('/api/top-players')
def top_players():
    try:
        players = service.get_top_players('PTS', limit=10)
        return jsonify(players)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/team-rankings')
def team_rankings():
    try:
        rankings = service.get_team_rankings()
        return jsonify(rankings)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/player/<name>')
def player_stats(name):
    try:
        stats = service.get_player_stats(name)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/team/<name>')
def team_stats(name):
    try:
        stats = service.get_team_stats(name)
        return jsonify(stats)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compare/players')
def compare_players():
    try:
        player1 = request.args.get('player1')
        player2 = request.args.get('player2')
        if not player1 or not player2:
            return jsonify({'error': 'Two players required'}), 400
        result = service.get_player_comparison(player1, player2)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/compare/teams')
def compare_teams():
    try:
        team1 = request.args.get('team1')
        team2 = request.args.get('team2')
        if not team1 or not team2:
            return jsonify({'error': 'Two teams required'}), 400
        result = service.get_team_comparison(team1, team2)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
