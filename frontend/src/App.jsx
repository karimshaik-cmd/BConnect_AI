import React, { useState } from 'react';
import '@fortawesome/fontawesome-free/css/all.min.css';
import BankingChat from './BankingChat';
import Login from './components/Login';
import UserPage from './components/UserPage';
import './BankingChat.css'; // Global styles for the chat app

function App() {
  const [loggedInUser, setLoggedInUser] = useState(null);

  const handleLogin = (userType) => {
    setLoggedInUser(userType);
  };

  const handleLogout = () => {
    setLoggedInUser(null);
  };

  if (!loggedInUser) {
    return <Login onLogin={handleLogin} />;
  }

  if (loggedInUser === 'user') {
    return <UserPage onLogout={handleLogout} userType={loggedInUser} />;
  }

  if (loggedInUser === 'admin') {
    return (
      <div className="App">
        <BankingChat onLogout={handleLogout} userType={loggedInUser} />
      </div>
    );
  }

  return null;
}

export default App;
