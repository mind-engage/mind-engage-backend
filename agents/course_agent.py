from langchain_community.vectorstores import FAISS
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_openai import OpenAI, OpenAIEmbeddings
from langchain_openai import ChatOpenAI
import os
from agents.database import (
    insert_course,
    insert_lecture,
    insert_topic,
    get_course_id,
    get_lecture_id)

TOPIC_TITLE_PROMPT = "Give a short topic title for the following. It should not exceed 8 words. Only one title in the response:"

# Models and params for NVidia NIM
# TOPIC_SIZE=1000
# embedder = NVIDIAEmbeddings(model="ai-embed-qa-4")
# llm = ChatNVIDIA(model="mistralai/mixtral-8x22b-instruct-v0.1")

TOPIC_SIZE=3000
embedder = OpenAIEmbeddings()
llm = ChatOpenAI(temperature=0, model="gpt-3.5-turbo-0125")

def create_embedding(topic_source_file: str, lecture_id: str):
    """
    Creates a text embedding for a specified topic document and saves the embedding.

    This function processes a topic document by loading it, splitting it into
    manageable chunks, and embedding these chunks using FAISS. The resulting
    embeddings are then saved to disk. This process is only needed once unless
    the document or the embedding process changes.

    Parameters:
    - topic_source_file (str): The name of the file containing the topic document. This
      file should be located within the './topic_docs/' directory.
    - topic_embedding_name (str): The name for the saved embedding file. This file will
      be stored within the './topic_embeddings/' directory.

    Returns:
    - bool: True if the embedding process completes successfully, False otherwise.

    Raises:
    - Exception: Propagates any exceptions that occur during the process, typically
      from file handling or data processing errors.
    """    
    try:
        data = []
        sources = []
        path2file = topic_source_file
        loader = TextLoader(path2file)
        document = loader.load()

        # create docs and metadatas
        text_splitter = CharacterTextSplitter(chunk_size=TOPIC_SIZE, separator=".", keep_separator=True, chunk_overlap=0)
        docs = text_splitter.split_documents(document)

        # you only need to do this once, in the future, when re-run this notebook, skip to below and load the vector store from disk
        store = FAISS.from_documents(docs, embedder )
        rag_db_folder = os.environ.get("RAG_DB_FOLDER", "./topic_embeddings/")
        store.save_local(rag_db_folder + lecture_id)
        return True
    except Exception as e:
        raise Exception(e)
        return False

def generate_topic_titles(lecture_id):
    """
    Generates a list of titles for topics based on their embeddings.

    This function loads a pre-existing FAISS database of topic embeddings and uses it to
    retrieve documents. For each document, it constructs a title using a language model
    based on the content of the document.

    Parameters:
    - topic_embedding_name (str): The name of the embedding file to load. This file
      is expected to be in the './topic_embeddings/' directory.

    Returns:
    - list of str: A list of titles generated for each topic in the embedding database.

    Raises:
    - Exception: Propagates any exceptions that occur, typically related to file access,
      FAISS database operations, or language model invocation errors.
    """    
    try:
      rag_db_folder = os.environ.get("RAG_DB_FOLDER", "./topic_embeddings/")
      faissDB = FAISS.load_local(rag_db_folder + lecture_id, embedder, allow_dangerous_deserialization=True)
      retriever = faissDB.as_retriever()
      titles = []
      for i, doc_id in  faissDB.index_to_docstore_id.items():
          document = faissDB.docstore.search(doc_id)
          response = llm.invoke(TOPIC_TITLE_PROMPT + document.page_content)
          titles.append(response.content)
      for title in titles:
          insert_topic(lecture_id, title)
      return True
    except Exception as e:
      raise Exception(e)
      return False


