from flask import Flask, request, jsonify
import uuid
import sqlite3
import json

from course_agent import create_embedding, generate_topic_titles, create_lecture
from database import get_lecture_id
import argparse
from database import delete_topics_by_lecture, delete_lecture_by_id

app = Flask(__name__)


# Create the main parser
parser = argparse.ArgumentParser(description="Main command-line parser")
sub_parsers = parser.add_subparsers(dest='command', help='sub-command help')

# Create a parser for the "titles" sub-command
parser_titles = sub_parsers.add_parser('titles', help='titles sub-command')
titles_subparsers = parser_titles.add_subparsers(dest='title_command', help='titles operation')

# Create a parser for the "create" command under "titles"
parser_title_create = titles_subparsers.add_parser('create', help='create titles')

# Create a parser for the "delete" command under "titles"
parser_title_delete = titles_subparsers.add_parser('delete', help='delete titles')

# Create a parser for the "lectures" sub-command
parser_lecture = sub_parsers.add_parser('lecture', help='lectures sub-command')
lecture_subparsers = parser_lecture.add_subparsers(dest='lecture_command', help='lectures operation')

# Create a parser for the "create" command under "lecture"
parser_lecture_create = lecture_subparsers.add_parser('create', help='create lectures')

# Create a parser for the "delete" command under "lectures"
parser_lecture_delete = lecture_subparsers.add_parser('delete', help='delete lecturees')


# Parse the command line arguments
args = parser.parse_args()

# Process the arguments based on the command and sub-commands
if args.command == 'titles':
    if args.title_command == 'create':
        print("Enter Lecture ID: ")
        lecture_id = input()
        result = generate_topic_titles(lecture_id)
    elif args.title_command == 'delete':
        print("Enter Lecture ID: ")
        lecture_id = input()
        result = delete_topics_by_lecture(lecture_id)
        if not result:
            print("Failed to delete topic titles")
elif args.command == 'lecture':
    if args.lecture_command == 'create':
        print("Enter Course ID: ")
        course_id = input()
        print("Lecture Title: ")
        lecture_name = input()
        print("Lecture Transcription File: ")
        lecture_source = input()
        print("Lecture License: ")
        lecture_license = input()
        lecture_id = create_lecture(course_id,  lecture_name, lecture_license)

        if not lecture_id:
            print("Failed to create embedding for ", lecture_source )
            exit(1)
        result = create_embedding(lecture_source, lecture_id)
        if not result:
            print("Failed to create embedding")
            exit(1)
        result = generate_topic_titles(lecture_id)
        if not result:
            print("Failed to create topic titles")
    elif args.lecture_command == 'delete':
        print("Enter Lecture ID: ")
        lecture_id = input()
        result = delete_topics_by_lecture(lecture_id)
        if not result:
            print("Failed to delete topics by lecture")
        result = delete_lecture_by_id(lecture_id)
        if not result:
            print("Failed to delete lecture")
