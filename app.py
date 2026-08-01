import os
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='templates', static_folder='templates')
app.config['SECRET_KEY'] = 'quiz-ultra-secret-123!'
# Wichtig für das Internet: Erlaube Verbindungen von allen Geräten
socketio = SocketIO(app, cors_allowed_origins="*")

# Deine 5 Fragen
fragen = [
    {"q": "Welches Jahr haben wir aktuell?", "c": ["2024", "2025", "2026", "2027"], "a": 2},
    {"q": "Welcher Planet ist der Sonne am nächsten?", "c": ["Venus", "Merkur", "Erde", "Mars"], "a": 1},
    {"q": "Wie viele Bundesländer hat Österreich?", "c": ["7", "8", "9", "10"], "a": 2},
    {"q": "Aus welcher Pflanze wird Tequila hergestellt?", "c": ["Kaktus", "Agave", "Zuckerrohr", "Weizen"], "a": 1},
    {"q": "Welche Farbe hat die Kahoot-Schaltfläche unten rechts?", "c": ["Rot", "Blau", "Gelb", "Grün"], "a": 3}
]

spiel_status = {"phase": "lobby", "frage_index": 0, "antworten_eingegangen": 0}
spieler = {} 

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/host.html')
def host():
    return render_template('host.html')

@socketio.on('beamer_bereit')
def beamer_bereit():
    emit('spieler_liste', [s["name"] for s in spieler.values()])

@socketio.on('join')
def handle_join(name):
    from flask import request
    spieler[request.sid] = {"name": name, "punkte": 0}
    emit('spieler_liste', [s["name"] for s in spieler.values()], broadcast=True)

@socketio.on('naechste_frage')
def handle_next():
    global spiel_status
    if spiel_status["phase"] in ["lobby", "auswertung"]:
        if spiel_status["phase"] == "auswertung":
            spiel_status["frage_index"] += 1
            
        if spiel_status["frage_index"] < len(fragen):
            spiel_status["phase"] = "spiel"
            spiel_status["antworten_eingegangen"] = 0
            aktuelle = fragen[spiel_status["frage_index"]]
            emit('starte_frage', {"frage": aktuelle["q"], "optionen": aktuelle["c"]}, broadcast=True)
        else:
            spiel_status["phase"] = "ende"
            rangliste = sorted(spieler.values(), key=lambda x: x["punkte"], reverse=True)
            emit('spiel_ende', rangliste, broadcast=True)

@socketio.on('sende_antwort')
def handle_answer(index):
    from flask import request
    global spiel_status
    s = spieler.get(request.sid)
    if s and spiel_status["phase"] == "spiel":
        korrekt = fragen[spiel_status["frage_index"]]["a"]
        if index == korrekt:
            s["punkte"] += 100
        spiel_status["antworten_eingegangen"] += 1
        
        if spiel_status["antworten_eingegangen"] >= len(spieler):
            spiel_status["phase"] = "auswertung"
            rangliste = sorted(spieler.values(), key=lambda x: x["punkte"], reverse=True)
            emit('zeige_auswertung', {"korrekt": korrekt, "rangliste": rangliste}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    from flask import request
    if request.sid in spieler:
        del spieler[request.sid]
        emit('spieler_liste', [s["name"] for s in spieler.values()], broadcast=True)

if __name__ == '__main__':
    # Holt den Port, den Render uns im Internet zuweist
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
