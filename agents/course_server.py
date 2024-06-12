from flask import Flask, request, jsonify
import uuid
import sqlite3
import json

from course_agent import create_embedding, generate_topic_titles, create_lecture
from database import get_lecture_id, delete_topics_by_lecture, delete_lecture_by_id

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

if __name__ == '__main__':
    app.run(debug=True)
