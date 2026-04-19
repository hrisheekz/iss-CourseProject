let socket = null
let myid = null
let roomid = null
let mysymbol = null

const parameters = new URLSearchParams(window.location.search)
if(parameters.has("roomid"))
{
    roomid = parameters.get("roomid")
}

async function init(){
    const response = await fetch("/me")
    const data = await response.json()
    myid = data.uid
    socket = new WebSocket("ws://localhost:8000/ws/"+myid)
    socket.onopen = () => {
        socket.send(JSON.stringify({type:"get_game_state",room_id:roomid}))
    }
    socket.onmessage = (event) => {
        const msg = JSON.parse(event.data)
        handleMessage(msg)
    }
}

window.onload = () => init()

function handleMessage(msg){
    if(msg.type == "game_init"){
        mysymbol = msg.your_symbol
        document.getElementById("game-info").textContent = "You are "+ mysymbol + " | vs " + msg.opponent_name
        updateStatus(msg.turn)
        renderBoard(msg.board)
        
        //  Make the forfeit button visible when the game starts
        const forfeitBtn = document.getElementById("forfeit-btn")
        if (forfeitBtn) forfeitBtn.style.display = "inline-block" 
    }
    else if(msg.type == "board_update"){
        renderBoard(msg.board)
        updateStatus(msg.turn)
        if(msg.winner){
            showResult(msg.winner)
        }
    }
    else if(msg.type == "game_over"){
        if (msg.reason === "forfeit" && msg.winner === "you") {
            showResult("forfeit_win")
        } else if (msg.reason === "forfeit" && msg.winner === "opponent") {
            showResult("forfeit_loss")
        } else {
            showResult("disconnect")
        }
    }
}

function renderBoard(board){
    const cells = document.querySelectorAll(".cell")
    cells.forEach((cell,index) => {
        cell.textContent = board[index]
        cell.className = "cell " + (board[index] == "X" ? "x" : board[index] == "O" ? "o" : "")
        cell.onclick = () => sendMove(index)
    })
}

function sendMove(index){
    socket.send(JSON.stringify({type:"move",cell:index}))
}

function updateStatus(turn){
    const status = document.getElementById("status")
    if(turn == myid){
        status.textContent = "Your turn"
    }
    else if(turn == null){
        status.textContent = "Game Over"
    }
    else{
        status.textContent = "Opponent's turn"
    }
}

function showResult(winner){
    const result = document.getElementById("game-result")
    const message = document.getElementById("result-message")
    
    //  Hide the forfeit button because the match ended
    const forfeitBtn = document.getElementById("forfeit-btn")
    if (forfeitBtn) {
        forfeitBtn.style.display = "none"
    }

    if(winner == "disconnect"){
        message.textContent = "Opponent has disconnected. You win by default!"
    }
    else if (winner == "forfeit_win"){
        message.textContent = "You win!!! Opponent has forfeited the game."
    }
    else if (winner == "forfeit_loss"){
        message.textContent = "You forfeited the game. You lose :c"
    }
    else if(winner == "draw"){
        message.textContent = "It's a draw"
    }
    else if (winner == mysymbol){
        message.textContent = "You win!!!"
    }
    else{
        message.textContent = "You lose :c"
    }
    
    result.style.display = "block"
    document.getElementById("back-to-lobby").onclick = () => {
        window.location.href = "/lobby"
    }
}

document.getElementById("forfeit-btn").addEventListener("click", () => {
    if (confirm("Are you sure you want to forfeit?")) {
        socket.send(JSON.stringify({
            "type": "forfeit"
        }));
    }
});