// src/components/Login.jsx
import React, { useState } from "react";
import AnimatedLogo from "./AnimatedLogo";

/**
 * Banking Connect Login
 * - Copilot AI UI inspired design
 */

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (username === "user" && password === "userpass") {
      onLogin("user");
    } else if (username === "admin" && password === "adminpass") {
      onLogin("admin");
    } else {
      setError("Invalid credentials");
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#1a1a2e] to-[#16213e] p-6">
      {/* Copilot-inspired purple theme */}
      <style>{`
        :root {
          --copilot-purple: #7C3AED;
          --copilot-light-purple: #A855F7;
        }
      `}</style>

      <div className="w-full max-w-md">
        {/* Centered login card */}
        <div className="p-10 rounded-2xl bg-gradient-to-tr from-[#2a2a3e] to-[#1e1e2e] shadow-2xl backdrop-blur-md border border-purple-500/20">
          <div className="flex flex-col items-center mb-10">
            <AnimatedLogo />
           
            <p className="text-white text-1xl font-bold mt-2">Sign in to continue</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">
                Username
              </label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                className="w-full rounded-lg bg-gray-800/50 border border-purple-500/30 px-4 py-3 text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                required
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-medium text-gray-300">
                  Password
                </label>
                <a href="#" className="text-xs text-cyan-400 hover:text-cyan-300 transition-colors">
                  Forgot?
                </a>
              </div>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="w-full rounded-lg bg-gray-800/50 border border-purple-500/30 px-4 py-3 text-white placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                required
              />
            </div>

            {error && (
              <div className="text-red-400 text-sm text-center bg-red-900/20 rounded-lg py-2">
                {error}
              </div>
            )}

            <button
              type="submit"
              className="w-full py-3 rounded-lg text-white font-semibold bg-gradient-to-r from-[#1e6ff7] to-[#00e5ff] shadow-lg hover:shadow-cyan-400/50 hover:scale-[1.02] transition-all duration-200"
            >
              Sign in to Banking Connect
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
