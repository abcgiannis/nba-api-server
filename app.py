from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return jsonify({
        "status": "NBA API Server is running",
        "endpoints": [
            "/api/players?search=...",
            "/api/games?date=YYYY-MM-DD",
            "/api/boxscore?game_id=...",
            "/api/player-stats?player_id=..."
        ]
    })

@app.route('/api/players')
def search_players():
    search = request.args.get('search', 'LeBron')
    url = "https://www.balldontlie.io/api/v1/players"
    params = {"search": search, "per_page": 10}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        players = []
        for p in data.get("data", []):
            players.append({
                "id": p["id"],
                "first_name": p["first_name"],
                "last_name": p["last_name"],
                "team": p.get("team", {}).get("full_name", "N/A")
            })
        return jsonify(players)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/games')
def get_games():
    date = request.args.get('date', '')
    url = "https://www.balldontlie.io/api/v1/games"
    params = {"dates[]": date, "per_page": 50}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        games = []
        for g in data.get("data", []):
            games.append({
                "id": g["id"],
                "date": g["date"],
                "home_team": g["home_team"]["full_name"],
                "away_team": g["visitor_team"]["full_name"],
                "home_score": g.get("home_team_score"),
                "away_score": g.get("visitor_team_score"),
                "status": g["status"]
            })
        return jsonify(games)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/boxscore')
def get_boxscore():
    game_id = request.args.get('game_id', '')
    url = f"https://www.balldontlie.io/api/v1/box_scores"
    params = {"game_id": game_id}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/player-stats')
def get_player_stats():
    player_id = request.args.get('player_id', '')
    url = "https://www.balldontlie.io/api/v1/stats"
    params = {"player_ids[]": player_id, "per_page": 10}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        stats = []
        for s in data.get("data", []):
            stats.append({
                "game_id": s["game"]["id"],
                "date": s["game"]["date"],
                "pts": s.get("pts"),
                "reb": s.get("reb"),
                "ast": s.get("ast"),
                "stl": s.get("stl"),
                "blk": s.get("blk"),
                "min": s.get("min")
            })
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
