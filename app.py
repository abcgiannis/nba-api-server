from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# Ρυθμίσεις για το NBA API Free Data (RapidAPI)
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "9bd9db0ebfmsh2dcf7ca35b912e0p13458cjsn314474139704")
RAPIDAPI_HOST = os.environ.get("RAPIDAPI_HOST", "nba-api-free-data.p.rapidapi.com")
BASE_URL = f"https://{RAPIDAPI_HOST}"
HEADERS = {
    "x-rapidapi-host": RAPIDAPI_HOST,
    "x-rapidapi-key": RAPIDAPI_KEY
}

def safe_get(endpoint, params=None):
    try:
        url = f"{BASE_URL}{endpoint}"
        resp = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": f"Status {resp.status_code}", "details": resp.text}
    except Exception as e:
        return {"error": str(e)}

@app.route('/')
def home():
    return jsonify({
        "status": "NBA API Server is running",
        "data_source": RAPIDAPI_HOST,
        "endpoints": [
            "/api/players?search=...",
            "/api/games?date=YYYY-MM-DD",
            "/api/player-stats?player_id=...",
            "/api/boxscore?game_id=..."
        ]
    })

# ------------------------------------------------------------
# Οι δικές μας "έξυπνες" διευθύνσεις που θα καλεί το Lovable
# ------------------------------------------------------------

@app.route('/api/players')
def search_players():
    search = request.args.get('search', 'LeBron')
    # Endpoint: Player/ All List (συνήθως /players)
    data = safe_get("/players", {"search": search})
    if "error" in data:
        return jsonify(data), 500

    # Το API επιστρέφει τα δεδομένα μέσα σε ένα κλειδί (π.χ. "response" ή "data")
    players_list = data.get("response") or data.get("data") or data.get("results") or []
    players = []
    for p in players_list:
        players.append({
            "id": p.get("id"),
            "first_name": p.get("firstname") or p.get("first_name") or "",
            "last_name": p.get("lastname") or p.get("last_name") or "",
            "team": (p.get("team") or {}).get("name") or (p.get("team") or {}).get("full_name") or "N/A"
        })
    return jsonify(players[:10])

@app.route('/api/games')
def get_games():
    date = request.args.get('date', '2026-05-13')
    # Endpoint: Scoreboard/ Get by Date (πιθανόν /scoreboard?date=...)
    data = safe_get("/scoreboard", {"date": date})
    if "error" in data:
        # Δοκιμάζουμε και το /games αν το /scoreboard αποτύχει
        data = safe_get("/games", {"date": date})
    if "error" in data:
        return jsonify(data), 500

    games_list = data.get("response") or data.get("data") or data.get("results") or []
    games = []
    for g in games_list:
        games.append({
            "id": g.get("id") or g.get("gameId"),
            "date": g.get("date") or g.get("gameDate"),
            "home_team": (g.get("homeTeam") or g.get("home") or {}).get("name") or (g.get("homeTeam") or {}).get("full_name") or "",
            "away_team": (g.get("awayTeam") or g.get("visitor") or {}).get("name") or (g.get("awayTeam") or {}).get("full_name") or "",
            "home_score": g.get("homeScore") or (g.get("scores", {}) or {}).get("home", {}).get("total"),
            "away_score": g.get("awayScore") or (g.get("scores", {}) or {}).get("away", {}).get("total"),
            "status": g.get("status") or g.get("gameStatus") or "Scheduled"
        })
    return jsonify(games)

@app.route('/api/player-stats')
def get_player_stats():
    player_id = request.args.get('player_id')
    if not player_id:
        return jsonify({"error": "player_id is required"}), 400

    # Endpoint: Player/ Gamelog (συχνά /players/gamelog?player=...)
    data = safe_get("/players/gamelog", {"player": player_id})
    if "error" in data:
        # εναλλακτικά δοκιμάζουμε /players/statistics
        data = safe_get("/players/statistics", {"player": player_id, "per_page": 5})

    if "error" in data:
        return jsonify(data), 500

    stats_list = data.get("response") or data.get("data") or data.get("results") or []
    stats = []
    for s in stats_list:
        stats.append({
            "game_id": s.get("game", {}).get("id") if isinstance(s.get("game"), dict) else s.get("gameId"),
            "date": s.get("date") or (s.get("game", {}) or {}).get("date"),
            "pts": s.get("points") or s.get("pts"),
            "reb": s.get("rebounds") or s.get("reb"),
            "ast": s.get("assists") or s.get("ast"),
            "stl": s.get("steals") or s.get("stl"),
            "blk": s.get("blocks") or s.get("blk"),
            "min": s.get("minutes") or s.get("min")
        })
    # επιστρέφουμε μέχρι 5 τελευταία
    return jsonify(stats[:5])

@app.route('/api/boxscore')
def get_boxscore():
    game_id = request.args.get('game_id')
    if not game_id:
        return jsonify({"error": "game_id is required"}), 400

    # Μπορούμε να τραβήξουμε τα stats όλων των παικτών για αυτόν τον αγώνα
    # Συνήθως υπάρχει endpoint τύπου /players/statistics?game=...
    data = safe_get("/players/statistics", {"game": game_id})
    if "error" in data:
        # Εναλλακτικά, δοκιμάζουμε /games/boxscore
        data = safe_get(f"/games/{game_id}/boxscore")

    if "error" in data:
        return jsonify(data), 500

    players_list = data.get("response") or data.get("data") or data.get("results") or []
    players = []
    for p in players_list:
        players.append({
            "player_id": p.get("player", {}).get("id") if isinstance(p.get("player"), dict) else p.get("playerId"),
            "name": f"{p.get('player', {}).get('firstname', '')} {p.get('player', {}).get('lastname', '')}" if isinstance(p.get("player"), dict) else p.get("playerName", ""),
            "team": (p.get("team", {}) or {}).get("name") or p.get("teamName", ""),
            "pts": p.get("points") or p.get("pts"),
            "reb": p.get("rebounds") or p.get("reb"),
            "ast": p.get("assists") or p.get("ast"),
            "stl": p.get("steals") or p.get("stl"),
            "blk": p.get("blocks") or p.get("blk"),
            "min": p.get("minutes") or p.get("min")
        })
    return jsonify(players)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
