import React from 'react';
import '../LoginUserPages.css';

const UserPage = ({ onLogout }) => {
  return (
    <div className="user-page">
      <button onClick={onLogout} className="sidebar-logout-button">Logout</button>
      <h2>Welcome User</h2>
      <p>This page is currently empty.</p>
    </div>
  );
};

export default UserPage;
