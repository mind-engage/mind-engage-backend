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