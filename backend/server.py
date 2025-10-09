# server.py

import os
import re
import json
import logging
import uuid
import tempfile
from functools import lru_cache
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# LangChain Imports
from langchain.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import Document
from langchain_community.llms import LlamaCpp

# Local utility imports
from ingest_pdf import ingest_documents_to_chroma
from ingest_errors import ingest_json_to_chroma

# --- Configuration and Setup ---

# Define the model path and vector store collection names
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "mistral-7b-instruct-v0.2.Q4_K_M.gguf")
BANKING_COLLECTION_NAME = "banking_docs"
ERROR_COLLECTION_NAME = "error_docs"
CHROMA_PERSIST_DIR = "chroma_db"
SESSION_STATE_FILE = "session_state.json"

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- Pydantic Schemas ---

class ChatRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatHistory(BaseModel):
    session_id: str
    name: str
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    session_id: str
    answer: str
    history: List[Dict[str, str]]

# --- Core Component Initialization ---

# 1. Embeddings
try:
    EMBEDDINGS = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    logger.info("HuggingFaceEmbeddings loaded successfully.")
except Exception as e:
    logger.error(f"Error loading embeddings: {e}")
    EMBEDDINGS = None

# 2. Vector Stores (Initialized in `load_vector_stores`)
BANKING_VECTORSTORE: Optional[Chroma] = None
ERROR_VECTORSTORE: Optional[Chroma] = None

def load_vector_stores():
    """Initializes and reloads the Chroma vector stores."""
    global BANKING_VECTORSTORE, ERROR_VECTORSTORE
    if not EMBEDDINGS:
        logger.error("Embeddings not loaded. Cannot initialize vector stores.")
        return

    try:
        BANKING_VECTORSTORE = Chroma(
            collection_name=BANKING_COLLECTION_NAME,
            embedding_function=EMBEDDINGS,
            persist_directory=CHROMA_PERSIST_DIR
        )
        ERROR_VECTORSTORE = Chroma(
            collection_name=ERROR_COLLECTION_NAME,
            embedding_function=EMBEDDINGS,
            persist_directory=CHROMA_PERSIST_DIR
        )
        logger.info("ChromaDB vector stores loaded/reloaded.")
    except Exception as e:
        logger.error(f"Error loading ChromaDB: {e}")

# Load vector stores on startup
load_vector_stores()

# 3. LLM (LlamaCpp)
@lru_cache(maxsize=1)
def get_llm():
    """Returns a cached instance of the LlamaCpp LLM."""
    if not os.path.exists(MODEL_PATH):
        logger.error(f"LLM model not found at {MODEL_PATH}. Please download it.")
        raise FileNotFoundError(f"LLM model not found at {MODEL_PATH}")

    return LlamaCpp(
        model_path=MODEL_PATH,
        temperature=0.1,
        max_tokens=512,
        n_ctx=2048,
        n_gpu_layers=30, # Adjust based on your GPU
        verbose=False,
    )

# 4. Prompt Templates
# Templating with {context} for RAG, {history} for chat history, and {question} for user input.

BASE_TEMPLATE = """
[INST] You are a highly professional, secure, and concise banking assistant.
Your goal is to provide factual, helpful answers based *only* on the provided context.
If the question is outside the context, state clearly that you cannot answer.
Always maintain a helpful and professional tone.
If the user provides any Personal Identifiable Information (PII), **immediately stop** and respond with the PII safety message.

Chat History:
{history}

Context:
{context}

Question:
{question}
[/INST]
"""

SUPPORT_TEMPLATE = """
[INST] You are a specialized banking system support assistant.
Your goal is to provide clear, step-by-step instructions and solutions for the given error or issue based *only* on the provided context.
If the context does not contain a solution, state that you do not have information for that specific error.

Chat History:
{history}

Context:
{context}

Question (Error/Issue):
{question}
[/INST]
"""

CHIT_CHAT_TEMPLATE = """
[INST] You are a friendly, but brief, assistant. Your response should be short, natural, and helpful.
Do not provide any banking or technical advice. If the user asks a substantive question, gently redirect them to ask a specific banking question.

Chat History:
{history}

Question:
{question}
[/INST]
"""

PII_SAFETY_RESPONSE = "I cannot process or store any Personal Identifiable Information (PII) like SSNs, account numbers, or passwords. Please rephrase your question without including sensitive details. For account-specific inquiries, please contact a live agent."

# --- Session Management ---

def load_sessions() -> Dict[str, ChatHistory]:
    """Loads chat history from the JSON file."""
    if not os.path.exists(SESSION_STATE_FILE):
        return {}
    try:
        with open(SESSION_STATE_FILE, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError:
        logger.warning("session_state.json is empty or invalid, starting fresh.")
        return {}
    # Convert raw data back to ChatHistory objects
    sessions = {}
    for session_id, history_data in data.items():
        try:
            sessions[session_id] = ChatHistory(**history_data)
        except Exception as e:
            logger.error(f"Error loading session {session_id}: {e}")
    return sessions

def save_sessions(sessions: Dict[str, ChatHistory]):
    """Saves chat history to the JSON file."""
    # Convert ChatHistory objects to serializable dictionary
    serializable_sessions = {k: v.dict() for k, v in sessions.items()}
    with open(SESSION_STATE_FILE, 'w') as f:
        json.dump(serializable_sessions, f, indent=4)

SESSIONS: Dict[str, ChatHistory] = load_sessions()

def get_chat_history_string(session_id: str) -> str:
    """Formats the chat history for the LLM prompt."""
    if session_id not in SESSIONS:
        return "No prior conversation."

    history_str = []
    for msg in SESSIONS[session_id].messages:
        role = "Human" if msg.role == "user" else "Assistant"
        history_str.append(f"{role}: {msg.content}")

    # Limit history to last 5 exchanges to save context window space
    return "\n".join(history_str[-10:])

def update_chat_history(session_id: str, user_msg: str, ai_msg: str, new_session: bool = False) -> List[Dict[str, str]]:
    """Adds new messages to the session and returns the updated history list."""
    if session_id not in SESSIONS:
        session_name = user_msg[:30].strip() or "New Chat"
        SESSIONS[session_id] = ChatHistory(
            session_id=session_id,
            name=session_name,
            messages=[]
        )

    SESSIONS[session_id].messages.append(ChatMessage(role="user", content=user_msg))
    SESSIONS[session_id].messages.append(ChatMessage(role="assistant", content=ai_msg))

    save_sessions(SESSIONS)

    return [{"role": m.role, "content": m.content} for m in SESSIONS[session_id].messages]

def check_for_pii(text: str) -> bool:
    """Detects common PII patterns: SSN, long digit sequences (credit cards, account numbers)."""
    # 1. SSN pattern: XXX-XX-XXXX or XXXXXXXXX (9 digits)
    ssn_pattern = r'\b\d{3}[- ]?\d{2}[- ]?\d{4}\b'
    if re.search(ssn_pattern, text):
        logger.warning("PII detected (SSN pattern).")
        return True

    # 2. Long digit sequence (e.g., credit card number 12-16 digits)
    long_digit_pattern = r'\b\d{12,16}\b'
    if re.search(long_digit_pattern, text.replace(' ', '')):
        logger.warning("PII detected (long digit sequence).")
        return True

    return False

def determine_prompt(question: str) -> str:
    """Analyzes the question to select the most appropriate prompt template."""
    q_lower = question.lower()
    
    # 1. Error/Support check
    error_keywords = ["error", "issue", "bug", "fix", "troubleshoot", "failed to log", "cannot connect"]
    if any(k in q_lower for k in error_keywords):
        return "support"

    # 2. Chit-chat check (short, non-substantive questions)
    chit_chat_keywords = ["hello", "hi", "how are you", "what is your name", "thanks", "thank you", "bye"]
    if len(question.split()) < 4 or any(q_lower == k for k in chit_chat_keywords):
        return "chit_chat"

    # 3. Default to Banking prompt
    return "banking"

# --- FastAPI App Initialization ---

app = FastAPI(
    title="Banking Chatbot API",
    description="Full-stack banking assistant powered by a local Mistral LLM and ChromaDB RAG."
)

# CORS Middleware Setup (Essential for frontend communication)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- API Endpoints ---

@app.get("/sessions", response_model=List[ChatHistory])
def get_all_sessions():
    """Retrieves a list of all current chat sessions for the sidebar."""
    # Convert the dictionary values to a list of ChatHistory objects
    return list(SESSIONS.values())

@app.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """Handles the question-answering logic with PII check and RAG."""
    question = request.question.strip()
    session_id = request.session_id or str(uuid.uuid4())
    
    # 1. PII Detection
    if check_for_pii(question):
        ai_response = PII_SAFETY_RESPONSE
        updated_history = update_chat_history(session_id, question, ai_response)
        return ChatResponse(session_id=session_id, answer=ai_response, history=updated_history)
        
    try:
        llm = get_llm()
    except FileNotFoundError as e:
        logger.error(str(e))
        raise HTTPException(status_code=503, detail="LLM Model not available on the server.")
    except Exception as e:
        logger.error(f"Error initializing LLM: {e}")
        raise HTTPException(status_code=500, detail="Internal server error with LLM initialization.")

    # 2. Determine Prompt and Template
    prompt_type = determine_prompt(question)
    current_history_str = get_chat_history_string(session_id)
    
    if prompt_type == "banking":
        template = BASE_TEMPLATE
        vectorstore = BANKING_VECTORSTORE
    elif prompt_type == "support":
        template = SUPPORT_TEMPLATE
        vectorstore = ERROR_VECTORSTORE
    else: # chit_chat
        template = CHIT_CHAT_TEMPLATE
        vectorstore = None

    # 3. RAG and Invocation
    context = "No specific banking context available."
    if vectorstore:
        # Retrieve relevant documents
        docs = vectorstore.similarity_search(question, k=4)
        context = "\n---\n".join([doc.page_content for doc in docs])

    full_prompt = PromptTemplate.from_template(template).format(
        history=current_history_str,
        context=context,
        question=question
    )

    try:
        # LLM Invocation
        ai_response = llm.invoke(full_prompt).strip()
    except Exception as e:
        logger.error(f"LLM invocation failed: {e}")
        ai_response = "An error occurred while generating the response. Please try again or rephrase your question."

    # 4. History Update and Response
    updated_history = update_chat_history(session_id, question, ai_response)
    
    return ChatResponse(session_id=session_id, answer=ai_response, history=updated_history)

@app.post("/upload-pdfs")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """Accepts and processes PDF, Excel, and Word files, ingesting them into the banking_docs vector store."""
    if not BANKING_VECTORSTORE:
        raise HTTPException(status_code=503, detail="Vector store not initialized.")

    logger.info(f"Received {len(files)} files for banking document ingestion.")

    temp_dir = tempfile.mkdtemp()
    filepaths = []
    try:
        for file in files:
            # Save file temporarily
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in ['.pdf', '.xls', '.xlsx', '.doc', '.docx']:
                logger.warning(f"Skipping unsupported file: {file.filename}")
                continue

            temp_path = os.path.join(temp_dir, file.filename)
            with open(temp_path, "wb") as f:
                f.write(await file.read())
            filepaths.append(temp_path)

        if not filepaths:
            return {"message": "No valid files were uploaded."}

        # Ingest into ChromaDB
        ingest_documents_to_chroma(filepaths, BANKING_VECTORSTORE)
        load_vector_stores() # Reload to ensure the store is ready for queries

        return {"message": f"Successfully processed and ingested {len(filepaths)} document(s) into 'banking_docs'. Vector store reloaded."}

    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {str(e)}")
    finally:
        # Clean up temporary files and directory
        for f in filepaths:
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)


@app.post("/upload-errors")
async def upload_errors(files: List[UploadFile] = File(...)):
    """Accepts and processes JSON error files, ingesting them into the error_docs vector store."""
    if not ERROR_VECTORSTORE:
        raise HTTPException(status_code=503, detail="Vector store not initialized.")

    logger.info(f"Received {len(files)} JSON files for error ingestion.")
    
    temp_dir = tempfile.mkdtemp()
    filepaths = []
    try:
        for file in files:
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension != '.json':
                logger.warning(f"Skipping non-JSON file: {file.filename}")
                continue
                
            temp_path = os.path.join(temp_dir, file.filename)
            with open(temp_path, "wb") as f:
                f.write(await file.read())
            filepaths.append(temp_path)

        if not filepaths:
            return {"message": "No valid JSON files were uploaded."}

        # Ingest into ChromaDB
        ingest_json_to_chroma(filepaths, ERROR_VECTORSTORE)
        load_vector_stores() # Reload to ensure the store is ready for queries

        return {"message": f"Successfully processed and ingested {len(filepaths)} JSON error documents into 'error_docs'. Vector store reloaded."}

    except Exception as e:
        logger.error(f"JSON upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"JSON ingestion failed: {str(e)}")
    finally:
        # Clean up temporary files and directory
        for f in filepaths:
            if os.path.exists(f):
                os.remove(f)
        if os.path.exists(temp_dir):
            os.rmdir(temp_dir)

@app.get("/")
def read_root():
    return {"message": "Banking Chatbot API is running."}

# Startup hook to check for model
@app.on_event("startup")
def startup_event():
    try:
        # Pre-check LLM availability
        get_llm()
    except FileNotFoundError:
        logger.error("LLM model file not found. System will run, but /ask endpoint will fail.")
    except Exception as e:
        logger.error(f"Error on LLM startup: {e}")