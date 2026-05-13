from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import time

app = Flask(__name__)
CORS(app)

# NBA Stats API headers (απαραίτητα για να μας απαντήσει το stats.nba.com)
NBA_HEADERS = {
    "Host": "stats.nba.com",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.nba.com/",
}

# Συνάρτηση για κλήσεις στο NBA API με επανάληψη σε περίπτωση αποτυχίας
def nba_api_call(url, params=None, retries=2):
    for i in range(retries):
        try:
            resp = requests.get(url, params=params, headers=NBA_HEADERS, timeout=10)
            if resp.status_code == 200:
                return resp.json()
            else:
                time.sleep(1)  # περίμενε λίγο πριν ξαναπροσπαθήσεις
        except Exception as e:
            if i == retries - 1:
                raise e
            time.sleep(1)
    return None

@app.route('/')
def home():
    return jsonify({
        "status": "NBA API Server is running",
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
    # NBA player search μέσω του stats.nba.com
    url = "https://stats.nba.com/stats/playerindex"
    params = {
        "leagueID": "00",
        "season": "2025-26",
        "historical": "0",
        "playerNameSearch": search
    }
    data = nba_api_call(url, params)
    if not data:
        return jsonify({"error": "Could not fetch players"}), 500
    players = []
    for row in data.get("resultSets", [{}])[0].get("rowSet", []):
        players.append({
            "id": row[0],
            "first_name": row[1],
            "last_name": row[2],
            "team": row[7]
        })
    return jsonify(players[:10])  # επιστρέφουμε μέχρι 10 αποτελέσματα

@app.route('/api/games')
def get_games():
    date = request.args.get('date', '2026-05-13')
    # NBA schedule
    url = "https://stats.nba.com/stats/scoreboardv3"
    params = {
        "gameDate": date,
        "leagueID": "00"
    }
    data = nba_api_call(url, params)
    if not data:
        return jsonify({"error": "Could not fetch games"}), 500
    games = []
    for g in data.get("scoreboard", {}).get("games", []):
        games.append({
            "id": g["gameId"],
            "date": g["gameDateEst"],
            "home_team": g["homeTeam"]["teamName"],
            "away_team": g["awayTeam"]["teamName"],
            "home_score": g.get("homeTeam", {}).get("score"),
            "away_score": g.get("awayTeam", {}).get("score"),
            "status": g.get("gameStatusText", "Scheduled")
        })
    return jsonify(games)

@app.route('/api/player-stats')
def get_player_stats():
    player_id = request.args.get('player_id')
    if not player_id:
        return jsonify({"error": "player_id is required"}), 400
    # Χρησιμοποιούμε το LastNGames για τα τελευταία 5 παιχνίδια
    url = "https://stats.nba.com/stats/playergamelogs"
    params = {
        "playerId": player_id,
        "season": "2025-26",
        "measureType": "Base",
        "perMode": "PerGame",
        "lastNGames": "5"
    }
    data = nba_api_call(url, params)
    if not data:
        return jsonify({"error": "Could not fetch stats"}), 500
    stats = []
    rows = data.get("resultSets", [{}])[0].get("rowSet", [])
    headers = data.get("resultSets", [{}])[0].get("headers", [])
    for row in rows:
        entry = {}
        for i, h in enumerate(headers):
            if h in ["GAME_DATE", "PTS", "REB", "AST", "STL", "BLK", "MIN"]:
                entry[h.lower()] = row[i]
        stats.append(entry)
    return jsonify(stats)

@app.route('/api/boxscore')
def get_boxscore():
    game_id = request.args.get('game_id')
    if not game_id:
        return jsonify({"error": "game_id is required"}), 400
    url = "https://stats.nba.com/stats/boxscoretraditionalv3"
    params = {
        "gameId": game_id,
        "leagueID": "00"
    }
    data = nba_api_call(url, params)
    if not data:
        return jsonify({"error": "Could not fetch boxscore"}), 500
    players = []
    for team in data.get("boxScoreTraditional", {}).get("awayTeam", {}), data.get("boxScoreTraditional", {}).get("homeTeam", {}):
        for p in team.get("players", []):
            players.append({
                "player_id": p["personId"],
                "name": f"{p['firstName']} {p['familyName']}",
                "team": team["teamName"],
                "pts": p["statistics"].get("points"),
                "reb": p["statistics"].get("reboundsTotal"),
                "ast": p["statistics"].get("assists"),
                "stl": p["statistics"].get("steals"),
                "blk": p["statistics"].get("blocks"),
                "min": p["statistics"].get("minutes")
            })
    return jsonify(players)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
