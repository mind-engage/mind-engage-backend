import sqlite3
from .states import LectureState

DATABASE_PATH = 'lecture_requests.db'

def init_db():
    conn = sqlite3.connect(DATABASE_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS requests
                 (uuid TEXT PRIMARY KEY, state TEXT)''')
    conn.commit()
    return conn

def insert_request(conn, request_uuid):
    c = conn.cursor()
    c.execute("INSERT INTO requests (uuid, state) VALUES (?, ?)", (request_uuid, LectureState.PENDING.value))
    conn.commit()

def update_request_state(conn, request_uuid, state):
    c = conn.cursor()
    c.execute("UPDATE requests SET state = ? WHERE uuid = ?", (state.value, request_uuid))
    conn.commit()

def get_request_state(conn, request_uuid):
    c = conn.cursor()
    c.execute("SELECT state FROM requests WHERE uuid = ?", (request_uuid,))
    row = c.fetchone()
    return row[0] if row else None
