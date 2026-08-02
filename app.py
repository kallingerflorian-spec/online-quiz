import os
import time
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'quiz-ultra-secret-123!'

# Native websocket handling via simple-websocket without strict sync_modes
socketio = SocketIO(app, cors_allowed_origins="*")

fragen = [
    {
        "typ": "puzzle",
        "zeit": 30,
        "q": "Ordne die Untersuchungen / Aufgaben den passenden Toren/Türen zu!",
        "pairs": [
            {"item": "DXA", "color": "Rot"},
            {"item": "Mammographie", "color": "Weiß"},
            {"item": "Klimaanlage kühlen", "color": "Blau"},
            {"item": "MR-Schulter mit Platzangst", "color": "Gelb"}
        ]
    },
    {
        "typ": "mc",
        "zeit": 20,
        "q": "Du bist in der DXA und du untersuchst einen 70-jährigen Mann. Alle T-Werte der LWS liegen über +2,5. Was ist dein nächster Schritt?",
        "c": [
            "Kurz weinen und den *-Arzt kontaktieren",
            "Zum Schalter schicken und neuen Termin ausmachen",
            "Ich überprüfe ein LWS-Röntgen (Ausschluss falsch hoher Werte durch Sinterungen/Arthrose)",
            "Ich mache einen distalen Radius dazu"
        ],
        "a": 2
    },
    {
        "typ": "mc",
        "zeit": 20,
        "q": "Du bist im Röntgen eingeteilt. Beim Anfertigen einer LWS siehst du plötzlich dieses Bild. Wie reagierst du?",
        "c": [
            "Du kontaktierst den *-Arzt",
            "Du fragst den Patienten, ob er gestürzt ist?",
            "Du fragst den Patienten, ob bestimmte Bewegungen angenehm sind",
            "Du rufst im MR an, ob ein Ladegerät fehlt"
        ],
        "a": 3,
        "bild_pfad": "/static/lws_fremdkoerper.jpg"
    }
]

spiel_status = {"phase": "lobby", "frage_index": 0, "frage_startzeit": 0}
spieler = {}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/host')
def host():
    return render_template('host.html')

@socketio.on('beamer_bereit')
def beamer_bereit():
    emit('spieler_liste', [s["name"] for s in spieler.values()])

@socketio.on('join')
def handle_join(name):
    spieler[request.sid] = {"name": name, "punkte": 0, "hat_geantwortet": False}
    emit('spieler_liste', [s["name"] for s in spieler.values()], broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    if request.sid in spieler:
        del spieler[request.sid]
        emit('spieler_liste', [s["name"] for s in spieler.values()], broadcast=True)

@socketio.on('naechste_frage')
def handle_next():
    global spiel_status
    if spiel_status["phase"] in ["lobby", "auswertung"]:
        if spiel_status["phase"] == "auswertung":
            spiel_status["frage_index"] += 1
            
        if spiel_status["frage_index"] < len(fragen):
            spiel_status["phase"] = "spiel"
            spiel_status["frage_startzeit"] = time.time()
            
            for s in spieler.values():
                s["hat_geantwortet"] = False
                
            aktuelle = fragen[spiel_status["frage_index"]]
            
            sende_daten = {
                "typ": aktuelle["typ"],
                "frage": aktuelle["q"],
                "nummer": spiel_status["frage_index"] + 1,
                "zeit": aktuelle["zeit"],
                "bild_pfad": aktuelle.get("bild_pfad", None)
            }
            if aktuelle["typ"] == "mc":
                sende_daten["antworten"] = aktuelle["c"]
            else:
                sende_daten["items"] = [p["item"] for p in aktuelle["pairs"]]
                sende_daten["farben"] = [p["color"] for p in aktuelle["pairs"]]
                
            emit('zeige_frage', sende_daten, broadcast=True)
            emit('spiel_start', {"typ": aktuelle["typ"], "daten": sende_daten}, broadcast=True)
        else:
            spiel_status["phase"] = "ende"
            rangliste = sorted(spieler.values(), key=lambda x: x["punkte"], reverse=True)
            emit('spiel_ende', rangliste, broadcast=True)

@socketio.on('zeit_abgelaufen')
def handle_timeout():
    global spiel_status
    if spiel_status["phase"] == "spiel":
        beende_runde()

@socketio.on('antwort_abgeben')
def handle_antwort(daten):
    global spiel_status
    sid = request.sid
    if spiel_status["phase"] != "spiel" or sid not in spieler or spieler[sid]["hat_geantwortet"]:
        return
    
    spieler[sid]["hat_geantwortet"] = True
    aktuelle = fragen[spiel_status["frage_index"]]
    
    vergangene_zeit = time.time() - spiel_status["frage_startzeit"]
    zeit_faktor = max(0.5, 1.0 - (vergangene_zeit / aktuelle["zeit"]) * 0.5)

    if aktuelle["typ"] == "mc":
        if int(daten["antwort_index"]) == aktuelle["a"]:
            spieler[sid]["punkte"] += int(100 * zeit_faktor)
    elif aktuelle["typ"] == "puzzle":
        user_loesung = daten["loesung"]
        richtig = True
        for idx, pair in enumerate(aktuelle["pairs"]):
            if user_loesung[idx] != pair["color"]:
                richtig = False
        if richtig:
            spieler[sid]["punkte"] += int(150 * zeit_faktor)

    if all(s["hat_geantwortet"] for s in spieler.values()):
        beende_runde()

def beende_runde():
    global spiel_status
    spiel_status["phase"] = "auswertung"
    aktuelle = fragen[spiel_status["frage_index"]]
    aktuelle_rangliste = sorted(spieler.values(), key=lambda x: x["punkte"], reverse=True)
    
    loesung_text = ""
    if aktuelle["typ"] == "mc":
        loesung_text = aktuelle["c"][aktuelle["a"]]
    else:
        loesung_text = ", ".join([f"{p['item']} → {p['color']}" for p in aktuelle["pairs"]])

    emit('zeige_auswertung', {
        "loesung": loesung_text,
        "rangliste": aktuelle_rangliste
    }, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
