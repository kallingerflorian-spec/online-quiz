const socket = io();

const quizURL = window.location.origin;

new QRCode(document.getElementById("qrcode"), {
    text: quizURL,
    width: 260,
    height: 260,
    colorDark: "#000000",
    colorLight: "#ffffff",
    correctLevel: QRCode.CorrectLevel.H
});

socket.on("players", players => {

    document.getElementById("count").innerText = players.length;

    if(players.length === 0){

        document.getElementById("players").innerHTML =
            "Noch keine Spieler";

        return;
    }

    document.getElementById("players").innerHTML =
        players.map(p=>`<div class="player">${p.name}</div>`).join("");

});

document
.getElementById("startButton")
.onclick = ()=>{

    socket.emit("start");

};