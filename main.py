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
from utils.facial_recognition_module import find_closest_match, build_encodings_cache

client = MongoClient("mongodb://localhost:27017/")
db = client["multiplayer_arena"]
user_collection = db["users"]

db_images_dict = {doc["uid"]: doc["profile_image"] for doc in user_collection.find({},{"uid":1,"profile_image":1})}
encodings_cache = build_encodings_cache(db_images_dict)

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
    matched_id = find_closest_match(body.image,encodings_cache)
    
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


# -----*------ phase 4
def update_elo(p1_uid: str, p2_uid: str, p1_score: float):
    
     # score: 1.0 for a win, 0.5 for a draw, 0.0 for a loss
    
    con = sqlite3.connect("data.db")
    cursor = con.cursor()
    
    cursor.execute("SELECT elo_rating FROM users WHERE uid = ?", (p1_uid,))
    p1_rating = cursor.fetchone()[0]
    
    cursor.execute("SELECT elo_rating FROM users WHERE uid = ?", (p2_uid,))
    p2_rating = cursor.fetchone()[0]
    
    # Elo Math
    K = 32
    E1 = 1 / (1 + 10 ** ((p2_rating - p1_rating) / 400))
    E2 = 1 / (1 + 10 ** ((p1_rating - p2_rating) / 400))
    
    p2_score = 1.0 - p1_score
    
    new_p1 = round(p1_rating + K * (p1_score - E1))
    new_p2 = round(p2_rating + K * (p2_score - E2))
    
    cursor.execute("UPDATE users SET elo_rating = ? WHERE uid = ?", (new_p1, p1_uid))
    cursor.execute("UPDATE users SET elo_rating = ? WHERE uid = ?", (new_p2, p2_uid))
    con.commit()
    con.close()


# ------*------

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
    if winner is None:
        next_turn = room["players"][1] if uid == room["players"][0] else room["players"][0]
        room["turn"] = next_turn
    else:
        next_turn = None
    
    for player_uid in room["players"]:
        if player_uid in connected_users:
            await connected_users[player_uid].send_text(json.dumps({
                "type":"board_update",
                "board":room["board"],
                "turn":next_turn,
                "winner":winner
            }))
    # --- phase 4: update elo 
    if winner is not None:
        p1_uid = room["players"][0]  # "X"
        p2_uid = room["players"][1]  # "O"
        
        if winner == "draw":
            update_elo(p1_uid, p2_uid, 0.5)
        else:
            if winner == "X":
                p1_score = 1.0
            else:
                p1_score = 0.0
            update_elo(p1_uid, p2_uid, p1_score)
            
        del rooms[room_id]
        await broadcast_lobby_update()

async def handle_get_game_state(uid:str,room_id:str):
    if room_id not in rooms:
        return
    room = rooms[room_id]
    opponent_uid = room["players"][1] if uid == room["players"][0] else room["players"][0]
    await connected_users[uid].send_text(json.dumps({
        "type":"game_init",
        "your_symbol":"X" if uid == room["players"][0] else "O",
        "opponent_name":get_name(opponent_uid),
        "turn":room["turn"],
        "board":room["board"]
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
    elif msg["type"] == "get_game_state":
        await handle_get_game_state(uid,msg["room_id"])
    elif msg["type"] == "forfeit":
        await handle_forfeit(uid)

@app.websocket("/ws/{uid}")
async def websocket_endpoint(websocket: WebSocket,uid: str):
    await websocket.accept()
    connected_users[uid] = websocket
    con = sqlite3.connect("data.db")
    cursor = con.cursor()
    q1 = "UPDATE users SET is_online = TRUE where uid = ?"
    cursor.execute(q1,(uid,))
    con.commit()
    con.close()
    
    in_room = False
    for room_id, room in rooms.items():
        if uid in room["players"]:
            await handle_get_game_state(uid, room_id)
            in_room = True
            break

    if not in_room:
        await broadcast_lobby_update()

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            await handle_message(uid,msg)
    except WebSocketDisconnect:
        del connected_users[uid]
        # con = sqlite3.connect("data.db")
        # cursor = con.cursor()
        # q1 = "UPDATE users SET is_online = FALSE where uid = ?"
        # cursor.execute(q1,(uid,))
        # con.commit()
        # con.close()
        # await broadcast_lobby_update()

        # --- phase 4 -  handle mid match disconnects
        room_to_delete = None
        for room_id, room in rooms.items():
            if uid in room["players"]:
                if any(cell != "" for cell in room["board"]):
                    remaining_player = room["players"][1] if room["players"][0] == uid else room["players"][0]
                
                    update_elo(remaining_player, uid, 1.0) # remaining player wins
                    
                    if remaining_player in connected_users:
                        await connected_users[remaining_player].send_text(json.dumps({
                            "type": "game_over",
                            "reason": "opponent_disconnected",
                            "winner": "you"
                        }))
                    room_to_delete = room_id
                break
                
        if room_to_delete:
            del rooms[room_to_delete]
            
        # Original offline status update
        con = sqlite3.connect("data.db")
        cursor = con.cursor()
        q1 = "UPDATE users SET is_online = FALSE where uid = ?"
        cursor.execute(q1,(uid,))
        con.commit()
        con.close()
        await broadcast_lobby_update()

@app.get("/game")
def game_page(request:Request):
    id = request.session.get("uid")
    if id is None:
        return RedirectResponse("/")
    return FileResponse("game.html")

# phase 4 ----*------
@app.get("/leaderboard")
def leaderboard_page(request: Request):
    if request.session.get("uid") is None:
         return RedirectResponse("/")
    return FileResponse("leaderboard.html")

@app.get("/api/leaderboard")
def get_leaderboard():
    con = sqlite3.connect("data.db")
    cursor = con.cursor()
    cursor.execute("SELECT uid, name, elo_rating, is_online FROM users ORDER BY elo_rating DESC")
    users = [
        {
            "rank": i + 1,
            "uid": row[0],
            "name": row[1],
            "elo_rating": row[2],
            "is_online": bool(row[3])
        }
        for i, row in enumerate(cursor.fetchall())
    ]
    con.close()
    return users


async def handle_forfeit(uid: str):
    room = None
    room_id = None
    
    for id, place in rooms.items():
        if uid in place["players"]:
            room = place
            room_id = id
            break
            
    if room is None:
        return

    opponent_uid = room["players"][1] if uid == room["players"][0] else room["players"][0]
    
    update_elo(opponent_uid, uid, 1.0) 
    
    for player_uid in room["players"]:
        if player_uid in connected_users:
            winner_status = "you" if player_uid == opponent_uid else "opponent"
            await connected_users[player_uid].send_text(json.dumps({
                "type": "game_over",
                "reason": "forfeit",
                "winner": winner_status
            }))
            
    del rooms[room_id]
    await broadcast_lobby_update()