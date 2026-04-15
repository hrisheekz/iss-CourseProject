from fastapi import FastAPI
from fastapi import WebSocket,WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse,RedirectResponse
from pydantic import BaseModel
from pymongo import MongoClient
from starlette.middleware.sessions import SessionMiddleware
from fastapi import Request
import json
import uuid
import sqlite3
from utils.facial_recognition_module import find_closest_match

client = MongoClient("mongodb://localhost:27017/")
db = client["multiplayer_arena"]
user_collection = db["users"]

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(SessionMiddleware, secret_key="supersecretkey123")

connected_users = {}
rooms = {}

@app.get("/")
def login_page():
    return FileResponse("identity.html")

class LoginRequest(BaseModel):
    image:str

@app.post("/login")
def login(request: Request,body: LoginRequest):
    db_images_dict = {}
    for doc in user_collection.find({},{"uid":1,"profile_image":1}):
        db_images_dict[doc["uid"]] = doc["profile_image"]
    matched_id = find_closest_match(body.image,db_images_dict)
    
    #Debug statements

    # print("Testing with", len(db_images_dict), "images")
    # print("Done loading — face recognition module is accessible")

    if matched_id is None:
        return {"success":False,"message":"No matching user has been found."}
    
    q1 = "SELECT * from users where uid = ?"
    con = sqlite3.connect("data.db")
    cursor = con.cursor()
    cursor.execute(q1,(matched_id,))
    user = cursor.fetchone()

    if user is None:
        con.close()
        return {"success":False,"message":"No matching user has been found."}
    
    q2 = "UPDATE users SET is_online = TRUE where uid = ?"
    cursor.execute(q2,(matched_id,))
    con.commit()
    con.close()

    request.session["uid"] = matched_id
    return {"success":True,"message":"Welcome back {}!".format(user[1])}

@app.get("/lobby")
def lobby_page(request: Request):
    uid = request.session.get("uid")
    if uid is None:
        return RedirectResponse("/")
    return FileResponse("lobby.html")

@app.get("/me")
def get_user(request: Request):
    uid = request.session.get("uid")
    if uid is None:
        return {"error": "Not logged in"}
    
    con = sqlite3.connect("data.db")
    cursor = con.cursor()
    q1 = "SELECT uid,name,elo_rating from users where uid = ?"
    cursor.execute(q1,(uid,))
    user = cursor.fetchone()
    con.close()
    if user is None:
        return {"error": "User not found"}

    return {"uid":user[0],"name":user[1],"elo_rating":user[2]}

@app.get("/initial-lobby")
def get_initial_lobby():
    con = sqlite3.connect("data.db")
    cursor = con.cursor()
    q1 = "SELECT uid,name,elo_rating FROM users WHERE is_online = TRUE"
    cursor.execute(q1)
    users = []
    for row in cursor.fetchall():
        users.append({"uid":row[0],"name":row[1],"elo_rating":row[2]})
    con.close()
    return users

async def broadcast_lobby_update():
    con = sqlite3.connect("data.db")
    cursor = con.cursor()
    q1 = "SELECT uid,name,elo_rating FROM users WHERE is_online = TRUE"
    cursor.execute(q1)
    online_users = []
    for row in cursor.fetchall():
        online_users.append({"uid":row[0] , "name" : row[1] , "elo_rating" : row[2]})
    con.close()
    message = json.dumps({"type": "lobby_update", "users": online_users})
    for uid,ws in connected_users.items():
        await ws.send_text(message)

async def handle_challenge(challenger_uid:str,target_uid:str):
    if target_uid in connected_users:
        await connected_users[target_uid].send_text(json.dumps({
            "type":"challenge_received",
            "challenger_uid":challenger_uid,
            "challenger_name":get_name(challenger_uid)
        }))

async def handle_accept(accepter_uid:str,challenger_uid:str):
    room_id = str(uuid.uuid4())
    rooms[room_id] = {
        "players":[challenger_uid,accepter_uid],
        "board":[""]*9,
        "turn":challenger_uid
    }
    for player_uid in [challenger_uid,accepter_uid]:
        if player_uid in connected_users:
            await connected_users[player_uid].send_text(json.dumps({
                "type":"game_start",
                "room_id":room_id,
                "your_symbol": "X" if player_uid == challenger_uid else "O"
            }))

async def handle_decline(decliner_uid:str,challenger_uid:str,):
    if challenger_uid in connected_users:
        await connected_users[challenger_uid].send_text(json.dumps({
            "type":"challenge_declined"
        }))

def get_name(uid:str):
    con = sqlite3.connect("data.db")
    cursor = con.cursor()
    q1 = "SELECT name from users where uid = ?"
    cursor.execute(q1,(uid,))
    row = cursor.fetchone()
    con.close()
    if row:
        return row[0]
    else:
        return uid

def check_winner(board:list) -> str:
    wins = [[0,1,2],[3,4,5],[6,7,8],[0,3,6],[1,4,7],[2,5,8],[0,4,8],[2,4,6]]
    for combo in wins:
        if (board[combo[0]] != "" and board[combo[1]] == board[combo[2]] == board[combo[0]]):
            return board[combo[0]]
    if "" not in board:
        return "draw"
    return None

async def handle_move(uid:str,cell:int):
    room = None
    room_id = None
    for id,place in rooms.items():
        if uid in place["players"]:
            room = place
            room_id = id
            break
    if room is None:
        return
    if room["turn"] != uid:
        return
    if room["board"][cell] != "":
        return
    symbol = "X" if uid == room["players"][0] else "O"
    room["board"][cell] = symbol
    winner = check_winner(room["board"])
    next_turn = room["players"][1] if uid == room["players"][0] else room["players"][0]
    room["turn"] = next_turn
    for player_uid in room["players"]:
        if player_uid in connected_users:
            await connected_users[player_uid].send_text(json.dumps({
                "type":"board_update",
                "board":room["board"],
                "turn":next_turn,
                "winner":winner
            }))

async def handle_message(uid:str,msg:dict):
    if msg["type"] == "request_lobby":
        await broadcast_lobby_update()
    elif msg["type"] == "challenge":
        await handle_challenge(uid,msg["target_uid"])
    elif msg["type"] == "accept":
        await handle_accept(uid,msg["challenger_uid"])
    elif msg["type"] == "decline":
        await handle_decline(uid,msg["challenger_uid"])
    elif msg["type"] == "move":
        await handle_move(uid,msg["cell"])

@app.websocket("/ws/{uid}")
async def websocket_endpoint(websocket: WebSocket,uid: str):
    await websocket.accept()
    connected_users[uid] = websocket
    await broadcast_lobby_update()

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            await handle_message(uid,msg)
    except WebSocketDisconnect:
        del connected_users[uid]
        con = sqlite3.connect("data.db")
        cursor = con.cursor()
        q1 = "UPDATE users SET is_online = FALSE where uid = ?"
        cursor.execute(q1,(uid,))
        con.commit()
        con.close()
        await broadcast_lobby_update()
