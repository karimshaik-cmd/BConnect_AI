import React, { useState, useEffect, useRef, useCallback } from 'react';
import SidebarLogo from './components/SidebarLogo';
import ChatMessage from './components/ChatMessage';
import { v4 as uuidv4 } from 'uuid';
import './BankingChat.css';

const API_BASE_URL = 'http://127.0.0.1:8000';

function BankingChat({ onLogout, userType }) {
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [message, setMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [sessions, setSessions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState({ type: '', text: '' });
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [showMenuId, setShowMenuId] = useState(null);
  const [showLogoutAlert, setShowLogoutAlert] = useState(false);
  const [showLogoutSuccess, setShowLogoutSuccess] = useState(false);

  const chatEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // --- Utility Functions ---

  const scrollToBottom = () => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const clearUploadMessage = () => {
    setTimeout(() => setUploadMessage({ type: '', text: '' }), 4000);
  }

  const handleLogout = () => {
    setShowLogoutAlert(true);
  };

  const confirmLogout = () => {
    setShowLogoutAlert(false);
    setShowLogoutSuccess(true);
    setTimeout(() => {
      setShowLogoutSuccess(false);
      onLogout();
    }, 3200);
  };

  const cancelLogout = () => {
    setShowLogoutAlert(false);
  };

  // --- API Functions ---

  const fetchSessions = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions?user_type=${userType}`);
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
  }, [currentSessionId, userType]);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  useEffect(scrollToBottom, [chatHistory]);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showMenuId !== null && !event.target.closest('.history-item')) {
        setShowMenuId(null);
      }
    };

    document.addEventListener('click', handleClickOutside);
    return () => document.removeEventListener('click', handleClickOutside);
  }, [showMenuId]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!message.trim() || isLoading) return;

    const userQuestion = message.trim();
    setMessage('');
    setIsLoading(true);
    setSelectedFiles([]); // Clear attachments after sending

    const sessionId = currentSessionId || uuidv4();

    // Add user message immediately
    const newUserMessage = { role: 'user', content: userQuestion };
    setChatHistory(prev => [...prev, newUserMessage]);
    setCurrentSessionId(sessionId); // Ensure session is set

    try {
      const response = await fetch(`${API_BASE_URL}/ask`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question: userQuestion, session_id: sessionId, user_type: userType }),
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
    setSelectedFiles([]);
  };

  const switchSession = (session) => {
    setCurrentSessionId(session.session_id);
    setChatHistory(session.messages);
    setSelectedFiles([]);
  };

  const [editingSessionId, setEditingSessionId] = useState(null);
  const [editedName, setEditedName] = useState('');

  const deleteSession = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete session');
      // Refetch sessions
      await fetchSessions();
      // If deleted session was current, start new chat
      if (sessionId === currentSessionId) {
        startNewChat();
      }
    } catch (error) {
      console.error("Error deleting session:", error);
    }
  };

  const renameSession = async (sessionId, newName) => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName }),
      });
      if (!response.ok) throw new Error('Failed to rename session');
      await fetchSessions();
      setEditingSessionId(null);
      setEditedName('');
    } catch (error) {
      console.error("Error renaming session:", error);
    }
  };

  const archiveSession = async (sessionId) => {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}/archive`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to archive session');
      await fetchSessions();
    } catch (error) {
      console.error("Error archiving session:", error);
    }
  };

  const shareSession = (sessionId) => {
    const shareUrl = `${window.location.origin}/share/${sessionId}`;
    navigator.clipboard.writeText(shareUrl).then(() => {
      alert('Share link copied to clipboard!');
    }).catch(() => {
      prompt('Share this link:', shareUrl);
    });
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    setSelectedFiles(prev => [...prev, ...files]);

    // Upload all files immediately upon selection
    if (files.length > 0) {
      handleFileUpload({ target: { files: files } }, 'pdf');
    }
  };

  const handleRemoveFile = (index) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index));
  };

  const getFileIcon = (fileName) => {
    const ext = fileName.split('.').pop().toLowerCase();
    switch (ext) {
      case 'pdf': return 'fas fa-file-pdf';
      case 'json': return 'fas fa-file-code';
      case 'xls':
      case 'xlsx': return 'fas fa-file-excel';
      case 'doc':
      case 'docx': return 'fas fa-file-word';
      default: return 'fas fa-file';
    }
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
        <SidebarLogo />
      </div>

      {/* New Chat Button */}
      <button className="new-chat-button" onClick={startNewChat}>
        <i className="fas fa-plus"></i> New Chat
      </button>

      {/* Chat History */}
      <div className="chat-history-list">
        <h3>History</h3>
        {sessions.map((session) => (
          <div
            key={session.session_id}
            className={`history-item ${session.session_id === currentSessionId ? 'active' : ''}`}
          >
            <span onClick={() => switchSession(session)} style={{ flex: 1, cursor: 'pointer' }}>
              <i className="fas fa-comment-dots"></i>
              {session.name || 'New Chat'}
            </span>
            <button
              className="menu-button"
              onClick={(e) => {
                e.stopPropagation();
                setShowMenuId(showMenuId === session.session_id ? null : session.session_id);
              }}
              title="More options"
            >
              <i className="fas fa-ellipsis-h"></i>
            </button>
            {showMenuId === session.session_id && (
              <div className="session-menu">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    shareSession(session.session_id);
                    setShowMenuId(null);
                  }}
                  className="menu-item"
                >
                  <i className="fas fa-share"></i> Share
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setEditingSessionId(session.session_id);
                    setEditedName(session.name || '');
                    setShowMenuId(null);
                  }}
                  className="menu-item"
                >
                  <i className="fas fa-edit"></i> Rename
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    archiveSession(session.session_id);
                    setShowMenuId(null);
                  }}
                  className="menu-item"
                >
                  <i className="fas fa-archive"></i> Archive
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteSession(session.session_id);
                    setShowMenuId(null);
                  }}
                  className="menu-item delete-menu-item"
                >
                  <i className="fas fa-trash"></i> Delete
                </button>
              </div>
            )}
            {editingSessionId === session.session_id && (
              <div className="session-menu">
                <input
                  type="text"
                  value={editedName}
                  onChange={(e) => setEditedName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      renameSession(session.session_id, editedName.trim() || 'New Chat');
                    }
                  }}
                  autoFocus
                  style={{ width: '100%', padding: '8px', border: 'none', background: 'rgba(255,255,255,0.1)', color: 'white' }}
                />
                <button
                  onClick={() => {
                    renameSession(session.session_id, editedName.trim() || 'New Chat');
                  }}
                  className="menu-item"
                >
                  <i className="fas fa-check"></i> Save
                </button>
                <button
                  onClick={() => {
                    setEditingSessionId(null);
                    setEditedName('');
                  }}
                  className="menu-item"
                >
                  <i className="fas fa-times"></i> Cancel
                </button>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Logout Button */}
      <button className="sidebar-logout-button" onClick={handleLogout}>
        <i className="fas fa-sign-out-alt"></i> Logout
      </button>
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

      {selectedFiles.length > 0 && (
        <div className="attachments-display">
          {selectedFiles.map((file, index) => (
            <div key={index} className="attachment-item">
              <i className={getFileIcon(file.name)}></i>
              <span className="file-name">{file.name}</span>
              <button
                type="button"
                className="remove-file"
                onClick={() => handleRemoveFile(index)}
              >
                ×
              </button>
            </div>
          ))}
        </div>
      )}

      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <button
          type="button"
          className="attach-button"
          onClick={() => fileInputRef.current?.click()}
          disabled={isLoading}
        >
          <i className="fas fa-paperclip"></i>
        </button>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Ask a banking-related question..."
          disabled={isLoading}
        />
        <button type="submit" disabled={(!message.trim() && selectedFiles.length === 0) || isLoading}>
          <i className={`fas ${isLoading ? 'fa-spinner fa-spin' : 'fa-paper-plane'}`}></i>
        </button>
      </form>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".pdf,.json,.xls,.xlsx,.doc,.docx"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
      />
    </div>
  );

  return (
    <div className="chat-app-container">
      {renderSidebar()}
      {renderMainChat()}

      {/* Logout Confirmation Alert */}
      {showLogoutAlert && (
        <div className="logout-alert-overlay">
          <div className="logout-alert">
            <div className="logout-core">
              <div className="logout-rings">
                <div className="logout-ring"></div>
                <div className="logout-ring"></div>
                <div className="logout-ring"></div>
              </div>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 15.5c-.77.833.192 2.5 1.732 2.5z" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <h3>Confirm Logout</h3>
            <p>Are you sure you want to log out? Any unsaved changes will be lost.</p>
            <div className="logout-alert-buttons">
              <button onClick={cancelLogout} className="cancel-button">Cancel</button>
              <button onClick={confirmLogout} className="confirm-button">Logout</button>
            </div>
          </div>
        </div>
      )}

      {/* Logout Success Alert */}
      {showLogoutSuccess && (
        <div className="logout-alert-overlay">
          <div className="logout-success-alert">
            <div className="logout-core">
              <div className="logout-rings">
                <div className="logout-ring"></div>
                <div className="logout-ring"></div>
                <div className="logout-ring"></div>
              </div>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M20 6L9 17l-5-5" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <h3>Logout Successful</h3>
            <p>You have been securely logged out of your session.</p>
          </div>
        </div>
      )}
    </div>
  );
}

export default BankingChat;