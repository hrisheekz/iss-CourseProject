from pymongo import MongoClient
import csv
import sqlite3
import requests

client = MongoClient("mongodb://localhost:27017/")
db = client["multiplayer_arena"]
user_collection = db["users"]

con = sqlite3.connect("data.db")
cursor = con.cursor()

with open("batch_data.csv","r") as f:
    reader = csv.reader(f)
    next(reader)
    for line in reader:
        uid = line[0]
        name = line[1]
        website_url = line[2]
        image_url = "https://" + website_url + "/images/pfp.jpg"
        try:
            response = requests.get(image_url,timeout=10)
            if (response.status_code == 200):
                # Now INSERT data into MYSQL table
                q2 = "INSERT INTO users(uid,name) VALUES(?,?)"
                cursor.execute(q2,(uid,name))
                # Executes an UPSERT into MongoDB, storing the image as BSON binary data or a Base64 string, keyed by the student’s uid.
                user_collection.update_one(
                    {"uid": uid},
                    {"$set": {"profile_image": response.content}},
                    upsert = True
                )
            else:
                print(f"Failed to fetch image for {name} with uid {uid}")
            con.commit()
        except Exception as e:
            print(f"Error fetching image for {name} with uid {uid}: {e}")

# Prints all users within the users table and theire corresponding images sizes (for verifying results)

# print("Total images stored:", user_collection.count_documents({}))
# for doc in user_collection.find({},{"uid": 1, "profile_image": 1}).limit(user_collection.count_documents({})):
#     print(f"UID: {doc['uid']}, Image size: {len(doc['profile_image'])} bytes")

con.close()
