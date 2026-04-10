import sys
import os

# Allow importing from data/ directory
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'data'))

from flask import Flask, jsonify, send_from_directory
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


if __name__ == '__main__':
    app.run(debug=True)
