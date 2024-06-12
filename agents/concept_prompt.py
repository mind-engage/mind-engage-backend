# Concept Clarity and Socratic Exploration Prompt
PREFIX = """
Assistant is a large language model designed to assist in the comprehension of complex topics by creating educational materials. Using the provided summary and context.

Please help me understand the concept of {concept}, which relates to a multiple-choice question I encountered. 
The question was: {question}
The options were: 
A) {option_a}
B) {option_b}
C) {option_c}
D) {option_d}
I chose {your_choice}, but it was incorrect. Can you explain why the correct answer is the right one and why the other options are not suitable? Additionally, can you provide a detailed explaination to help me explore the concept further?
"""

SUFFIX = """Begin! Previous conversation history: {chat_history} New input: {input} {agent_scratchpad}"""

FORMAT_INSTRUCTIONS = """Prefix your response as follows ```{ai_prefix}: [your response here] ```"""


def get_formatted(prompt_template, topic_summary, quiz_dict, answer):
    user_answer = ""
    num_answer = ord(answer.lower()) - ord('a'); 
    if num_answer >= 0 and num_answer < 4:
        user_answer = quiz_dict["choices"][num_answer]
        
    concept_prompt = prompt_template.format(
        concept=topic_summary,
        question=quiz_dict["question"],
        option_a=quiz_dict["choices"][0],
        option_b=quiz_dict["choices"][1],
        option_c=quiz_dict["choices"][2],
        option_d=quiz_dict["choices"][3],
        your_choice=user_answer
    )
    return concept_prompt