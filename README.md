# Identity-Verified Multiplayer Arena

A real-time multiplayer web application where users authenticate via facial recognition and compete in head-to-head Tic-Tac-Toe matches. The system uses a hybrid database architecture: SQLite for relational metadata (user info, Elo ratings) and MongoDB for storing profile images. Matchmaking and gameplay are handled via WebSockets, with automatic Elo updates and disconnect-based forfeits.

## Database Schemas

### SQLite (Relational Metadata)
Run the following to initialise the SQLite database:
```bash
uv run python sql_data.py
```

Schema:
```sql
CREATE TABLE IF NOT EXISTS users (
    uid         VARCHAR(255) PRIMARY KEY,
    name        VARCHAR(255) NOT NULL,
    elo_rating  INTEGER      DEFAULT 1200,
    is_online   BOOLEAN      DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS matches (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    winner_uid   VARCHAR(255) NOT NULL,
    loser_uid    VARCHAR(255) NOT NULL,
    result       VARCHAR(255) NOT NULL,
    timestamp    DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### MongoDB (Image Storage)
Ensure MongoDB is running locally on the default port:
```bash
mongod
```
No manual setup required — the scraper automatically creates the `multiplayer_arena` database and `users` collection.

## Initialising the Databases

**Step 1:** Initialise the SQLite schema:
```bash
uv run python sql_data.py
```

**Step 2:** Run the scraper to populate both databases:
```bash
uv run python scraper.py
```
This fetches profile images from each student's website, inserts metadata into SQLite, and stores images in MongoDB.

## Starting the Server

```bash
uv run uvicorn main:app --reload
```

Note: On first startup, the server will build a facial recognition encodings cache from all stored profile images. This may take 1-2 minutes. Wait for `Application startup complete` before opening the browser.

The WebSocket server runs on the same process as the HTTP server via FastAPI — no separate command needed.

## Assumptions

- MongoDB is used exclusively for binary image storage as per the polyglot persistence requirement.
- Profile images are fetched from `https://<website_url>/images/pfp.jpg` as specified. Students whose URLs returned a 404 or timeout are skipped gracefully and will not be able to log in.
- A small portion of students could not be encoded by the facial recognition module due to undetectable faces in their profile images.
- The WebSocket server and HTTP server are co-located in the same FastAPI application.
- Session management is handled server-side using `itsdangerous` via Starlette's `SessionMiddleware`.
- A player who disconnects mid-game forfeits the match regardless of board state, and Elo is updated accordingly.



## Team & Contributions
* **Hrisheek Patnala (Myself)** - Developed phase-4 and the frontend
* **Aditya Ak** - Developed major part of the backend including phase 2 and 3
* **Kimaya Arora** - Developed majority of the frontend and phase 1

Specifications about each of the phases of the project and all the requirements have been specified in [Project-doc.pdf](Project-doc.pdf)
