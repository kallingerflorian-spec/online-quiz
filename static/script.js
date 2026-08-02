new Sortable(document.getElementById("list"), {
    animation: 200
});

async function checkOrder(){

    const cards=document.querySelectorAll("#list li");

    let order=[];

    cards.forEach(card=>{
        order.push(card.innerText);
    });

    const response=await fetch("/check",{

        method:"POST",

        headers:{
            "Content-Type":"application/json"
        },

        body:JSON.stringify({
            order:order
        })

    });

    const data=await response.json();

    const result=document.getElementById("result");

    if(data.success){

        result.innerHTML="✅ Richtig!";

        result.style.color="green";

    }else{

        result.innerHTML="❌ Leider falsch.";

        result.style.color="red";

    }

}