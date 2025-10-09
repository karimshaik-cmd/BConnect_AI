# BCONNECT: Full-Stack Banking Chatbot

This project implements a full-stack banking assistant chatbot using **FastAPI** for the backend (with LangChain, Mistral LLM, and ChromaDB) and **React** (with Vite) for the frontend user interface.

## Prerequisites

1.  **Python 3.9+**
2.  **Node.js 18+** (LTS recommended)
3.  **Git**
4.  **Mistral LLM File**: The specified model is `mistral-7b-instruct-v0.2.Q4_K_M.gguf`. You must download this file and place it in the `./backend/models/` directory.

    * *Note: This file is several gigabytes and must be obtained from a reputable source like Hugging Face or the official LLamaCpp/Mistral repositories.*

## 1. Backend Setup

### A. Environment Setup and Dependencies

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```
2.  Create a virtual environment (optional but recommended):
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  Install Python dependencies:
    ```bash
    pip install -r requirements.txt
    ```
    * **Note on `llama-cpp-python`**: If you have a GPU (CUDA or Metal), you may want to install the library with GPU support for performance:
        ```bash
        # Example for CUDA
        pip uninstall llama-cpp-python -y
        CMAKE_ARGS="-DLLAMA_CUBLAS=on" FORCE_CMAKE=1 pip install llama-cpp-python
        ```

### B. LLM Model Placement

1.  Create the models folder:
    ```bash
    mkdir -p models
    ```
2.  **Download** `mistral-7b-instruct-v0.2.Q4_K_M.gguf` and place it here:
    ```
    ./backend/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf
    ```

### C. Run the Backend Server

Run the FastAPI application using Uvicorn:

```bash
uvicorn server:app --reload --host 127.0.0.1 --port 8000