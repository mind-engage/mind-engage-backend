from flask import Flask, request, jsonify
import uuid
import sqlite3
import json
import os
from werkzeug.utils import secure_filename
import threading
import requests
import magic  # Import python-magic library
from .states import LectureState
from .database import init_db, insert_request, update_request_state, get_request_state

from agents.course_agent import create_embedding, generate_topic_titles
from agents.database import get_lecture_id, delete_topics_by_lecture, delete_lecture_by_id, insert_lecture, update_lecture

app = Flask(__name__)

# Configuration for the upload and transcripts folders
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'data/uploads')
app.config['TRANSCRIPTS_FOLDER'] = os.environ.get('TRANSCRIPTS_FOLDER', 'data/transcripts')
# Get the transcription service URL from environment variable
TRANSCRIPTION_SERVICE_URL = os.getenv('TRANSCRIPTION_SERVICE_URL', 'http://127.0.0.1:8080/inference')

# Define the allowed file extensions for uploads
# ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'mp4', 'txt'}
ALLOWED_EXTENSIONS = {'mp3', 'txt'}


# Initialize the database connection
conn = init_db()

@app.route('/titles/create', methods=['POST'])
def create_titles():
    data = request.json
    lecture_id = data.get('lecture_id')
    if lecture_id is None:
        return jsonify({'error': 'Lecture ID is required'}), 400
    result = generate_topic_titles(lecture_id)
    return jsonify(result), 200 if result else 500

@app.route('/titles/delete', methods=['DELETE'])
def delete_titles():
    data = request.json
    lecture_id = data.get('lecture_id')
    if lecture_id is None:
        return jsonify({'error': 'Lecture ID is required'}), 400
    result = delete_topics_by_lecture(lecture_id)
    if not result:
        return jsonify({'error': 'Failed to delete topic titles'}), 500
    return jsonify({'message': 'Topics deleted successfully'}), 200

# Function to check if a file extension is allowed
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_text_file(file_path):
    mime = magic.Magic(mime=True)
    mime_type = mime.from_file(file_path)
    return mime_type.startswith('text')

def transcribe(file_path):
    url = TRANSCRIPTION_SERVICE_URL
    with open(file_path, 'rb') as file:
        response = requests.post(
            url,
            files={'file': file},
            data={
                'temperature': '0.0',
                'temperature_inc': '0.2',
                'response_format': 'json'
            },
            timeout=3600
        )
    if response.status_code == 200:
        transcription_result = response.json()
        # Assuming the response contains the transcription text under the key 'transcription'
        return transcription_result.get("text", 'transcription_failed')
    else:
        return None

def process_request(request_uuid, file_path, title, description, license):
    update_request_state(conn, request_uuid, LectureState.INIT)

    # Use request_id as lecture_id
    lecture_id = request_uuid
    if is_text_file(file_path):
        lecture_text = file_path
    else:
        lecture_text = transcribe(file_path)
        if lecture_text is None or lecture_text == 'transcription_failed':
            update_request_state(conn, request_uuid, LectureState.TRANSCRIPTION_FAILED)
            return

        # Save the transcribed text to a file
        transcript_filename = f"{request_uuid}.txt"
        transcript_file_path = os.path.join(app.config['TRANSCRIPTS_FOLDER'], transcript_filename)
        with open(transcript_file_path, 'w') as transcript_file:
            transcript_file.write(lecture_text)
        lecture_text = transcript_file_path

    update_request_state(conn, request_uuid, LectureState.CREATE_EMBEDDING)
    result = create_embedding(lecture_text, lecture_id)
    if not result:
        update_request_state(conn, request_uuid, LectureState.CREATE_EMBEDDING_FAILED)
        return

    update_request_state(conn, request_uuid, LectureState.GENERATE_TOPIC_TITLES)
    result = generate_topic_titles(lecture_id)
    if not result:
        update_request_state(conn, request_uuid, LectureState.GENERATE_TOPIC_TITLES_FAILED)
        return

    # Now create the lecture after success state
    course_id = 1  # Placeholder for course_id, which should be retrieved or passed in the request
    result = insert_lecture(lecture_id, course_id, title, license)
    if not result:
        update_request_state(conn, request_uuid, LectureState.FAILED_TO_CREATE_LECTURE)
        return

    update_request_state(conn, request_uuid, LectureState.SUCCESS)

@app.route('/lecture/create', methods=['POST'])
def create_lecture_endpoint():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    # Check if the file has a valid extension
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        # Generate UUID for the request and use it to create a unique filename
        request_uuid = str(uuid.uuid4())
        filename = secure_filename(f"{request_uuid}_{file.filename}")
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Retrieve data from request body
        data = request.form
        title = data.get('title')
        description = data.get('description')
        license = data.get('license')

        if not all([title, description, license]):
            return jsonify({'error': 'All fields are required'}), 400

        insert_request(conn, request_uuid)

        # Spawn a thread to process the request
        thread = threading.Thread(target=process_request, args=(request_uuid, file_path, title, description, license))
        thread.start()

        return jsonify({'uuid': request_uuid}), 200
    else:
        return jsonify({'error': 'File type not allowed'}), 400

@app.route('/lecture/delete', methods=['DELETE'])
def delete_lecture():
    data = request.json
    lecture_id = data.get('lecture_id')
    if lecture_id is None:
        return jsonify({'error': 'Lecture ID is required'}), 400

    result = delete_topics_by_lecture(lecture_id)
    if not result:
        return jsonify({'error': 'Failed to delete topics by lecture'}), 500

    result = delete_lecture_by_id(lecture_id)
    if not result:
        return jsonify({'error': 'Failed to delete lecture'}), 500

    return jsonify({'message': 'Lecture deleted successfully'}), 200

@app.route('/lecture/status/<request_uuid>', methods=['GET'])
def status_lecture_endpoint(request_uuid):
    state = get_request_state(conn, request_uuid)
    if state:
        return jsonify({'uuid': request_uuid, 'state': state}), 200
    else:
        return jsonify({'error': 'Request not found'}), 404

if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['TRANSCRIPTS_FOLDER'], exist_ok=True)
    app.run(debug=True)
