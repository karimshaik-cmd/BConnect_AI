

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
from .ingest_pdf import ingest_documents_to_chroma
from .ingest_errors import ingest_json_to_chroma
from .chat_engine import ChatEngine

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
    user_type: str

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatHistory(BaseModel):
    session_id: str
    user_type: str
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

# 3. EmbeddingManager for ChatEngine compatibility
class EmbeddingManager:
    """Wrapper class to provide ChatEngine-compatible interface for Chroma vectorstores"""

    def __init__(self, banking_vectorstore: Chroma, error_vectorstore: Chroma):
        self.banking_vectorstore = banking_vectorstore
        self.error_vectorstore = error_vectorstore

    def search_similar(self, query: str, top_k: int = 5, collection: str = "banking") -> List[Dict[str, Any]]:
        """Search similar documents in the specified collection"""
        vectorstore = self.banking_vectorstore if collection == "banking" else self.error_vectorstore
        if not vectorstore:
            return []

        docs = vectorstore.similarity_search(query, k=top_k)
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": 1.0  # Chroma doesn't provide scores directly
            }
            for doc in docs
        ]

    def has_documents(self) -> bool:
        """Check if documents are loaded"""
        return (self.banking_vectorstore is not None and
                self.error_vectorstore is not None)

    def get_stats(self) -> Dict[str, Any]:
        """Get document statistics"""
        banking_count = len(self.banking_vectorstore.get()) if self.banking_vectorstore else 0
        error_count = len(self.error_vectorstore.get()) if self.error_vectorstore else 0
        return {
            "documents": banking_count + error_count,
            "chunks": banking_count + error_count,
            "file_types": {"banking": banking_count, "error": error_count}
        }

    def get_recent_sources(self) -> List[str]:
        """Get recent document sources"""
        sources = []
        if self.banking_vectorstore:
            try:
                docs = self.banking_vectorstore.get()
                sources.extend(list(set(doc.get('source', '') for doc in docs['metadatas'] if doc.get('source'))))
            except:
                pass
        if self.error_vectorstore:
            try:
                docs = self.error_vectorstore.get()
                sources.extend(list(set(doc.get('source', '') for doc in docs['metadatas'] if doc.get('source'))))
            except:
                pass
        return list(set(sources))

    def clear_documents(self):
        """Clear all documents - placeholder for future implementation"""
        pass

# Initialize EmbeddingManager and ChatEngine
EMBEDDING_MANAGER = EmbeddingManager(BANKING_VECTORSTORE, ERROR_VECTORSTORE) if BANKING_VECTORSTORE and ERROR_VECTORSTORE else None
CHAT_ENGINE = ChatEngine(embedding_manager=EMBEDDING_MANAGER) if EMBEDDING_MANAGER else None

# 4. LLM (LlamaCpp)
@lru_cache(maxsize=1)
def get_llm():
    """Returns a cached instance of the LlamaCpp LLM."""
    if not os.path.exists(MODEL_PATH):
        logger.error(f"LLM model not found at {MODEL_PATH}. Please download it.")
        raise FileNotFoundError(f"LLM model not found at {MODEL_PATH}")

    return LlamaCpp(
        model_path=MODEL_PATH,
        temperature=0.1,
        max_tokens=256,
        n_ctx=4096,
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

EXCEL_TEMPLATE = """
[[INST]
You are a structured API specification assistant. Your job is to extract mandatory field requirements for API objects based **only** on the tabular context provided below.

**CRITICAL INSTRUCTIONS:**
1.  **NEVER REFUSE:** You **must** generate a table of required fields. If no fields are found, you must state: "No required fields found for the specified object in the uploaded document." Do not generate generic refusals like "I don't have access to the documentation."
2.  **DATA SOURCE:** Your only source of information is the 'Context' section.
3.  **EXTRACTION LOGIC:**
    * **Goal:** Find all fields related to the user's query (e.g., 'reqMerchantOnboard').
    * **Filter 1:** Include only rows where the 'Required/ Optional' column contains the value 'Required'.
    * **Filter 2:** Include rows where the 'Required/ Optional' column contains the value 'Conditional'.
    * **Field Path:** The full hierarchical field path (e.g., 'Head.ver' or 'Merchant.Address.city') is available in the 'Field Path' and 'Level X' columns of the context. Construct the Field Path using the components separated by a dot (.).

**OUTPUT FORMAT:**

**A. REQUIRED FIELDS**
Create a Markdown table for all fields marked 'Required'.
| Field Path | Type | Comments |
| :--- | :--- | :--- |

**B. CONDITIONAL FIELDS**
Create a separate Markdown table for all fields marked 'Conditional'.
| Field Path | Type | Condition |
| :--- | :--- | :--- |

Chat History:
{history}

Context (Excel Extract - Tabular data for RAG):
{context}

User Question:
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
        # Backward compatibility: add user_type if missing
        history_data.setdefault('user_type', 'admin')  # Default for existing sessions
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

def update_chat_history(session_id: str, user_type: str, user_msg: str, ai_msg: str, new_session: bool = False) -> List[Dict[str, str]]:
    """Adds new messages to the session and returns the updated history list."""
    if session_id not in SESSIONS:
        session_name = user_msg[:30].strip() or "New Chat"
        SESSIONS[session_id] = ChatHistory(
            session_id=session_id,
            user_type=user_type,
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
    q = question.lower()
    if any(k in q for k in ["error", "issue", "bug", "fix", "troubleshoot", "failed to log", "cannot connect"]):
        return "support"
    if any(k in q for k in ["excel", "field", "required", "optional", "regex", "datatype", "api"]):
        return "excel"
    if len(q.split()) < 4 or any(q in x for x in ["hi", "hello", "thanks", "bye", "thank you"]):
        return "chit_chat"
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
def get_all_sessions(user_type: str):
    """Retrieves a list of all current chat sessions for the sidebar."""
    # Convert the dictionary values to a list of ChatHistory objects
    return [s for s in SESSIONS.values() if s.user_type == user_type]

@app.delete("/sessions/{session_id}")
def delete_session(session_id: str):
    """Deletes a specific chat session."""
    if session_id not in SESSIONS:
        raise HTTPException(status_code=404, detail="Session not found")
    del SESSIONS[session_id]
    save_sessions(SESSIONS)
    return {"message": f"Session {session_id} deleted successfully"}

@app.post("/ask", response_model=ChatResponse)
async def ask_question(request: ChatRequest):
    """Handles the question-answering logic with PII check and RAG using ChatEngine."""
    question = request.question.strip()
    session_id = request.session_id or str(uuid.uuid4())

    # 1. PII Detection
    if check_for_pii(question):
        ai_response = PII_SAFETY_RESPONSE
        updated_history = update_chat_history(session_id, request.user_type, question, ai_response)
        return ChatResponse(session_id=session_id, answer=ai_response, history=updated_history)

    # 2. Check if ChatEngine is available, fallback to LLM if not
    if not CHAT_ENGINE:
        logger.warning("ChatEngine not initialized, falling back to local LLM")
        try:
            llm = get_llm()
        except FileNotFoundError as e:
            logger.error(str(e))
            raise HTTPException(status_code=503, detail="LLM Model not available on the server.")
        except Exception as e:
            logger.error(f"Error initializing LLM: {e}")
            raise HTTPException(status_code=500, detail="Internal server error with LLM initialization.")

        # Fallback logic using original templates
        prompt_type = determine_prompt(question)
        current_history_str = get_chat_history_string(session_id)

        if prompt_type == "banking":
            template = BASE_TEMPLATE
            vectorstore = BANKING_VECTORSTORE
        elif prompt_type == "support":
            template = SUPPORT_TEMPLATE
            vectorstore = ERROR_VECTORSTORE
        elif prompt_type == "excel":
            template = EXCEL_TEMPLATE
            vectorstore = BANKING_VECTORSTORE
        else:  # chit_chat
            template = CHIT_CHAT_TEMPLATE
            vectorstore = None

        context = "No relevant context found."
        if vectorstore:
            search_term = re.findall(r"(resp|req)\w+", question, re.IGNORECASE)
            search_text = search_term[0] if search_term else question
            docs = vectorstore.similarity_search(search_text, k=5)
            if not docs:
                docs = vectorstore.similarity_search(question, k=5)

            logger.info(f"🔍 Retrieved {len(docs)} docs for query: '{question}'")
            if docs:
                context = "\n\n--- DOCUMENT CONTEXT START ---\n\n".join([doc.page_content for doc in docs])

        full_prompt = PromptTemplate.from_template(template).format(
            history=current_history_str,
            context=context,
            question=question
        )

        try:
            ai_response = llm.invoke(full_prompt).strip()
        except Exception as e:
            logger.error(f"❌ LLM invocation failed: {e}")
            ai_response = "An internal error occurred while generating the response."
    else:
        # 3. Use ChatEngine for enhanced processing
        logger.info("Using ChatEngine for query processing")

        # Get conversation history for ChatEngine
        conversation_history = []
        if session_id in SESSIONS:
            # Convert to format expected by ChatEngine
            for msg in SESSIONS[session_id].messages[-6:]:  # Last 3 exchanges
                conversation_history.append({
                    "role": msg.role,
                    "content": msg.content
                })

        # Determine vectorstore for RAG context
        prompt_type = determine_prompt(question)
        if prompt_type == "banking":
            vectorstore = BANKING_VECTORSTORE
            collection = "banking"
        elif prompt_type == "support":
            vectorstore = ERROR_VECTORSTORE
            collection = "error"
        elif prompt_type == "excel":
            vectorstore = BANKING_VECTORSTORE
            collection = "banking"
        else:  # chit_chat
            vectorstore = None
            collection = "banking"

        # Get RAG context
        context = ""
        if vectorstore:
            search_term = re.findall(r"(resp|req)\w+", question, re.IGNORECASE)
            search_text = search_term[0] if search_term else question
            docs = vectorstore.similarity_search(search_text, k=5)
            if not docs:
                docs = vectorstore.similarity_search(question, k=5)

            logger.info(f"🔍 Retrieved {len(docs)} docs for query: '{question}'")
            if docs:
                context = "\n\n--- DOCUMENT CONTEXT START ---\n\n".join([doc.page_content for doc in docs])

        # Generate response using ChatEngine
        try:
            ai_response = CHAT_ENGINE.generate_response(
                query=question,
                context=context,
                conversation_history=conversation_history
            )
        except Exception as e:
            logger.error(f"❌ ChatEngine generation failed: {e}")
            ai_response = "An internal error occurred while generating the response."

    # 4. History Update and Response
    updated_history = update_chat_history(session_id, request.user_type, question, ai_response)

    return ChatResponse(session_id=session_id, answer=ai_response, history=updated_history)

@app.post("/upload-pdfs")
async def upload_pdfs(files: List[UploadFile] = File(...)):
    """Accepts and processes PDF, Excel, Word, CSV, and TXT files, ingesting them into the banking_docs vector store."""
    if not BANKING_VECTORSTORE:
        raise HTTPException(status_code=503, detail="Vector store not initialized.")

    logger.info(f"Received {len(files)} files for banking document ingestion.")

    temp_dir = tempfile.mkdtemp()
    filepaths = []
    try:
        for file in files:
            # Save file temporarily
            file_extension = os.path.splitext(file.filename)[1].lower()
            if file_extension not in ['.pdf', '.xls', '.xlsx', '.doc', '.docx', '.csv', '.txt', '.json']:
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

@app.post("/upload-documents")
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Accepts and processes PDF, Excel, Word, CSV, or TXT files,
    ingesting them into the banking_docs vector store dynamically.
    """
    if not BANKING_VECTORSTORE:
        raise HTTPException(status_code=503, detail="Vector store not initialized.")

    logger.info(f"Received {len(files)} files for banking document ingestion.")
    temp_dir = tempfile.mkdtemp()
    filepaths = []

    try:
        for file in files:
            ext = os.path.splitext(file.filename)[1].lower()
            if ext not in ['.pdf', '.xls', '.xlsx', '.csv', '.doc', '.docx', '.txt', '.json']:
                logger.warning(f"Skipping unsupported file: {file.filename}")
                continue

            temp_path = os.path.join(temp_dir, file.filename)
            with open(temp_path, "wb") as f:
                f.write(await file.read())
            filepaths.append(temp_path)

        if not filepaths:
            return {"message": "No valid files were uploaded."}

        result = ingest_documents_to_chroma(filepaths, BANKING_VECTORSTORE)
        load_vector_stores()  # Reload to ensure new data is active

        return {
            "message": f"✅ Successfully processed {len(filepaths)} file(s).",
            "details": result
        }

    except Exception as e:
        logger.error(f"Document upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Document ingestion failed: {str(e)}")

    finally:
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
