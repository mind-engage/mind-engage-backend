from enum import Enum

class LectureState(Enum):
    PENDING = "pending"
    INIT = "init"
    TRANSCRIPTION_FAILED = "transcription_failed"
    CREATE_EMBEDDING = "create_embedding"
    CREATE_EMBEDDING_FAILED = "create_embedding_failed"
    GENERATE_TOPIC_TITLES = "generate_topic_titles"
    GENERATE_TOPIC_TITLES_FAILED = "generate_topic_titles_failed"
    SUCCESS = "success"
    FAILED_TO_CREATE_LECTURE = "failed_to_create_lecture"