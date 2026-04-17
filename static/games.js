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
    socket = new WebSocket("ws://localhost:8000/ws/" + myid)
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
    }
    else if(msg.type == "board_update"){
        renderBoard(msg.board)
        updateStatus(msg.turn)
        if(msg.winner){
            showResult(msg.winner)
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
    if(winner == "draw"){
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