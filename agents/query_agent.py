from langchain.agents import AgentExecutor
from langchain.agents.loading import AGENT_TO_CLASS
from langchain.agents.agent_types import AgentType
from langchain.memory import ConversationBufferMemory

from typing import TypedDict, Annotated, List, Union, Dict, Any
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.messages import BaseMessage

from langgraph.graph import END, StateGraph
from langgraph.prebuilt.tool_executor import ToolExecutor
import operator

from langchain.pydantic_v1 import BaseModel, Field
from langchain.tools import BaseTool
from langchain.tools import Tool

from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.agents.agent import AgentOutputParser
from langchain_core.exceptions import OutputParserException
import re
from langchain_openai import OpenAI, OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.vectorstores import VectorStoreRetriever

from .database import (
    create_tables, add_session,
    update_user_user_stats, 
    update_topic_summary,
    get_topic_title,
    get_topic_summary,
    insert_topic_quiz,
    get_topic_quiz)


class QueryAgentParser(AgentOutputParser):
    """Output parser for the conversational agent."""

    ai_prefix: str = "AI"
    """Prefix to use before AI output."""

    #format_instructions: str = FORMAT_INSTRUCTIONS
    #"""Default formatting instructions"""

    #def get_format_instructions(self) -> str:
    #    """Returns formatting instructions for the given output parser."""
    #    return self.format_instructions

    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        if f"{self.ai_prefix}:" in text or "Quiz" in text:
            return AgentFinish(
                {"output": text.split(f"{self.ai_prefix}:")[-1].strip()}, text
            )
        regex = r"Action: (.*?)[\n]*Action Input: ([\s\S]*)"
        match = re.search(regex, text, re.DOTALL)
        if not match:
            raise OutputParserException(f"Could not parse LLM output: `{text}`")
        action = match.group(1)
        action_input = match.group(2)
        return AgentAction(action.strip(), action_input.strip(" ").strip('"'), text)

    @property
    def _type(self) -> str:
        return "conversational"


class BaseRetrieverTool(BaseModel):
    """Base tool for interacting with a SQL database."""

    retriever: VectorStoreRetriever = Field(exclude=True)

    class Config(BaseTool.Config):
        pass

class TopicRetriever(BaseRetrieverTool, BaseTool):
    name = "GetTopic"
    description = "Useful to retrieve the topic context for the quiz."
    
    def _run(self, query):
        try:
            documents = self.retriever.invoke(query)
            if len(documents) > 0:
                document = documents[0].page_content
                return document
            else:
                return None
        except Exception as e:
            print("Failed to retrieve context")
            return None

    def _arun(self, query: str):
        raise NotImplementedError("This tool does not support async")



class AgentState(TypedDict):
    # The input string
    input: str
    # The list of previous messages in the conversation
    chat_history: list[BaseMessage]
    # The outcome of a given call to the agent
    # Needs `None` as a valid type, since this is what this will start as
    agent_outcome: Union[AgentAction, AgentFinish, None]
    # List of actions and corresponding observations
    # Here we annotate this with `operator.add` to indicate that operations to
    # this state should be ADDED to the existing values (not overwrite it)
    intermediate_steps: Annotated[list[tuple[AgentAction, str]], operator.add]



class QueryAgent():
    """
    A class that integrates various AI and retrieval tools to perform complex querying and information retrieval tasks.
    It uses embeddings and language models to extract and generate responses based on the input topics.
    """

    def __init__(self, rag_db, prompt_prefix, format_instructions, prompt_suffix):
        """
        Initializes the QueryAgent with specific settings for language models, embeddings, and retrieval systems.
        
        Args:
            rag_db (str): The name of the file containing embeddings for retrieval.
            prompt_prefix (str): Text to prepend to each model prompt.
            format_instructions (str): Instructions for formatting model outputs.
            prompt_suffix (str): Text to append to each model prompt.
        """

        # Initialize language model and embeddings.        
        #self.llm = ChatNVIDIA(model="mistralai/mixtral-8x22b-instruct-v0.1")
        #self.embedder = NVIDIAEmbeddings(model="ai-embed-qa-4")
        self.llm = ChatOpenAI(temperature=0.2, model="gpt-3.5-turbo-0125")
        self.embedder = OpenAIEmbeddings()

        # Load and set up the FAISS database for retrieval.
        self.faissDB = FAISS.load_local("./topic_embeddings/" + rag_db, self.embedder, allow_dangerous_deserialization=True)
        self.retriever = self.faissDB.as_retriever()

        # Configure retrieval and processing tools.
        self.topic_retriever = TopicRetriever(retriever=self.retriever)
        self.topic_tool=Tool.from_function(
            func = self.topic_retriever.invoke,
            name = "GetTopic",
            description="Set focus context for the topic")

        self.tools =[self.topic_tool]
        self.tool_executor = ToolExecutor(self.tools)

         # Set up agent execution with parsers and settings.
        agent_cls = AGENT_TO_CLASS[AgentType.CONVERSATIONAL_REACT_DESCRIPTION]
        agent_kwargs = {}
        agent_obj = agent_cls.from_llm_and_tools(
            self.llm, 
            [], #tools, 
            callback_manager=None,
            output_parser = QueryAgentParser(ai_prefix = "AI"),
            prefix = prompt_prefix,
            suffix = prompt_suffix,
            format_instructions = format_instructions, 
            **agent_kwargs)
        
        self.agent_execute = AgentExecutor.from_agent_and_tools(
            agent=agent_obj,
            tools=[], #tools,
            callback_manager=None,
            handle_parsing_errors=True,
            verbose=True,
            output_key = "output",
            max_iterations=3,
            return_intermediate_steps=True,
            # early_stopping_method="generate", # or use **force**
            memory = ConversationBufferMemory(memory_key="chat_history", input_key='input', output_key="output")
        )            

    def run_agent(self, state: AgentState):
        """
        Executes the main logic of the agent, handling and processing user input based on the agent's state.
        
        Args:
            state (AgentState): The current state of the agent including input and intermediate steps.
        
        Returns:
            dict: Outcome of the agent execution.
        """        
        inputs = state.copy()

        text = inputs['input']
        context = None
        intermediate_steps = inputs['intermediate_steps']
        if len(intermediate_steps) > 0:
            if isinstance (intermediate_steps[0][0], AgentAction):
                context = intermediate_steps[0][1]
        
        query = text if not context else text + "\n\n context:" + context

        agent_outcome = self.agent_execute.invoke({"input":query})
        return {"agent_outcome": agent_outcome}

    def first_agent(self, inputs):
        """
        Initiates the querying process by selecting and invoking the first relevant tool.
        
        Args:
            inputs (dict): Initial input parameters for the tool.
        
        Returns:
            dict: Initial action to be taken by the agent.
        """        
        action = AgentAction(
            # We force call this tool
            tool="GetTopic",
            # We just pass in the `input` key to this tool
            tool_input=inputs["input"],
            log="",
        )
        return {"agent_outcome": action}


    def should_continue(self, data):
        """
        Determines the flow of the agent's execution based on the outcome of the previous action.
        
        Args:
            data (dict): Data containing the outcome of the last agent action.
        
        Returns:
            str: Directive to either continue with further actions or end the workflow.
        """

        # If the agent outcome is an AgentFinish, then we return `exit` string
        # This will be used when setting up the graph to define the flow
        if data["agent_outcome"]["output"] is not None:
            print(" **AgentFinish** " )
            return "end"
        # Otherwise, an AgentAction is returned
        # Here we return `continue` string
        # This will be used when setting up the graph to define the flow
        else:
            return "continue"

    def execute_tools(self, data):
        """
        Executes tools based on the agent's state and action, compiling results into intermediate steps.
        
        Args:
            data (dict): Data containing the latest agent outcome.
        
        Returns:
            dict: Updated intermediate steps after tool execution.
        """        
        agent_action = data["agent_outcome"]
        output = self.tool_executor.invoke(agent_action)
        return {"intermediate_steps": [(agent_action, str(output))]}

    def setup_workflow(self):
        """
        Configures the workflow and state transitions for the agent operations, setting up the graph of execution nodes.
        """
        workflow = StateGraph(AgentState)
        workflow.add_node("first_agent", self.first_agent)
        workflow.add_node("agent", self.run_agent)
        #workflow.set_entry_point("agent")
        workflow.set_entry_point("first_agent")
        workflow.add_node("action", self.execute_tools)


        # We now add a conditional edge
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "continue": "action",
                "end": END,
            },
        )

        workflow.add_edge("action", "agent")
        workflow.add_edge("first_agent", "action")
        self.quizz_app = workflow.compile()


def parse_return(value: Union[Dict[str, Any], Any]):
    """
    Parses a return value, potentially containing nested data or error information, and extracts relevant content.

    Args:
        value (Union[Dict[str, Any], Any]): The value to be parsed, which may be a dictionary containing structured data or errors, or any other data type.

    Returns:
        Any: The extracted data if available, or None if extraction is not applicable.
    """    
    if isinstance(value, dict):
        # Check if the value is a dictionary and process it accordingly.
        if "error" in value:
            print(f"Error: {value['message']} (Code {value['code']})")
        else:
            # Extract and return the 'agent_outcome' data if present.
            if "agent_outcome" in value:
                data = value["agent_outcome"]["output"]
                return data
            else:
                print("Unexpected value:", value)
                
    else:
        # Print an error message if the expected key is not found.
        print("Returned value:", value)
        
def parse_quiz(llm_response):
    """
    Parses the quiz content from a language model's response into structured components.

    Args:
        llm_response (str): The raw text response from a language model, containing a summary, questions, choices, and answers.

    Returns:
        dict: A dictionary with keys 'summary', 'questions', 'choices', and 'answers', containing the parsed quiz components.
    
    This function processes the response through several steps:
    1. Extracts the summary.
    2. Identifies and extracts each quiz question along with its choices.
    3. Extracts the answer key for the questions.
    """
    # Use regex to find the summary section and strip unnecessary whitespace
    summary_match = re.search(r'Summary: (.*?)\n\nQuiz:', llm_response, re.DOTALL)
    summary = summary_match.group(1).strip() if summary_match else ""

    # Initialize lists for storing questions and choices, and a dictionary for answers.
    questions = []
    choices = []
    answers = {}

    # Use regex to locate and parse the answers, ensuring proper handling of formatting issues.
    quiz_pattern = re.compile(r'(\d+\.|-)\s+\[Question\s+\d+\s+-\s+\w+\]\s+(.+?)\n\s*([a-d]\)\s*.+?\n\s*[a-d]\)\s*.+?\n\s*[a-d]\)\s*.+?\n\s*[a-d]\)\s*.+?)(?=\s*(\d+\.|-)\s*|\s*Answers:)', re.DOTALL)
    quiz_matches = quiz_pattern.findall(llm_response)

    for q in quiz_matches:
        # Extract question and corresponding choices
        question_text = q[1].strip()
        choice_text = q[2].strip().split('\n')
        
        # Clean each choice, removing extra spaces before and after the choice identifier
        cleaned_choices = [choice.strip() for choice in choice_text if choice.strip()]
        questions.append(question_text)
        choices.append(cleaned_choices)

    # Updated to handle potential irregular whitespaces and line breaks within the JSON string
    answers_match = re.search(r'Answers:\s+({\s+"1":\s+"[a-d]",\s+"2":\s+"[a-d]",\s+"3":\s+"[a-d]"\s+})', llm_response, re.DOTALL)
    if answers_match:
        answers_dict = eval(answers_match.group(1))
        for key, value in answers_dict.items():
            answers[key] = value.strip()

    return {
        'summary': summary,
        'questions': questions,
        'choices': choices,
        'answers': answers
    }

def generate_quiz_and_cache(agent, topic_id):
    """
    Generates three quiz questions at basic, intermediate, and advanced levels for the given topic,
    and caches the quiz data including the questions, choices, and answers.

    This function retrieves the topic title using a provided topic ID, then uses a specified agent
    to generate quiz questions. It parses the output to extract questions, choices, answers, and a
    summary of the topic. It stores the quiz information in a database and updates the topic summary.

    Parameters:
    - agent (Agent): The agent object capable of invoking the quiz generation application.
    - topic_id (int): The ID of the topic for which the quiz is generated.

    Side Effects:
    - Inserts quiz data into a database using `insert_topic_quiz`.
    - Updates topic summary in the database using `update_topic_summary`.
    """

    # Retrieve the topic title using the topic ID.    
    topic = get_topic_title(topic_id)

    # Prepare the input data for the agent's quiz application.
    input_data = {"input": topic}

    # Invoke the quiz application to generate quiz questions.
    outputs = agent.quizz_app.invoke(input_data)

    # Parse the output from the quiz application to structured data.
    response = parse_return(outputs)
    quiz = parse_quiz(response)

    # Insert each question into the database along with its level, choices, and correct answer.
    # Also, update the topic summary for the given topic ID.
    for id, question in enumerate(quiz["questions"]):
        level=id
        choices = quiz["choices"][id]
        answer = quiz["answers"][str(id+1)]
        summary = quiz["summary"]
        insert_topic_quiz(topic_id, level, question, choices, answer)
        update_topic_summary(topic_id, summary)


def generate_conceptual_clarity(agent, topic_id):
    """
    Generates and retrieves responses for a given topic intended to clarify core concepts,
    using a specialized quiz application through an agent.

    This function first retrieves the title of the topic using its ID. It then constructs the input
    data for the agent's quiz application. The function invokes the quiz application with the
    topic title and processes the raw output to provide a structured response that includes
    potentially clarifying information or quiz questions on the topic.

    Parameters:
    - agent (Agent): The agent object capable of invoking the quiz generation application, expected
                     to handle the topic input and provide a relevant output.
    - topic_id (int): The ID of the topic for which the conceptual clarity is being generated.

    Returns:
    - dict: A structured dictionary containing the response from the quiz application, which could
            include quiz questions, clarifications, or other forms of educational content
            related to the topic.

    Examples of Usage:
    - This function can be used to generate pre-lecture quiz questions to assess and enhance
      students' understanding of a topic before a detailed discussion.
    """

    # Retrieve the topic title using the topic ID.
    topic = get_topic_title(topic_id)

     # Prepare the input data for the agent's quiz application.
    input_data = {"input": topic}

    # Invoke the quiz application to process the topic and generate relevant responses.
    outputs = agent.quizz_app.invoke(input_data)

    # Parse the output from the quiz application to structured data.
    response = parse_return(outputs)

    return response
