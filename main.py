from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pymongo import MongoClient
import sqlite3
from utils.facial_recognition_module import find_closest_match

client = MongoClient("mongodb://localhost:27017/")
db = client["multiplayer_arena"]
user_collection = db["users"]

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def login_page():
    return FileResponse("identity.html")

class LoginRequest(BaseModel):
    image:str

@app.post("/login")
def login(request:LoginRequest):
    db_images_dict = {}
    for doc in user_collection.find({},{"uid":1,"profile_image":1}):
        db_images_dict[doc["uid"]] = doc["profile_image"]
    matched_id = find_closest_match(request.image,db_images_dict)
    print("Testing with", len(db_images_dict), "images")
    print("Done loading — face recognition module is accessible")

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

    return {"success":True,"message":"Welcome back {}!".format(user[1])}