# Banking Chatbot

A full-stack banking chatbot application with AI-powered document analysis and chat functionality.

## Features

- **AI-Powered Chat**: Conversational interface powered by Mistral-7B LLM
- **Document Analysis**: Upload and analyze PDF documents and error logs
- **Vector Search**: ChromaDB-powered semantic search across banking documents
- **Single Production Server**: Combined frontend and backend serving
- **Modern UI**: React-based frontend with Tailwind CSS

## Quick Start

### Prerequisites
- Python 3.8+
- Node.js 16+
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd banking-chatbot
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Node.js dependencies**
   ```bash
   npm install
   ```

4. **Build the frontend**
   ```bash
   npm run build
   ```

### Running the Application

**Production Mode (Single Server)**
```bash
python start.py
```
This will build the frontend and start the combined server at `http://localhost:8000`

**Development Mode**
```bash
# Terminal 1: Start backend
cd backend
python server.py

# Terminal 2: Start frontend
npm run dev
```

## Project Structure

```
banking-chatbot/
├── backend/                 # FastAPI backend
│   ├── server.py           # Main server with API endpoints
│   ├── chat_engine.py      # Chat logic and LLM integration
│   ├── data_analyzer.py    # Document analysis functionality
│   ├── ingest_pdf.py       # PDF document processing
│   ├── ingest_errors.py    # Error log processing
│   ├── config/
│   │   └── settings.py     # Configuration settings
│   └── models/             # LLM models
├── frontend/               # React frontend
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── App.jsx         # Main app component
│   │   └── main.jsx        # Entry point
│   ├── dist/               # Built frontend (generated)
│   └── package.json
├── chroma_db/              # Vector database storage
├── start.py                # Production launcher
├── requirements.txt        # Python dependencies
└── package.json           # Root package.json
```

## API Endpoints

- `GET /` - Health check
- `POST /api/ask` - Chat with the AI
- `POST /api/upload-documents` - Upload PDF documents
- `POST /api/upload-errors` - Upload error logs
- `GET /api/sessions` - Get chat sessions
- `POST /api/sessions` - Create new session
- `GET /api/sessions/{session_id}` - Get session details

## Configuration

Edit `backend/config/settings.py` to configure:
- API keys (GROQ_API_KEY)
- Model settings
- Vector database parameters
- UI settings

## Deployment

### For Company Laptop (Offline Installation)

1. **Prepare the zip file on your personal machine:**
   ```bash
   # Install all dependencies
   pip install -r requirements.txt
   npm install
   npm run build

   # Create zip file
   zip -r banking-chatbot.zip .
   ```

2. **On company laptop:**
   - Extract the zip file
   - Run `python start.py`
   - Access at `http://localhost:8000`

### Docker Deployment (Optional)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN cd frontend && npm install && npm run build

EXPOSE 8000
CMD ["python", "start.py"]
```

## Troubleshooting

### Common Issues

1. **LLM Model Not Found**
   - Ensure `backend/models/mistral-7b-instruct-v0.2.Q4_K_M.gguf` exists
   - Check model path in `server.py`

2. **Frontend Build Fails**
   - Ensure Node.js 16+ is installed
   - Run `npm install` in frontend directory

3. **Vector Store Issues**
   - Delete `chroma_db/` directory to reset
   - Re-upload documents after restart

### Logs

Check logs in:
- Backend: Console output when running server
- Frontend: Browser developer tools

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes
4. Test thoroughly
5. Submit a pull request

## License

ISC License
