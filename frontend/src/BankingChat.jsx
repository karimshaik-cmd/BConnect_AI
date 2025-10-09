import React, { useState, useEffect, useRef, useCallback } from 'react';
import BankingLogo from './components/BankingLogo';
import ChatMessage from './components/ChatMessage';
import { v4 as uuidv4 } from 'uuid';

const API_BASE_URL = 'http://127.0.0.1:8000';

function BankingChat() {
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState({ type: '', text: '' });
  
  const chatEndRef = useRef(null);

  // --- Utility Functions ---

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const clearUploadMessage = () => {
    setTimeout(() => setUploadMessage({ type: '', text: '' }), 4000);
  }

  // --- API Functions ---

  const fetchSessions = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions`);
      if (!response.ok) throw new Error('Failed to fetch sessions');
      const data = await response.json();
      setSessions(data);

      // If no session is active, start a new one or load the last one
      if (data.length > 0 && !currentSessionId) {
        const lastSession = data[data.length - 1];
        setCurrentSessionId(lastSession.session_id);
        setChatHistory(lastSession.messages);
      } else if (data.length === 0 && !currentSessionId) {
        startNewChat();
      }
    } catch (error) {
      console.error("Error fetching sessions:", error);
    }
  }, [currentSessionId]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  useEffect(scrollToBottom, [chatHistory]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    const userQuestion = message.trim();
    setMessage('');
    setIsLoading(true);

    const sessionId = currentSessionId || uuidv4();
    
    // Add user message immediately
    const newUserMessage = { role: 'user', content: userQuestion };
    setChatHistory(prev => [...prev, newUserMessage]);
    setCurrentSessionId(sessionId); // Ensure session is set

    try {
      const response = await fetch(`${API_BASE_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userQuestion, session_id: sessionId }),
      });

      if (!response.ok) throw new Error('Network response was not ok');

      const data = await response.json();
      
      setChatHistory(data.history);
      setCurrentSessionId(data.session_id);
      fetchSessions(); // Update sidebar with new session/message
      
    } catch (error) {
      console.error("Error sending message:", error);
      const errorMessage = { role: 'assistant', content: 'Sorry, I am currently unable to connect to the AI service.' };
      setChatHistory(prev => [...prev.slice(0, -1), newUserMessage, errorMessage]); // Replace loading message with error
    } finally {
      setIsLoading(false);
    }
  };

  const startNewChat = () => {
    setCurrentSessionId(uuidv4());
    setChatHistory([]);
    setMessage('');
  };

  const switchSession = (session) => {
    setCurrentSessionId(session.session_id);
    setChatHistory(session.messages);
  };

  const handleFileUpload = async (e, type) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    const endpoint = type === 'pdf' ? '/upload-pdfs' : '/upload-errors';
    const fileType = type === 'pdf' ? 'PDF' : 'JSON Error';
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    setUploadMessage({ type: 'info', text: `Uploading ${files.length} ${fileType} file(s)...` });

    try {
      const response = await fetch(`${API_BASE_URL}${endpoint}`, {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) throw new Error(data.detail || 'Upload failed');

      setUploadMessage({ type: 'success', text: data.message });
    } catch (error) {
      console.error("Upload error:", error);
      setUploadMessage({ type: 'error', text: `Upload failed: ${error.message}` });
    } finally {
      e.target.value = null; // Clear file input
      clearUploadMessage();
    }
  };

  // --- Render Components ---

  const renderSidebar = () => (
    <div className="sidebar">
      <div className="sidebar-header">
        <BankingLogo />
        <h2 className="title-text">BCONNECT AI</h2>
      </div>

      {/* New Chat Button */}
      <button className="new-chat-button" onClick={startNewChat}>
        <i className="fas fa-plus"></i> New Chat
      </button>
      
      {/* File Uploads */}
      <div className="upload-section">
        <label className="upload-label pdf-upload">
          <input
            type="file"
            accept=".pdf,.xls,.xlsx,.doc,.docx"
            multiple
            onChange={(e) => handleFileUpload(e, 'pdf')}
          />
          <i className="fas fa-file-pdf"></i> Upload Banking PDFs
        </label>
        <label className="upload-label error-upload">
          <input 
            type="file" 
            accept=".json" 
            multiple 
            onChange={(e) => handleFileUpload(e, 'error')} 
          />
          <i className="fas fa-bug"></i> Upload Error JSONs
        </label>
      </div>

      {/* Chat History */}
      <div className="chat-history-list">
        <h3>History</h3>
        {sessions.map((session) => (
          <div 
            key={session.session_id} 
            className={`history-item ${session.session_id === currentSessionId ? 'active' : ''}`}
            onClick={() => switchSession(session)}
          >
            <i className="fas fa-comment-dots"></i>
            {session.name || 'New Chat'}
          </div>
        ))}
      </div>
    </div>
  );

  const renderMainChat = () => (
    <div className="main-chat-area">
      <div className="chat-messages">
        {chatHistory.length === 0 ? (
          <div className="chat-placeholder">
            <i className="fas fa-robot"></i>
            <h1>How can I assist your banking inquiries today?</h1>
            <p>I can provide factual information from uploaded documents, or help troubleshoot system errors.</p>
          </div>
        ) : (
          chatHistory.map((msg, index) => (
            <ChatMessage key={index} message={msg} />
          ))
        )}
        {isLoading && (
          <div className="chat-message ai-message loading-message">
            <div className="message-content">
              <div className="dot-flashing"></div>
            </div>
          </div>
        )}
        <div ref={chatEndRef} />
      </div>

      {uploadMessage.text && (
        <div className={`upload-status-bar ${uploadMessage.type}`}>
          <i className={`fas ${uploadMessage.type === 'error' ? 'fa-times-circle' : 'fa-check-circle'}`}></i>
          {uploadMessage.text}
        </div>
      )}

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask a banking-related question..."
          disabled={isLoading}
        />
        <button type="submit" disabled={!message.trim() || isLoading}>
          <i className={`fas ${isLoading ? 'fa-spinner fa-spin' : 'fa-paper-plane'}`}></i>
        </button>
      </form>
    </div>
  );

  return (
    <div className="chat-app-container">
      {renderSidebar()}
      {renderMainChat()}
    </div>
  );
}

export default BankingChat;