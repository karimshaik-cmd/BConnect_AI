// src/components/Login.jsx
import React, { useState } from "react";
import AnimatedLogo from "./AnimatedLogo";
import "./NeuralLogin.css";

/**
 * Banking Connect Login
 * - Neural AI UI inspired design
 */

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [passwordVisible, setPasswordVisible] = useState(false);

  const validateUsername = () => {
    if (!username.trim()) {
      showError("username", "User ID required to initiate access");
      return false;
    }
    clearError("username");
    return true;
  };

  const validatePassword = () => {
    if (!password) {
      showError("password", "Access key required");
      return false;
    }
    if (password.length < 6) {
      showError("password", "Access key must contain at least 6 characters");
      return false;
    }
    clearError("password");
    return true;
  };

  const showError = (field, message) => {
    const smartField = document.getElementById(field).closest('.smart-field');
    const errorElement = document.getElementById(`${field}Error`);
    smartField.classList.add('error');
    errorElement.textContent = message;
    errorElement.classList.add('show');
  };

  const clearError = (field) => {
    const smartField = document.getElementById(field).closest('.smart-field');
    const errorElement = document.getElementById(`${field}Error`);
    smartField.classList.remove('error');
    errorElement.classList.remove('show');
    setTimeout(() => {
      errorElement.textContent = '';
    }, 200);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    const isUsernameValid = validateUsername();
    const isPasswordValid = validatePassword();

    if (!isUsernameValid || !isPasswordValid) {
      return;
    }

    setIsLoading(true);

    try {
      // Simulate AI authentication processing
      await new Promise(resolve => setTimeout(resolve, 2500));

      // Check credentials
      if (username === "user" && password === "userpass") {
        showNeuralSuccess();
        setTimeout(() => onLogin("user"), 3200);
      } else if (username === "admin" && password === "adminpass") {
        showNeuralSuccess();
        setTimeout(() => onLogin("admin"), 3200);
      } else {
        showError("password", "Authentication failed — please verify credentials");
      }
    } catch (error) {
      showError("password", "Connection attempt failed. Try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const showNeuralSuccess = () => {
    const form = document.getElementById('loginForm');
    const signup = document.querySelector('.signup-section');
    const successMessage = document.getElementById('successMessage');

    form.style.transform = 'scale(0.95)';
    form.style.opacity = '0';

    setTimeout(() => {
      form.style.display = 'none';
      signup.style.display = 'none';
      successMessage.classList.add('show');
    }, 300);
  };

  const togglePasswordVisibility = () => {
    setPasswordVisible(!passwordVisible);
  };

  const handleSocialLogin = (provider) => {
    console.log(`Initializing ${provider} Banking Connect Connection...`);
    // Placeholder for social login functionality
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6" style={{ background: '#0a0a0f', fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Inter", sans-serif' }}>
      {/* Neural Background */}
      <div className="neural-background">
        <div className="neural-node"></div>
        <div className="neural-node"></div>
        <div className="neural-node"></div>
        <div className="neural-node"></div>
        <div className="neural-node"></div>
      </div>

      <div className="login-container">
        <div className="login-card">
          <div className="ai-glow"></div>

          <div className="login-header">
            <div className="ai-logo">
              <AnimatedLogo size={60} />
            </div>
            <h1>Banking Connect Access</h1>
            <p>Accessing your Secure AI Console</p>
          </div>

          <form id="loginForm" onSubmit={handleSubmit} className="login-form" noValidate>
            <div className="smart-field" data-field="username">
              <div className="field-background"></div>
              <input
                type="text"
                id="username"
                name="username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoComplete="username"
                placeholder=" "
              />
              <label htmlFor="username">Username</label>
              <div className="ai-indicator">
                <div className="ai-pulse"></div>
              </div>
              <div className="field-completion"></div>
              <span className="error-message" id="usernameError"></span>
            </div>

            <div className="smart-field" data-field="password">
              <div className="field-background"></div>
              <input
                type={passwordVisible ? "text" : "password"}
                id="password"
                name="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
                placeholder=" "
              />
              <label htmlFor="password">Password</label>
              <button
                type="button"
                className={`smart-toggle ${passwordVisible ? 'toggle-active' : ''}`}
                id="passwordToggle"
                onClick={togglePasswordVisibility}
                aria-label="Toggle password visibility"
              >
                <svg className="toggle-show" width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path d="M9 3.75c-3.15 0-5.85 1.89-7.02 4.72a.75.75 0 000 .56c1.17 2.83 3.87 4.72 7.02 4.72s5.85-1.89 7.02-4.72a.75.75 0 000-.56C14.85 5.64 12.15 3.75 9 3.75zM9 12a3 3 0 110-6 3 3 0 010 6z" fill="currentColor"/>
                </svg>
                <svg className="toggle-hide" width="18" height="18" viewBox="0 0 18 18" fill="none">
                  <path d="M3.53 2.47a.75.75 0 00-1.06 1.06l11 11a.75.75 0 101.06-1.06l-2.82-2.82c.8-.67 1.5-1.49 2.04-2.42a.75.75 0 000-.56C12.58 4.84 10.89 3.75 9 3.75c-.69 0-1.36.1-2 .29L3.53 2.47zM7.974 5.847L10.126 8a1.5 1.5 0 01-2.126-2.126l-.026-.027z" fill="currentColor"/>
                </svg>
              </button>
              <div className="ai-indicator">
                <div className="ai-pulse"></div>
              </div>
              <div className="field-completion"></div>
              <span className="error-message" id="passwordError"></span>
            </div>

            <div className="form-options">
              <label className="smart-checkbox">
                <input type="checkbox" id="remember" name="remember" />
                <span className="checkbox-ai">
                  <div className="checkbox-core"></div>
                  <svg width="12" height="10" viewBox="0 0 12 10" fill="none">
                    <path d="M1 5l3 3 7-7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  </svg>
                </span>
                <span className="checkbox-text">Remember this session</span>
              </label>
              <a href="#" className="neural-link">Recover Access Key</a>
            </div>

            <button type="submit" className={`neural-button ${isLoading ? 'loading' : ''}`} disabled={isLoading}>
              <div className="button-bg"></div>
              <span className="button-text">Activate Secure Connection</span>
              <div className="button-loader">
                <div className="neural-spinner">
                  <div className="spinner-segment"></div>
                  <div className="spinner-segment"></div>
                  <div className="spinner-segment"></div>
                </div>
              </div>
              <div className="button-glow"></div>
            </button>
          </form>



          <div className="signup-section">
            <span>New to Banking Connect? </span>
            <a href="#" className="neural-signup">Create your AI Access.</a>
          </div>

          <div className="success-neural" id="successMessage">
            <div className="success-core">
              <div className="success-rings">
                <div className="success-ring"></div>
                <div className="success-ring"></div>
                <div className="success-ring"></div>
              </div>
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <h3>Connection Established — AI Workspace Ready</h3>
            <p>Activating Intelligent Workspace...</p>
          </div>
        </div>
      </div>
    </div>
  );
}
