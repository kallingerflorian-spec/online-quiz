import os
import time
from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='templates', static_folder='templates')
app.config['SECRET_KEY'] = 'millionenshow-secret-99!'
socketio = SocketIO(
    app,
    cors_allowed_origins="*",
    async_mode="threading"
)
# Deine 5 Millionen-Show-Fragen (Schwierigkeit steigt!)
# a = Index der richtigen Antwort (0=Rot, 1=Blau, 2=Gelb, 3=Grün)
fragen = [
    {"q": "Für 100 €: Welches Tier bellt üblicherweise?", "c": ["Katze", "Maus", "Hund", "Vogel"], "a": 2},
    {"q": "Für 500 €: Was ist das chemische Symbol für Wasser?", "c": ["CO2", "H2O", "NaCl", "O2"], "a": 1},
    {"q": "Für 2.000 €: Welcher Planet wird auch der 'Rote Planet' genannt?", "c": ["Mars", "Venus", "Jupiter", "Saturn"], "a": 0},
    {"q": "Für 10.000 €: Wie viele Tasten hat ein Standard-Klavier?", "c": ["66", "78", "88", "92"], "a": 2},
    {"q": "Die 1.000.000 € Frage: Wer entwickelte die Relativitätstheorie?", "c": ["Isaac Newton", "Albert Einstein", "Nikola Tesla", "Marie Curie"], "a": 1}
]

spiel_status = {
    "phase": "lobby", 
    "frage_index": 0, 
    "antworten_eingegangen": 0,
    "frage_startzeit": 0  # Für die Zeiterfassung
}
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
            spiel_status["frage_startzeit"] = time.time()  # Startzeit der Frage merken!
            
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
        antwort_zeit = time.time()
        vergangene_zeit = antwort_zeit - spiel_status["frage_startzeit"]
        
        korrekt = fragen[spiel_status["frage_index"]]["a"]
        if index == korrekt:
            # Kahoot-Formel: Wer schneller drückt, kriegt mehr Punkte (Max 1000, Min 500)
            # Zeitlimit im Frontend ist 20 Sekunden
            zeit_faktor = max(0, (20 - vergangene_zeit) / 20)
            punkte_fuer_runde = int(500 + (500 * zeit_faktor))
            s["punkte"] += punkte_fuer_runde
            
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
    port = int(os.environ.get('PORT', 5000))
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
