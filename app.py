from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import os

app = Flask(__name__)
CORS(app)

# Ρυθμίσεις για το NBA API Free Data (RapidAPI)
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "9bd9db0ebfmsh2dcf7ca35b912e0p13458cjsn314474139704")
RAPIDAPI_HOST = "nba-api-free-data.p.rapidapi.com"
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

# -----------------------------------------------
# Τα δικά μας endpoints που θα καλεί το Lovable
# -----------------------------------------------

@app.route('/api/players')
def search_players():
    search = request.args.get('search', 'LeBron')

    # Το API έχει endpoint /nba-player-list?teamid=...
    # Για αναζήτηση με όνομα, παίρνουμε όλους τους παίκτες και φιλτράρουμε
    # (Το API μπορεί να υποστηρίζει και αναζήτηση με όνομα, δοκιμάζουμε)
    
    # Πρώτη προσπάθεια: μήπως υπάρχει endpoint αναζήτησης
    data = safe_get("/nba-player-list", {"name": search})
    if "error" in data:
        # Δεύτερη προσπάθεια: αν δεν δουλεύει με name, παίρνουμε όλους
        data = safe_get("/nba-player-list", {})
    
    if "error" in data:
        return jsonify(data), 500

    # Το API επιστρέφει τα δεδομένα μέσα σε διάφορα κλειδιά
    players_list = data.get("response") or data.get("data") or data.get("results") or data or []
    
    # Αν είναι dict αντί για list, το μετατρέπουμε
    if isinstance(players_list, dict):
        players_list = list(players_list.values()) if not isinstance(players_list, list) else [players_list]
    if not isinstance(players_list, list):
        players_list = []

    players = []
    for p in players_list:
        if not isinstance(p, dict):
            continue
        first = p.get("firstname") or p.get("firstName") or p.get("first_name") or ""
        last = p.get("lastname") or p.get("lastName") or p.get("last_name") or ""
        full = f"{first} {last}".strip()
        
        # Φιλτράρισμα αν δώσαμε search
        if search and search.lower() not in full.lower():
            continue
            
        players.append({
            "id": p.get("id") or p.get("playerId") or p.get("player_id"),
            "first_name": first,
            "last_name": last,
            "team": (p.get("team") or {}).get("name") or p.get("teamName") or p.get("team_name") or "N/A"
        })
    
    return jsonify(players[:10])

@app.route('/api/games')
def get_games():
    date = request.args.get('date', '2026-05-14')
    # Αφαίρεσε τις παύλες για το API (θέλει YYYYMMDD)
    date_formatted = date.replace('-', '')
    
    data = safe_get("/nba-scoreboard-by-date", {"date": date_formatted})
    if "error" in data:
        return jsonify(data), 500

    games_list = data.get("response") or data.get("data") or data.get("results") or data or []
    if isinstance(games_list, dict):
        games_list = [games_list]
    if not isinstance(games_list, list):
        games_list = []

    games = []
    for g in games_list:
        if not isinstance(g, dict):
            continue
        games.append({
            "id": g.get("id") or g.get("gameId") or g.get("game_id"),
            "date": g.get("date") or g.get("gameDate") or date,
            "home_team": (g.get("homeTeam") or g.get("home") or {}).get("name") or g.get("home_team") or "",
            "away_team": (g.get("awayTeam") or g.get("away") or {}).get("name") or g.get("away_team") or "",
            "home_score": g.get("homeScore") or g.get("home_score") or (g.get("scores") or {}).get("home"),
            "away_score": g.get("awayScore") or g.get("away_score") or (g.get("scores") or {}).get("away"),
            "status": g.get("status") or g.get("gameStatus") or "Scheduled"
        })
    return jsonify(games)

@app.route('/api/player-stats')
def get_player_stats():
    player_id = request.args.get('player_id')
    if not player_id:
        return jsonify({"error": "player_id is required"}), 400

    data = safe_get("/nba-player-stats", {"playerid": player_id})
    if "error" in data:
        return jsonify(data), 500

    stats_list = data.get("response") or data.get("data") or data.get("results") or data or []
    if isinstance(stats_list, dict):
        stats_list = [stats_list]
    if not isinstance(stats_list, list):
        stats_list = []

    stats = []
    for s in stats_list:
        if not isinstance(s, dict):
            continue
        stats.append({
            "game_id": s.get("gameId") or s.get("game_id") or (s.get("game") or {}).get("id"),
            "date": s.get("date") or s.get("gameDate") or (s.get("game") or {}).get("date"),
            "pts": s.get("points") or s.get("pts") or s.get("PTS"),
            "reb": s.get("rebounds") or s.get("reb") or s.get("REB"),
            "ast": s.get("assists") or s.get("ast") or s.get("AST"),
            "stl": s.get("steals") or s.get("stl") or s.get("STL"),
            "blk": s.get("blocks") or s.get("blk") or s.get("BLK"),
            "min": s.get("minutes") or s.get("min") or s.get("MIN")
        })
    return jsonify(stats[:5])

@app.route('/api/boxscore')
def get_boxscore():
    game_id = request.args.get('game_id')
    if not game_id:
        return jsonify({"error": "game_id is required"}), 400

    # Χρησιμοποιούμε το nba-player-stats με game parameter
    data = safe_get("/nba-player-stats", {"gameid": game_id})
    if "error" in data:
        return jsonify(data), 500

    players_list = data.get("response") or data.get("data") or data.get("results") or data or []
    if isinstance(players_list, dict):
        players_list = [players_list]
    if not isinstance(players_list, list):
        players_list = []

    players = []
    for p in players_list:
        if not isinstance(p, dict):
            continue
        players.append({
            "player_id": p.get("playerId") or p.get("id") or p.get("player_id"),
            "name": f"{p.get('firstName', '')} {p.get('lastName', '')}".strip() or p.get("name", ""),
            "team": p.get("teamName") or p.get("team_name") or (p.get("team") or {}).get("name", ""),
            "pts": p.get("points") or p.get("pts") or p.get("PTS"),
            "reb": p.get("rebounds") or p.get("reb") or p.get("REB"),
            "ast": p.get("assists") or p.get("ast") or p.get("AST"),
            "stl": p.get("steals") or p.get("stl") or p.get("STL"),
            "blk": p.get("blocks") or p.get("blk") or p.get("BLK"),
            "min": p.get("minutes") or p.get("min") or p.get("MIN")
        })
    return jsonify(players)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
