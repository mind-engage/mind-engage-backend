# Rest server

from flask import Flask, request, jsonify
import uuid
import sqlite3
import json
import pandas as pd
import time

# Initialize and configure the SQLite database
def get_db_connection():
    conn = sqlite3.connect("quiz.db")
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    
    conn.execute('''
    CREATE TABLE IF NOT EXISTS courses (
        course_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_name TEXT NOT NULL,
        description TEXT,
        author TEXT NOT NULL
    );
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS lectures (
        lecture_id INTEGER PRIMARY KEY AUTOINCREMENT,
        course_id INTEGER,
        lecture_title TEXT NOT NULL,
        license TEXT,
        FOREIGN KEY (course_id) REFERENCES courses(course_id)
    );
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS topics (
        topic_id INTEGER PRIMARY KEY AUTOINCREMENT,
        lecture_id INTEGER,
        topic_title TEXT NOT NULL,
        topic_summary TEXT,
        FOREIGN KEY (lecture_id) REFERENCES lectures(lecture_id)
    );
    ''')

    conn.execute('''
    CREATE TABLE IF NOT EXISTS session (
        session TEXT PRIMARY KEY,
        start_time INTEGER
    );
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_stats (
            session  TEXT,
            topic_id INTEGER,
            level    INTEGER
            user_attempt INTEGER DEFAULT 0,
            user_answer TEXT DEFAULT '',
            PRIMARY KEY(session, topic_id, level)
        );
    ''')

    conn.execute('''
        CREATE TABLE IF NOT EXISTS topic_quiz (
            topic_id INTEGER KEY,
            level INTEGER KEY,
            question TEXT,
            choice_a TEXT,
            choice_b TEXT,
            choice_c TEXT,
            choice_d TEXT,
            answer   TEXT,
            PRIMARY KEY(topic_id, level)
        );
        '''
    )

    conn.commit()
    conn.close()


def add_session(session):
    conn = get_db_connection()
    start_time = int(time.time())
    conn.execute("INSERT INTO session (session, start_time) VALUES (?, ?)", (session, start_time))    
    conn.commit()
    conn.close()

def session_exists(session):
    conn = get_db_connection()

    sql = 'SELECT EXISTS(SELECT 1 FROM session WHERE session = ?)'
    cur = conn.cursor()
    try:
        # Execute the SQL command
        cur.execute(sql, (session,))
        # Fetch the result
        exists = cur.fetchone()[0]
        return bool(exists)
    except sqlite3.Error as e:
        print("An error occurred:", e)
        return False
    finally:
        # Close the cursor
        cur.close()
        conn.close()

def add_user_stats(session, topic_id, level):
    conn = get_db_connection()
    conn.execute("INSERT INTO user_stats (session, answer) VALUES (?, ?)", (session, answer))
    conn.commit()
    conn.close()


def update_user_user_stats(session, topic_id, level, new_answer):
    """ Updates user_answer and increments user_attempt for a given session. """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # First, retrieve the current user_attempt value for the given session
    cursor.execute('''
        SELECT user_attempt FROM user_stats WHERE session = ? AND topic_id = ? AND level = ?
    ''', (session, topic_id, level))
    result = cursor.fetchone()
    
    if result:
        current_attempt = result[0]  # Get the current number of attempts
        new_attempt = current_attempt + 1  # Increment the attempt count

        # Now, update the user_answer and user_attempt in the table
        cursor.execute('''
            UPDATE quiz
            SET user_answer = ?, user_attempt = ?
            WHERE session = ? AND topic_id = ? AND level = ?
        ''', (new_answer, new_attempt, session, topic_id, level))        
        conn.commit()
    else:
        print(f"No session found with the identifier '{session}'. No update performed.")
    
    cursor.close()
    conn.close()

def update_topic_summary(topic_id, new_summary):
    conn = get_db_connection()  # This function needs to be defined to handle your database connection
    """ Update the summary of a topic in the topics table """
    try:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE topics
            SET topic_summary = ?
            WHERE topic_id = ?
        ''', (new_summary, topic_id))
        conn.commit()
        cursor.close()
    except Exception as e:
        print("An error occurred while updating the topic summary:", e)
    finally:
        conn.close()

def get_topic_title(topic_id):
    conn = get_db_connection()
    query = "SELECT topic_title FROM topics WHERE topic_id = ?;"
    df = pd.read_sql_query(query, conn, params=(topic_id,))
    conn.close()

    if not df.empty:
        topic = df.iloc[0]['topic_title']
        return topic    
    else:
        return None

def get_topic_lecture_id(topic_id):
    conn = get_db_connection()
    query = "SELECT lecture_id FROM topics WHERE topic_id = ?;"
    df = pd.read_sql_query(query, conn, params=(topic_id,))
    conn.close()

    if not df.empty:
        lecture_id = df.iloc[0]['lecture_id']
        return lecture_id    
    else:
        return None

def get_topic_summary(topic_id):
    conn = get_db_connection()
    query = "SELECT topic_summary FROM topics WHERE topic_id = ?;"
    df = pd.read_sql_query(query, conn, params=(topic_id,))
    conn.close()

    if not df.empty:
        topic_summary = df.iloc[0]['topic_summary']
        return topic_summary    
    else:
        return None

def insert_topic_quiz(topic_id, level,  question, choices, answer):
    conn = get_db_connection()
    """ Insert a new topic quiz into the topic_quiz table or update if it already exists """
    try:
        conn.execute('''
            INSERT INTO topic_quiz (topic_id, level, question, choice_a, choice_b, choice_c, choice_d, answer)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(topic_id, level) DO UPDATE SET
            question=excluded.question,
            choice_a=excluded.choice_a,
            choice_b=excluded.choice_b,
            choice_c=excluded.choice_c,
            choice_d=excluded.choice_d,
            answer=excluded.answer
        ''', (topic_id,
              level,
              question,
              choices[0],  # assuming choices is a list of 4 items
              choices[1],
              choices[2],
              choices[3],
              answer))
        conn.commit()
    finally:
        conn.close()

def get_topic_quiz(topic_id, level):
    conn = get_db_connection()
    """ Retrieve a topic quiz from the topic_quiz table """
    try:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT question, choice_a, choice_b, choice_c, choice_d, answer
            FROM topic_quiz
            WHERE topic_id = ? AND level = ?
        ''', (topic_id, level))
        
        # Fetch the data
        data = cursor.fetchone()
        if data:
            result = {
                'question': data[0],
                'choices': [
                    data[1],
                    data[2],
                    data[3],
                    data[4]
                ],
                'answer': data[5]
            }
            return result
        else:
            return None  # or you can raise an exception or return an error message if preferred
    except Exception as e:
        print("An error occurred while retrieving the topic quiz:", e)
        return None
    finally:
        conn.close()

def fetch_lectures_by_course(course_id):
    conn = get_db_connection()
    query = "SELECT lecture_id, lecture_title, license FROM lectures WHERE course_id = ?;"
    cursor = conn.cursor()
    cursor.execute(query, (course_id,))
    rows = cursor.fetchall()  # Fetch all rows as a list of tuples
    conn.close()
    return rows


def fetch_topics_by_lecture(lecture_id):
    conn = get_db_connection()
    query = """
        SELECT topic_id, topic_title FROM topics WHERE lecture_id = ?;
    """
    cursor = conn.cursor()
    cursor.execute(query, (lecture_id,))
    rows = cursor.fetchall()  # Fetch all rows as a list of tuples
    conn.close()
    return rows

# Functions used by course_agent
#
def insert_course(course_name, description, author):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO courses (course_name, description, author) 
    VALUES (?, ?, ?);
    ''', (course_name, description, author))
    conn.commit()
    # Retrieve the ID of the newly inserted course
    course_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return course_id

def insert_lecture(course_id, lecture_title, license):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO lectures (course_id, lecture_title, license) 
    VALUES (?, ?, ?);
    ''', (course_id, lecture_title, license))
    conn.commit()
    lecture_id = cursor.lastrowid  # Retrieve the ID of the newly inserted lecture
    cursor.close()
    conn.close()
    return lecture_id

def insert_topic(lecture_id, topic_title):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO topics (lecture_id, topic_title) 
    VALUES (?, ?);
    ''', (lecture_id, topic_title))
    conn.commit()
    topic_id = cursor.lastrowid  # Retrieve the ID of the newly inserted topic
    cursor.close()
    conn.close()
    return topic_id

def get_course_id(course_name):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT course_id FROM courses WHERE course_name = ?", (course_name,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result['course_id'] if result else None

def get_lecture_id(lecture_title):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT lecture_id FROM lectures WHERE lecture_title = ?", (lecture_title,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result['lecture_id'] if result else None

def delete_lecture_by_id(lecture_id):
    conn =  get_db_connection()
    cursor = conn.cursor()
    
    try:
        # SQL command to delete a lecture by lecture_id
        sql = 'DELETE FROM lectures WHERE lecture_id = ?'
        
        # Execute the SQL command
        cursor.execute(sql, (lecture_id,))
        
        # Commit the changes to the database
        conn.commit()
        
        # Check if the row was deleted
        if cursor.rowcount == 0:
            print("No lecture found with the given lecture_id.")
        else:
            print(f"Lecture with lecture_id {lecture_id} has been deleted.")
        return True
    except sqlite3.Error as e:
        # Print an error message if an exception occurs
        print(f"An error occurred: {e}")
        return False
    finally:
        # Close the database connection
        cursor.close()
        conn.close()


def delete_topics_by_lecture(lecture_id):
    """
    Deletes all topics associated with a specific lecture_id from the 'topics' table.

    Args:
        lecture_id (int): The ID of the lecture for which topics should be deleted.

    Returns:
        int: The number of rows deleted.

    Raises:
        Exception: If an error occurs during the database operation.
    """
    # Connect to the SQLite database
    conn =  get_db_connection()
    cur = conn.cursor()

    try:
        # SQL statement to delete rows
        sql = 'DELETE FROM topics WHERE lecture_id = ?'
        
        # Execute the deletion command
        cur.execute(sql, (lecture_id,))

        # Commit the changes to the database
        conn.commit()

        # Return the number of rows affected
        rows_deleted = cur.rowcount
        return rows_deleted

    except Exception as e:
        # Rollback any changes if an exception occurred
        conn.rollback()
        raise Exception(f"An error occurred: {e}")

    finally:
        # Close the database connection
        cur.close()
        conn.close()

create_tables()  # Ensure the table is created
