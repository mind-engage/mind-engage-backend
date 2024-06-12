from flask import Flask, request, jsonify
import uuid

from agents.query_agent import QueryAgent, generate_quiz_and_cache, generate_conceptual_clarity
from agents.database import (
    get_topic_quiz, 
    get_topic_summary, 
    fetch_lectures_by_course, 
    fetch_topics_by_lecture, 
    add_session, 
    session_exists,
    get_topic_lecture_id)

import agents.concept_prompt
import agents.quiz_prompt

#query_agent = QueryAgent(quiz_prompt.PREFIX, quiz_prompt.FORMAT_INSTRUCTIONS, quiz_prompt.SUFFIX)
#query_agent.setup_workflow()

app = Flask(__name__)


@app.route('/register', methods=['POST'])
def register():
    session_id = str(uuid.uuid4())
    add_session(session_id)
    return jsonify({'session_id': session_id})

@app.route('/lectures', methods=['GET'])
def lectures():
    session_id = request.args['session_id']
    if not session_exists(session_id):
        return jsonify({'error': 'Invalid session ID'}), 401
    course_id = request.args.get('course_id', 1)  # Default course ID
    rows = fetch_lectures_by_course(course_id)
    lectures = [{'lecture_id': row[0], 'lecture_title': row[1], 'license': row[2]} for row in rows]
    return jsonify(lectures)

@app.route('/topics', methods=['GET'])
def topics():
    session_id = request.args['session_id']
    if not session_exists(session_id):
        return jsonify({'error': 'Invalid session ID'}), 401
    lecture_id = request.args['lecture_id']
    rows = fetch_topics_by_lecture(lecture_id)
    topics = [{'topic_id': row[0], 'topic_title': row[1]} for row in rows]
    return jsonify(topics)

@app.route('/quiz', methods=['GET'])
def quiz():
    session_id = request.args['session_id']
    if not session_exists(session_id):
        return jsonify({'error': 'Invalid session ID'}), 401
    topic_id = int(request.args['topic_id'])
    level = int(request.args.get('level', 0))
    quiz = get_topic_quiz(topic_id, level)
    if not quiz:
        lecture_id = get_topic_lecture_id(topic_id)
        rag_db = str(lecture_id)
        quiz_agent = QueryAgent(rag_db, quiz_prompt.PREFIX, quiz_prompt.FORMAT_INSTRUCTIONS, quiz_prompt.SUFFIX)
        quiz_agent.setup_workflow()
        generate_quiz_and_cache(quiz_agent, topic_id)
        quiz = get_topic_quiz(topic_id, level)
    topic_summary = get_topic_summary(topic_id)
    response = {
        "topic_id": topic_id,
        "level": level,
        "summary": topic_summary,
        "question": quiz["question"],
        "choices": quiz["choices"]
    }
    return jsonify(response)

@app.route('/conceptual_clarity', methods=['GET'])
def conceptual_clarity():
    session_id = request.args['session_id']
    if not session_exists(session_id):
        return jsonify({'error': 'Invalid session ID'}), 401
    topic_id = int(request.args['topic_id'])
    level = request.args['level']
    answer = request.args['answer']
    quiz_dict = get_topic_quiz(topic_id, int(level))
    topic_summary = get_topic_summary(topic_id)
    lecture_id = get_topic_lecture_id(topic_id)
    rag_db = str(lecture_id)
    prompt_prefix = concept_prompt.get_formatted(concept_prompt.PREFIX, topic_summary, quiz_dict, answer)
    concept_agent = QueryAgent(rag_db, prompt_prefix, concept_prompt.FORMAT_INSTRUCTIONS, concept_prompt.SUFFIX)
    concept_agent.setup_workflow()
    concept = generate_conceptual_clarity(concept_agent, topic_id)
    return jsonify({'concept': concept, 'summary': topic_summary})

@app.route('/submit_answer', methods=['POST'])
def submit_answer():
    session_id = request.json['session_id']
    if not session_exists(session_id):
        return jsonify({'error': 'Invalid session ID'}), 401
    topic_id = int(request.json['topic_id'])
    level = request.json['level']
    user_answer = request.json['answer']

    quiz_dict = get_topic_quiz(topic_id, int(level))
    correct_answer = quiz_dict["answer"]
    if ord(correct_answer) == ord('a') + user_answer:
        response = {"message": "Correct Answer", "result": 'true'}
    else:
        response = {"message": "Wrong Answer", "result": 'false'}
    return jsonify(response)

    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
