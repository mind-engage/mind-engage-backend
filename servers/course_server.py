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

from agents.course_agent import create_embedding, generate_topic_titles, create_lecture
from agents.database import get_lecture_id, delete_topics_by_lecture, delete_lecture_by_id


app = Flask(__name__)

# Configuration for the upload folder
UPLOAD_FOLDER = 'path_to_upload_folder'  # Set the path to the folder where files will be saved
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Define the allowed file extensions for uploads
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg', 'mp4', 'txt'}

# Get the transcription service URL from environment variable
TRANSCRIPTION_SERVICE_URL = os.getenv('TRANSCRIPTION_SERVICE_URL', 'http://127.0.0.1:8080/inference')

# Initialize the database connection
conn = init_db()


app = Flask(__name__)

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

@app.route('/lecture/create', methods=['POST'])
def create_lecture_endpoint():
    data = request.json
    course_id = data.get('course_id')
    lecture_name = data.get('lecture_name')
    lecture_source = data.get('lecture_source')
    lecture_license = data.get('lecture_license')

    if not all([course_id, lecture_name, lecture_source, lecture_license]):
        return jsonify({'error': 'All fields are required'}), 400

    lecture_id = create_lecture(course_id, lecture_name, lecture_license)
    if not lecture_id:
        return jsonify({'error': 'Failed to create lecture'}), 500

    result = create_embedding(lecture_source, lecture_id)
    if not result:
        return jsonify({'error': 'Failed to create embedding'}), 500

    result = generate_topic_titles(lecture_id)
    if not result:
        return jsonify({'error': 'Failed to create topic titles'}), 500
    
    return jsonify({'message': 'Lecture created successfully', 'lecture_id': lecture_id}), 200


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
        return transcription_result.get('transcription', 'transcription_failed')
    else:
        return None

def process_request(request_uuid, file_path, title, description, license):
    update_request_state(conn, request_uuid, LectureState.INIT)

    if is_text_file(file_path):
        lecture_source = file_path
    else:
        lecture_source = transcribe(file_path)
        if lecture_source is None or lecture_source == 'transcription_failed':
            update_request_state(conn, request_uuid, LectureState.TRANSCRIPTION_FAILED)
            return

    update_request_state(conn, request_uuid, LectureState.CREATE_EMBEDDING)
    result = create_embedding(lecture_source)
    if not result:
        update_request_state(conn, request_uuid, LectureState.CREATE_EMBEDDING_FAILED)
        return

    update_request_state(conn, request_uuid, LectureState.GENERATE_TOPIC_TITLES)
    result = generate_topic_titles()
    if not result:
        update_request_state(conn, request_uuid, LectureState.GENERATE_TOPIC_TITLES_FAILED)
        return

    update_request_state(conn, request_uuid, LectureState.SUCCESS)

    # Now create the lecture after success state
    course_id = 1  # Placeholder for course_id, which should be retrieved or passed in the request
    lecture_id = create_lecture(course_id, title, license)
    if not lecture_id:
        update_request_state(conn, request_uuid, LectureState.FAILED_TO_CREATE_LECTURE)
        return

@app.route('/lecture/upload_create', methods=['POST'])
def upload_create_lecture_endpoint():
    # Check if a file was uploaded
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    # Check if the file has a valid extension
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Retrieve data from request body
        data = request.form
        title = data.get('title')
        description = data.get('description')
        license = data.get('license')

        if not all([title, description, license]):
            return jsonify({'error': 'All fields are required'}), 400

        # Generate UUID for the request
        request_uuid = str(uuid.uuid4())
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
    app.config['UPLOAD_FOLDER'] = 'topic_embeddings'  # Configure upload folder
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True)
