let myid = null
let socket = null

async function init(){
    const response = await fetch("/me")
    const data = await response.json()

    if (data.error){
        window.location.href = "/";
        console.log("Not logged in.")
        return;
    }

    myid = data.uid
    document.querySelector("#welcome-message").textContent = "Welcome " + data.name + "!"
    const init_lobby = await fetch("/initial-lobby")
    const users = await init_lobby.json()
    renderGrid(users)
    socket = new WebSocket("ws://localhost:8000/ws/"+myid)
    socket.onopen = () => {
        console.log("Connection has been established.")
        socket.send(JSON.stringify({type:"request_lobby"}));
    }
    socket.onmessage = (event) => {
        try{
            const msg = JSON.parse(event.data)
            handleMessage(msg)
        }
        catch(err){
            console.error("Received invalid JSON:",err)
        }
    }
    socket.onclose = () => {
        console.log("Disconnected from server.")
    }
}

function handleMessage(data){
    if (data.type == "lobby_update")
    {
        renderGrid(data.users)
    }
    else if(data.type == "challenge_received")
    {
        showChallenge(data.challenger_uid,data.challenger_name)
    }
    else if(data.type == "challenge_declined")
    {
        alert("Your challenge has been declined!")
    }
    else if(data.type == "game_start")
    {
        window.location.href = "/game"
    }
}
function renderGrid(users){
    const grid = document.getElementById("user-grid")
    if (!grid)
        return
    grid.innerHTML = ""

    users.forEach(user => {
        const card = document.createElement("div")
        card.className = "user-card"
        const infodiv = document.createElement("div")
        infodiv.className = "user-info"
        infodiv.innerHTML = `<strong>${user.name}</strong><p>Elo: ${user.elo_rating}</p>`
        card.appendChild(infodiv)

        if (myid && user_uid != myid){
            const btn = document.createElement("button")
            btn.textContent = "Challenge"
            btn.className = "challenge-btn"
            btn.onclick = () => sendChallenge(user.uid)
            card.appendChild(btn)
        }
        else if(user_uid == myid){
            card.style.border = "1px solid #10b981"; // Green border for yourself
            card.style.opacity = "0.8";
        }
        grid.appendChild(card)
    })
}

function sendChallenge(targetUid){
    socket.send(JSON.stringify({type:"challenge",target_uid:targetUid}))
}

function showChallenge(challengerUid,challengerName){
    document.getElementById("challenge-message").textContent = challengerName + " has challenged you!"
    document.getElementById("challenge").style.display = "block"
    
    document.getElementById("accept-btn").onclick = () => {
        socket.send(JSON.stringify({type:"accept",challenger_uid:challengerUid}))
        document.getElementById("challenge").style.display = "none"
    }

    document.getElementById("decline-btn").onclick = () => {
        socket.send(JSON.stringify({type:"decline",challenger_uid:challengerUid}))
        document.getElementById("challenge").style.display = "none"
    }
}

window.onload = () => {
    init()
}