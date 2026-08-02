from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

GAME_URL = "https://online-quiz-xe6u.onrender.com"

QUESTION = {
    "title": "Bringe die Planeten in die richtige Reihenfolge von der Sonne aus:",
    "correct_order": [
        "Merkur",
        "Venus",
        "Erde",
        "Mars"
    ]
}

@app.route("/")
def index():
    return render_template(
        "index.html",
        question=QUESTION["title"],
        items=QUESTION["correct_order"]
    )

@app.route("/host")
def host():
    return render_template("host.html", game_url=GAME_URL)

# ... weitere Routen ...

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

# Beispiel-Reihenfolgefrage
QUESTION = {
    "title": "Bringe die Planeten in die richtige Reihenfolge von der Sonne aus:",
    "correct_order": [
        "Merkur",
        "Venus",
        "Erde",
        "Mars"
    ]
}


@app.route("/")
def index():
    return render_template(
        "index.html",
        question=QUESTION["title"],
        items=QUESTION["correct_order"]
    )


@app.route("/host")
def host():
    return render_template("host.html")


@app.route("/check", methods=["POST"])
def check():
    data = request.get_json()

    if not data or "order" not in data:
        return jsonify({
            "success": False,
            "message": "Keine Daten erhalten."
        }), 400

    correct = data["order"] == QUESTION["correct_order"]

    return jsonify({
        "success": correct,
        "correct_order": QUESTION["correct_order"]
    })


@app.route("/question")
def question():
    return jsonify({
        "title": QUESTION["title"],
        "items": QUESTION["correct_order"]
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
