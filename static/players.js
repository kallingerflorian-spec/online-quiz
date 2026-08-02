const socket = io();

let answered = false;

document
.getElementById("joinButton")
.onclick = () => {

    const name =
        document.getElementById("name").value.trim();

    if(name.length < 2){

        alert("Bitte Namen eingeben.");

        return;
    }

    socket.emit("join",{

        name:name

    });

    document.getElementById("joinCard").style.display="none";

    document.getElementById("quizCard").style.display="block";

};

socket.on("question", q=>{

    answered=false;

    document.getElementById("progress").innerText=q.question;

    document.getElementById("question").innerText=q.question;

    const imageDiv=document.getElementById("imageContainer");

    imageDiv.innerHTML="";

    if(q.image){

        imageDiv.innerHTML=
        `<img src="${q.image}" class="questionImage">`;

    }

    const answers=document.getElementById("answers");

    answers.innerHTML="";

    if(q.type==="multiple"){

        q.answers.forEach((answer,index)=>{

            const btn=document.createElement("button");

            btn.className="answer";

            btn.innerText=answer;

            btn.onclick=()=>{

                if(answered)return;

                answered=true;

                socket.emit("answer",{

                    answer:index

                });

                document
                .querySelectorAll(".answer")
                .forEach(b=>b.disabled=true);

            };

            answers.appendChild(btn);

        });

    }

});