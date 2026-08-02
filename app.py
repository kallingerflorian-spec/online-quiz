from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import json

app = Flask(__name__)
app.config["SECRET_KEY"] = "quiz"

socketio = SocketIO(
    app,
    cors_allowed_origins="*"
)

players = []

current_question = 0

with open("questions.json","r",encoding="utf8") as f:
    QUESTIONS = json.load(f)


@app.route("/")
def player():
    return render_template("player.html")


@app.route("/host")
def host():
    return render_template("host.html")


@socketio.on("join")
def join(data):

    name = data["name"]

    players.append({
        "name":name,
        "points":0
    })

    emit(
        "players",
        players,
        broadcast=True
    )


@socketio.on("start")

def start():

    emit(
        "question",
        QUESTIONS[current_question],
        broadcast=True
    )


if __name__ == "__main__":
    socketio.run(
        app,
        debug=True
    )
