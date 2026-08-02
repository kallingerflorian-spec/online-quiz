from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Beispielfrage mit korrekter Reihenfolge
QUESTION_DATA = {
    "question": "Bringe diese Schritte in die richtige logische Reihenfolge:",
    "correct_order": ["1. Planen", "2. Programmieren", "3. Testen", "4. Veröffentlichen"]
}

@app.route('/')
def index():
    # Gemischte Reihenfolge für den Benutzer
    import random
    shuffled = QUESTION_DATA["correct_order"][:]
    random.shuffle(shuffled)
    return render_template('index.html', question=QUESTION_DATA["question"], items=shuffled)

@app.route('/submit', methods=['POST'])
def submit():
    user_answer = request.form.getlist('order[]')
    is_correct = (user_answer == QUESTION_DATA["correct_order"])
    result_text = "Richtig! Perfekte Reihung." if is_correct else "Leider falsch. Versuch es noch einmal."
    return render_template('result.html', result=result_text, correct=QUESTION_DATA["correct_order"])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
