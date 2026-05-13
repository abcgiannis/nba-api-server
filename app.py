from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)

NBA_STATS_BASE = "https://stats.nba.com/stats"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Referer": "https://www.nba.com/"
}

@app.route('/')
def home():
    return jsonify({"status": "NBA API Server is running", "endpoints": ["/api/players", "/api/games", "/api/boxscore", "/api/player-stats"]})

@app.route('/api/players')
def search_players():
    search = request.args.get('search', 'LeBron')
    # NBA player search
    url = "https://www.balldontlie.io/api/v1/players"
    params = {"search": search, "per_page": 10}
    resp = requests.get(url, params=params)
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

@app.route('/api/games')
def get_games():
    date = request.args.get('date', '')
    url = "https://www.balldontlie.io/api/v1/games"
    params = {"dates[]": date, "per_page": 50}
    resp = requests.get(url, params=params)
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

@app.route('/api/boxscore')
def get_boxscore():
    game_id = request.args.get('game_id', '')
    url = f"https://www.balldontlie.io/api/v1/box_scores"
    params = {"game_id": game_id}
    resp = requests.get(url, params=params)
    data = resp.json()
    return jsonify(data)

@app.route('/api/player-stats')
def get_player_stats():
    player_id = request.args.get('player_id', '')
    url = "https://www.balldontlie.io/api/v1/stats"
    params = {"player_ids[]": player_id, "per_page": 10}
    resp = requests.get(url, params=params)
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
