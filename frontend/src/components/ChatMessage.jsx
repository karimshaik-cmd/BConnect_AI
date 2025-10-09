import React from 'react';

const ChatMessage = ({ message }) => {
  const isUser = message.role === 'user';
  const className = isUser ? 'chat-message user-message' : 'chat-message ai-message';

  return (
    <div className={className}>
      <div className="message-content">
        {message.content}
      </div>
    </div>
  );
};

export default ChatMessage;