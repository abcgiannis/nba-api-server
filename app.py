from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import time

app = Flask(__name__)
CORS(app)

# Balldontlie API (δωρεάν, δημόσιο, χωρίς κλειδί)
BASE_URL = "https://www.balldontlie.io/api/v1"

def safe_get(url, params=None, retries=2):
    """Κάνει GET request με επανάληψη σε περίπτωση αποτυχίας."""
    for i in range(retries):
        try:
            resp = requests.get(url, params=params, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            else:
                time.sleep(0.5)
        except Exception as e:
            if i == retries - 1:
                return {"error": str(e)}
            time.sleep(0.5)
    return {"error": "Max retries exceeded"}

@app.route('/')
def home():
    return jsonify({
        "status": "NBA API Server is running",
        "data_source": "balldontlie.io (free, public)",
        "endpoints": [
            "/api/players?search=...",
            "/api/games?date=YYYY-MM-DD",
            "/api/player-stats?player_id=...",
            "/api/boxscore?game_id=..."
        ]
    })

@app.route('/api/players')
def search_players():
    search = request.args.get('search', 'LeBron')
    url = f"{BASE_URL}/players"
    params = {"search": search, "per_page": 10}
    data = safe_get(url, params)
    if "error" in data:
        return jsonify(data), 500
    players = []
    for p in data.get("data", []):
        players.append({
            "id": p["id"],
            "first_name": p["first_name"],
            "last_name": p["last_name"],
            "team": p.get("team", {}).get("full_name", "N/A")
        })
    return jsonify(players)

@app.route('/api/games')
def get_games():
    date = request.args.get('date', '2026-05-13')
    url = f"{BASE_URL}/games"
    params = {"dates[]": date, "per_page": 50}
    data = safe_get(url, params)
    if "error" in data:
        return jsonify(data), 500
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

@app.route('/api/player-stats')
def get_player_stats():
    player_id = request.args.get('player_id')
    if not player_id:
        return jsonify({"error": "player_id is required"}), 400
    url = f"{BASE_URL}/stats"
    params = {"player_ids[]": player_id, "per_page": 5}  # τελευταίοι 5 αγώνες
    data = safe_get(url, params)
    if "error" in data:
        return jsonify(data), 500
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

@app.route('/api/boxscore')
def get_boxscore():
    game_id = request.args.get('game_id')
    if not game_id:
        return jsonify({"error": "game_id is required"}), 400
    url = f"{BASE_URL}/box_scores"
    params = {"game_id": game_id}
    data = safe_get(url, params)
    if "error" in data:
        return jsonify(data), 500
    # Απλοποιούμε την απάντηση
    players = []
    for team_key in ["home_team", "visitor_team"]:
        team = data.get("data", {}).get(team_key, {})
        for p in team.get("players", []):
            players.append({
                "player_id": p["id"],
                "name": f"{p['first_name']} {p['last_name']}",
                "team": team["full_name"],
                "pts": p.get("pts"),
                "reb": p.get("reb"),
                "ast": p.get("ast"),
                "stl": p.get("stl"),
                "blk": p.get("blk"),
                "min": p.get("min")
            })
    return jsonify(players)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
