import os
import time
import qrcode
from flask import Flask, render_template_string, request, jsonify
from kahoot import client

app = Flask(__name__)

# Globale Variablen für den Kahoot-Bot
bot = None
current_question = None

# HTML-Oberfläche für das Smartphone (wird über den QR-Code aufgerufen)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Kahoot Reihenfolge Steuerung</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: Arial, sans-serif; text-align: center; background: #f0f0f0; padding: 20px; }
        button { width: 80%; padding: 15px; margin: 10px; font-size: 18px; border: none; border-radius: 8px; color: white; font-weight: bold; cursor: pointer; }
        .rot { background: #e21b3c; }
        .blau { background: #1368ce; }
        .gelb { background: #d89e00; }
        .gruen { background: #26890c; }
        .send-btn { background: #333; margin-top: 30px; width: 90%; }
        #sequence { font-size: 24px; margin: 20px; font-weight: bold; min-height: 30px; }
    </style>
</head>
<body>
    <h2>Kahoot Live-Eingabe</h2>
    <p>Tippe die Farben in der richtigen Reihenfolge an:</p>
    <div id="sequence">-</div>
    
    <button class="rot" onclick="add(0, '🔴 Rot')">Rot</button>
    <button class="blau" onclick="add(1, '🔵 Blau')">Blau</button>
    <button class="gelb" onclick="add(2, '🟡 Gelb')">Gelb</button>
    <button class="gruen" onclick="add(3, '🟢 Grün')">Grün</button>
    
    <button class="send-btn" onclick="sendOrder()">🚀 REIHENFOLGE ABSENDEN</button>
    <button style="background:#888;" onclick="resetOrder()">❌ Reset</button>

    <script>
        let currentOrder = [];
        let labels = [];
        
        function add(id, label) {
            if(currentOrder.length < 4 && !currentOrder.includes(id)) {
                currentOrder.push(id);
                labels.push(label);
                document.getElementById('sequence').innerText = labels.join(' ➔ ');
            }
        }
        
        function resetOrder() {
            currentOrder = [];
            labels = [];
            document.getElementById('sequence').innerText = '-';
        }
        
        function sendOrder() {
            if(currentOrder.length !== 4) {
                alert('Bitte alle 4 Farben auswählen!');
                return;
            }
            fetch('/submit-order', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({order: currentOrder})
            })
            .then(res => res.json())
            .then(data => alert(data.status))
            .catch(err => alert('Fehler: ' + err));
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# Route, die vom Smartphone aufgerufen wird, um die Reihenfolge zu übermitteln
@app.route('/submit-order', Brass='POST', methods=['POST'])
def submit_order():
    global current_question
    data = request.get_json()
    chosen_order = data.get('order') # Liste wie [1, 3, 0, 2]
    
    if current_question:
        try:
            current_question.answer(chosen_order)
            return jsonify({"status": f"Reihenfolge {chosen_order} gesendet!"})
        except Exception as e:
            return jsonify({"status": f"Fehler beim Senden: {str(e)}"}), 500
    else:
        return jsonify({"status": "Keine aktive Frage im Spiel gefunden oder Bot nicht bereit."}), 400

# Route zum Starten des Bots (kann von Render getriggert werden)
@app.route('/start-bot/<pin>/<name>')
def start_bot(pin, name):
    global bot
    bot = client()
    
    @bot.on("question_start")
    def on_question_started(question):
        global current_question
        current_question = question
        print(f"Neue Frage empfangen. Typ: {question.type}")

    bot.join(pin, name)
    return jsonify({"status": f"Bot {name} versucht PIN {pin} beizutreten."})

if __name__ == '__main__':
    # Generiere den QR-Code für deine Render-URL
    # Ersetzen Sie dies später durch Ihre echte Render-Webservice-URL (z.B. https://onrender.com)
    RENDER_URL = os.environ.get("RENDER_EXTERNAL_URL", "http://localhost:5000")
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(RENDER_URL)
    qr.make(fit=True)
    
    # Zeigt den QR-Code direkt in den Render-Log-Dateien an (ASCII-Art)
    print("\n--- SCANNEN SIE DIESEN QR-CODE MIT DEM SMARTPHONE ---")
    qr.print_ascii()
    print(f"Verbindungs-URL: {RENDER_URL}\n----------------------------------------------------\n")
    
    # Render weist dynamisch einen Port zu, standardmäßig 10000 oder über os.environ
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
