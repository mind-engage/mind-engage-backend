from flask import Flask, request, jsonify
import uuid
import json
import time
import os

# Environment variable to determine the database type
DATABASE_URL = os.getenv('DATABASE_URL')

# Determine if we're using PostgreSQL or SQLite
if DATABASE_URL and 'postgresql' in DATABASE_URL:
    import psycopg2
    from psycopg2.extras import RealDictCursor

    def get_db_connection():
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
        return conn

    PLACEHOLDER = '%s'

else:
    import sqlite3

    def get_db_connection():
        conn = sqlite3.connect("quiz.db")
        conn.row_factory = sqlite3.Row
        return conn

    PLACEHOLDER = '?'

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS courses (
        course_id TEXT PRIMARY KEY,
        course_name TEXT NOT NULL,
        description TEXT,
        author TEXT NOT NULL
    );
    ''')

    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS lectures (
        lecture_id TEXT PRIMARY KEY,
        course_id TEXT,
        lecture_title TEXT NOT NULL,
        license TEXT,
        FOREIGN KEY (course_id) REFERENCES courses(course_id)
    );
    ''')

    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS topics (
        topic_id SERIAL PRIMARY KEY,
        lecture_id TEXT,
        topic_title TEXT NOT NULL,
        topic_summary TEXT,
        FOREIGN KEY (lecture_id) REFERENCES lectures(lecture_id)
    );
    ''')

    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS session (
        session TEXT PRIMARY KEY,
        start_time BIGINT
    );
    ''')

    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS user_stats (
        session TEXT,
        topic_id INTEGER,
        level INTEGER,
        user_attempt INTEGER DEFAULT 0,
        user_answer TEXT DEFAULT '',
        PRIMARY KEY(session, topic_id, level)
    );
    ''')

    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS topic_quiz (
        topic_id INTEGER,
        level INTEGER,
        question TEXT,
        choice_a TEXT,
        choice_b TEXT,
        choice_c TEXT,
        choice_d TEXT,
        answer TEXT,
        PRIMARY KEY(topic_id, level)
    );
    ''')

    conn.commit()
    cursor.close()
    conn.close()

def add_session(session):
    conn = get_db_connection()
    start_time = int(time.time())
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO session (session, start_time) VALUES ({PLACEHOLDER}, {PLACEHOLDER})", (session, start_time))
    conn.commit()
    cursor.close()
    conn.close()

def session_exists(session):
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = f'SELECT EXISTS(SELECT 1 FROM session WHERE session = {PLACEHOLDER})'
    cursor.execute(sql, (session,))
    result = cursor.fetchone()
    # Convert the result to a dictionary if it's not already
    if isinstance(result, tuple):
        exists = {'exists': result[0]}
    elif isinstance(result, dict):
        exists = result
    else:
        raise TypeError("Unexpected result type from database query")
    
    cursor.close()
    conn.close()
    return exists

def add_user_stats(session, topic_id, level):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"INSERT INTO user_stats (session, topic_id, level) VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})", (session, topic_id, level))
    conn.commit()
    cursor.close()
    conn.close()

def update_user_user_stats(session, topic_id, level, new_answer):
    """ Updates user_answer and increments user_attempt for a given session. """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First, retrieve the current user_attempt value for the given session
    cursor.execute(f'''
        SELECT user_attempt FROM user_stats WHERE session = {PLACEHOLDER} AND topic_id = {PLACEHOLDER} AND level = {PLACEHOLDER}
    ''', (session, topic_id, level))
    result = cursor.fetchone()
    
    if result:
        current_attempt = result['user_attempt']  # Get the current number of attempts
        new_attempt = current_attempt + 1  # Increment the attempt count

        # Now, update the user_answer and user_attempt in the table
        cursor.execute(f'''
            UPDATE user_stats
            SET user_answer = {PLACEHOLDER}, user_attempt = {PLACEHOLDER}
            WHERE session = {PLACEHOLDER} AND topic_id = {PLACEHOLDER} AND level = {PLACEHOLDER}
        ''', (new_answer, new_attempt, session, topic_id, level))        
        conn.commit()
    else:
        print(f"No session found with the identifier '{session}'. No update performed.")
    
    cursor.close()
    conn.close()

def update_topic_summary(topic_id, new_summary):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'''
        UPDATE topics
        SET topic_summary = {PLACEHOLDER}
        WHERE topic_id = {PLACEHOLDER}
    ''', (new_summary, topic_id))
    conn.commit()
    cursor.close()
    conn.close()

def get_topic_title(topic_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT topic_title FROM topics WHERE topic_id = {PLACEHOLDER};", (topic_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result['topic_title']
    else:
        return None

def get_topic_lecture_id(topic_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT lecture_id FROM topics WHERE topic_id = {PLACEHOLDER};", (topic_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result['lecture_id']
    else:
        return None

def get_topic_summary(topic_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT topic_summary FROM topics WHERE topic_id = {PLACEHOLDER};", (topic_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        return result['topic_summary']
    else:
        return None

def insert_topic_quiz(topic_id, level, question, choices, answer):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'''
        INSERT INTO topic_quiz (topic_id, level, question, choice_a, choice_b, choice_c, choice_d, answer)
        VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER})
        ON CONFLICT (topic_id, level) DO UPDATE SET
            question = EXCLUDED.question,
            choice_a = EXCLUDED.choice_a,
            choice_b = EXCLUDED.choice_b,
            choice_c = EXCLUDED.choice_c,
            choice_d = EXCLUDED.choice_d,
            answer = EXCLUDED.answer
    ''', (topic_id, level, question, choices[0], choices[1], choices[2], choices[3], answer))
    conn.commit()
    cursor.close()
    conn.close()

def get_topic_quiz(topic_id, level):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'''
        SELECT question, choice_a, choice_b, choice_c, choice_d, answer
        FROM topic_quiz
        WHERE topic_id = {PLACEHOLDER} AND level = {PLACEHOLDER}
    ''', (topic_id, level))
    
    data = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if data:
        result = {
            'question': data['question'],
            'choices': [data['choice_a'], data['choice_b'], data['choice_c'], data['choice_d']],
            'answer': data['answer']
        }
        return result
    else:
        return None

def fetch_lectures_by_course(course_id):
    conn = get_db_connection()
    query = f"SELECT lecture_id, lecture_title, license FROM lectures WHERE course_id = {PLACEHOLDER};"
    cursor = conn.cursor()
    cursor.execute(query, (course_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def fetch_topics_by_lecture(lecture_id):
    conn = get_db_connection()
    query = f"SELECT topic_id, topic_title FROM topics WHERE lecture_id = {PLACEHOLDER};"
    cursor = conn.cursor()
    cursor.execute(query, (lecture_id,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()
    return rows

def insert_course(course_id, course_name, description, author):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'''
    INSERT INTO courses (course_id, course_name, description, author) 
    VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER});
    ''', (course_id, course_name, description, author))
    conn.commit()
    cursor.close()
    conn.close()

def insert_lecture(lecture_id, course_id, lecture_title, license):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(f'''
        INSERT INTO lectures (lecture_id, course_id, lecture_title, license) 
        VALUES ({PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER}, {PLACEHOLDER});
        ''', (lecture_id, course_id, lecture_title, license))
        conn.commit()
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def update_lecture(lecture_id, course_id, lecture_title, license):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'''
    UPDATE lectures 
    SET course_id = {PLACEHOLDER}, lecture_title = {PLACEHOLDER}, license = {PLACEHOLDER}
    WHERE lecture_id = {PLACEHOLDER};
    ''', (course_id, lecture_title, license, lecture_id))
    conn.commit()
    cursor.close()
    conn.close()

def insert_topic(lecture_id, topic_title):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f'''
    INSERT INTO topics (lecture_id, topic_title) 
    VALUES ({PLACEHOLDER}, {PLACEHOLDER})
    RETURNING topic_id;
    ''', (lecture_id, topic_title))
    topic_id = cursor.fetchone()['topic_id']
    conn.commit()
    cursor.close()
    conn.close()
    return topic_id

def get_course_id(course_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT course_id FROM courses WHERE course_name = {PLACEHOLDER}", (course_name,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result['course_id'] if result else None

def get_lecture_id(lecture_title):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT lecture_id FROM lectures WHERE lecture_title = {PLACEHOLDER}", (lecture_title,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result['lecture_id'] if result else None

def delete_lecture_by_id(lecture_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = f'DELETE FROM lectures WHERE lecture_id = {PLACEHOLDER}'
        cursor.execute(sql, (lecture_id,))
        conn.commit()
        if cursor.rowcount == 0:
            print("No lecture found with the given lecture_id.")
        else:
            print(f"Lecture with lecture_id {lecture_id} has been deleted.")
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def delete_topics_by_lecture(lecture_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = f'DELETE FROM topics WHERE lecture_id = {PLACEHOLDER}'
        cursor.execute(sql, (lecture_id,))
        conn.commit()
        rows_deleted = cursor.rowcount
        return rows_deleted
    except Exception as e:
        conn.rollback()
        raise Exception(f"An error occurred: {e}")
    finally:
        cursor.close()
        conn.close()

create_tables()  # Ensure the table is created

