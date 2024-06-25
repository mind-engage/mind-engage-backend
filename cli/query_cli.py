import uuid
import pandas as pd

from agents.database  import (
    get_topic_quiz,
    get_topic_summary,
    get_db_connection,
    fetch_lectures_by_course,
    fetch_topics_by_lecture
)

from agents.query_agent import (
    QueryAgent, 
    parse_return, 
    generate_quiz_and_cache, 
    generate_conceptual_clarity)
    
import agents.quiz_prompt
import agents.concept_prompt


def display_lectures(lectures):
    print(f"{'Lecture ID':<12}{'Lecture Title':<30}")  # Header with column titles
    print("-" * 42)  # Separator line
    for lecture_id, lecture_title, license in lectures:
        print(f"{lecture_id:<12}{lecture_title:<30}{license:<256}")

def display_topics(topics):
    print(f"{'Topic ID':<10}{'Topic Title':<30}")  # Header with column titles
    print("-" * 40)  # Separator line
    for topic_id, topic_title in topics:
        print(f"{topic_id:<10}{topic_title:<30}")

if __name__ == '__main__':
    # Step-1 User => Requests learing session, Agent => generates session_id
    session_id = str(uuid.uuid4())

    # Step-2 User => Requests available lectures, Agent => sends list of lectures
    # Course is hard coded for now
    course_id =  str(uuid.UUID(int=0))

    lectures = fetch_lectures_by_course(course_id)
    display_lectures(lectures)
    lecture_id = input("Enter a lecture ID to fetch topics: ")    
 
    # Step-3 User => Selects a lecture_id and requests available topics, Agent => sends list of topics for the lectures
    topics = fetch_topics_by_lecture(lecture_id)
    display_topics(topics)

    # Step-4 User => Selects a topic_id, 
    topic_id = input("Enter a topic ID to fetch the title: ")

    #    Agent checks if session_id exists
    #      if session exists, retrieves quiz for the first failed question and send the quiz 

    # Step-6 Agent: sends quiz-basic on the topic

    quiz_dict = get_topic_quiz(topic_id, level=0)
    if not quiz_dict:
        rag_db = lecture_id
        query_agent = QueryAgent(rag_db, quiz_prompt.PREFIX, quiz_prompt.FORMAT_INSTRUCTIONS, quiz_prompt.SUFFIX)
        query_agent.setup_workflow()
        generate_quiz_and_cache(query_agent, topic_id)

    for level in range(3):
        quiz_dict = get_topic_quiz(topic_id, level)
        if(quiz_dict):
            topic_summary = get_topic_summary(topic_id)
            answer = quiz_dict["answer"]
            if topic_summary: print(f"Summary:  {topic_summary}\n")
            print(quiz_dict["question"])
            for choice in quiz_dict["choices"]:
                print(choice)

            print("Enter Answer")
            user_answer = input()
            if user_answer == answer:
                print("Correct!")
            else:
                print("Answer is Wrong! Look at the following for clarity.")
                # Get concept
                rag_db = lecture_id
                prompt_prefix = concept_prompt.get_formatted(concept_prompt.PREFIX, topic_summary, quiz_dict, answer)
                concept_agent = QueryAgent(rag_db, prompt_prefix, concept_prompt.FORMAT_INSTRUCTIONS, concept_prompt.SUFFIX)
                concept_agent.setup_workflow()
                # Quick check
                concept = generate_conceptual_clarity(concept_agent, topic_id)
                print(concept)
                input("Press Enter to continue...")

