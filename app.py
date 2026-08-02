from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import random
import string
import time
from threading import Thread


app = Flask(__name__)
app.config["SECRET_KEY"] = "quiz-secret"

socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)
# ---------------------------------
# Einstellungen
# ---------------------------------

GAME_URL = "https://online-quiz-xe6u.onrender.com"

QUESTION = {
    "title": "Ordne die Torfarben den Untersuchungen/Aktivitäten richtig zu: MRT (klaustro), MRT, Klimaanlage kühlen und Mammographie?:",
    "correct_order": [
        "🟦 Blau",
        "🟥 Rot",
        "⬜ Weiß",
        "🟨 Gelb"
    ]
}

# ---------------------------------
# Speicher
# ---------------------------------

players = {}

scores = {}
host_sid = None
answers = {}

game = {
    "pin": "",
    "started": False,
    "timer": 30,
    "question": 0
}

# ---------------------------------
# Hilfsfunktionen
# ---------------------------------
timer_running = False





def countdown():

    global timer_running

    timer_running = True

    while game["timer"] > 0:

        socketio.emit(
            "timer",
            {"time": game["timer"]}
        )

        socketio.sleep(1)

        game["timer"] -= 1

    timer_running = False

    socketio.emit(
        "time_up"
    )

    show_results()


@socketio.on("restart_game")
def restart_game():

    global game

    game["started"] = False
    game["timer"] = 20
    game["question"] = 0
    game["pin"] = generate_pin()   # Optional: neuer Spielcode

    players.clear()
    scores.clear()
    answers.clear()

    socketio.emit("game_restarted")


def generate_pin():
    return "".join(random.choices(string.digits, k=6))

game["pin"] = generate_pin()

# ---------------------------------
# Seiten
# ---------------------------------

@app.route("/")
def index():
    return render_template(
        "index.html",
        game_url=GAME_URL
    )


@app.route("/host")
def host():
    return render_template(
        "host.html",
        game_url=GAME_URL,
        pin=game["pin"]
    )

# ---------------------------------
# Socket Events
# ---------------------------------


@socketio.on("join")
def join(data):

    name = data.get("name", "").strip()

    if not name:
        emit("join_error", {
            "message": "Bitte Namen eingeben."
        })
        return

    players[request.sid] = name

    scores.setdefault(name, 0)
    answers[name] = False

    emit("joined")

    socketio.emit(
        "player_list",
        list(players.values())
    )




@socketio.on("host_request_players")
def host_request_players():

    emit(
        "player_list",
        list(players.values())
    )


@socketio.on("host_connected")
def host_connected():

    global host_sid

    host_sid = request.sid


@socketio.on("start_game")
def start_game():

    if game["started"]:
        return

    game["started"] = True
    game["timer"] = 30

    for name in answers:
        answers[name] = False

    socketio.emit(
        "start_question",
        QUESTION
    )

    socketio.start_background_task(countdown)



@socketio.on("submit_order")
def submit_order(data):

    player = players.get(request.sid)

    if player is None:
        return

    if answers[player]:
        return

    answers[player] = True

    correct = data["order"] == QUESTION["correct_order"]
    emit(
        "answer_result",
        {
            "correct": correct
        }
    )
    if correct:
        scores[player] += game["timer"] * 100

        if host_sid:
            socketio.emit(
                "answer_update",
                {
                    "player": player,
                    "correct": correct
                },
                to=host_sid
            )




def show_results():

    ranking = []

    for name, score in scores.items():

        ranking.append({
            "name": name,
            "score": score
        })

    ranking.sort(
        key=lambda x: x["score"],
        reverse=True
    )
    if host_sid:
        socketio.emit(
            "leaderboard",
            ranking,
            to=host_sid
        )




@socketio.on("disconnect")
def disconnect():

    if request.sid not in players:
        return

    name = players.pop(request.sid)

    answers.pop(name, None)
    scores.pop(name, None)

    socketio.emit(
        "player_list",
        list(players.values()),
    )



if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=5000,
        debug=True
    )

