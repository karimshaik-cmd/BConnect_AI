import React, { useState } from 'react';
import '../LoginUserPages.css';

const Login = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (username === 'user' && password === 'userpass') {
      onLogin('user');
    } else if (username === 'admin' && password === 'adminpass') {
      onLogin('admin');
    } else {
      setError('Invalid credentials');
    }
  };

  return (
    <div className="login-page">
      <div className="login-header">
        <div className="logo">
          <h1>BCONNECT</h1>
        </div>
      </div>
      <div className="login-form-container">
        <h2>Sign in</h2>
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="input-field">
            <input
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="input-field">
            <input
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          {error && <p className="error-message">{error}</p>}
          <button type="submit" className="sign-in-button">
            Sign in
          </button>
        </form>
        <a href="#" className="forgot-link">Forgot password?</a>
      </div>
    </div>
  );
};

export default Login;
