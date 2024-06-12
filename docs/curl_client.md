# Curl commands for  Quary Agent API
## Register a new session

```
curl -X POST http://localhost:8080/register
```
## Fetch lectures by course ID
```
curl -X GET "http://localhost:8080/lectures?session_id=<session_id>&course_id=<course_id>"
```
## Fetch topics by lecture ID
```
curl -X GET "http://localhost:8080/topics?session_id=<session_id>&lecture_id=<lecture_id>"
```
## Fetch quiz by topic ID
```
curl -X GET "http://localhost:8080/quiz?session_id=<session_id>&topic_id=<topic_id>&level=<level>"
```

# Get conceptual clarity on a topic

```
curl -X GET "http://localhost:8080/conceptual_clarity?session_id=<session_id>&topic_id=<topic_id>&level=<level>&answer=<answer>"
```

## Submit answer
```
curl -X POST http://localhost:8080/submit_answer -H "Content-Type: application/json" -d '{"session_id": "<session_id>", "topic_id": "<topic_id", "level": 1, "answer": "answer"}'

```

# Curl commands for  Course Agent API

Sure, here are the cURL commands in single-line format for each of the API endpoints you provided:

## Creating Titles
```bash
curl -X POST http://localhost:5000/titles/create -H "Content-Type: application/json" -d '{"lecture_id": "1"}'
```

## Deleting Titles
```bash
curl -X DELETE http://localhost:5000/titles/delete -H "Content-Type: application/json" -d '{"lecture_id": "1"}'
```

## Creating a Lecture
```bash
curl -X POST http://localhost:5000/lecture/create -H "Content-Type: application/json" -d '{"course_id": "101", "lecture_name": "Introduction to AI", "lecture_source": "source_file.txt", "lecture_license": "CC BY-SA"}'
```

## Deleting a Lecture
```bash
curl -X DELETE http://localhost:5000/lecture/delete -H "Content-Type: application/json" -d '{"lecture_id": "1"}'
```
