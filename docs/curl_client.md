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

## Upload a file and create a lecture:
```
curl -X POST http://localhost:5000/lecture/create \
  -H "Content-Type: multipart/form-data" \
  -F "file=@/path/to/your/file.txt" \
  -F "title=Sample Lecture Title" \
  -F "description=Sample Lecture Description" \
  -F "license=Creative Commons - Attribution"

```

## Check the status of the lecture creation process:
```
curl -X GET http://localhost:5000/lecture/status/<lecture_id>
```

## Deleting a Lecture
```bash
curl -X DELETE http://localhost:5000/lecture/delete -H "Content-Type: application/json" -d '{"lecture_id": <lecture_id>}'
```

## Creating Titles
```bash
curl -X POST http://localhost:5000/titles/create -H "Content-Type: application/json" -d '{"lecture_id": <lecture_id>}'
```

## Deleting Titles
```bash
curl -X DELETE http://localhost:5000/titles/delete -H "Content-Type: application/json" -d '{"lecture_id": <lecture_id>}'
```

