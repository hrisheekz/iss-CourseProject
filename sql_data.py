import sqlite3

con = sqlite3.connect("data.db")
cursor = con.cursor()

q1 = "CREATE TABLE IF NOT EXISTS users(uid VARCHAR(255) PRIMARY KEY , name VARCHAR(255) NOT NULL , elo_rating INTEGER DEFAULT 1200 , is_online BOOLEAN DEFAULT FALSE)"
cursor.execute(q1)

# Prints all users within the users table (for verifying results)
# q2 = "SELECT * FROM users"
# cursor.execute(q2)
# rows = cursor.fetchall()
# for row in rows:
#     print(row)

con.close()
