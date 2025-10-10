import React from 'react';
// You might want to import a CSS file here, e.g., import './BankingConnectLogo.css';

const BankingConnectLogo = ({ size = 100, color = '#007bff' }) => {
  const logoWidth = size * 1.5;
  const logoHeight = size;

  return (
    <svg
      viewBox={`0 0 ${logoWidth} ${logoHeight}`}
      width={logoWidth}
      height={logoHeight}
      xmlns="http://www.w3.org/2000/svg"
      role="img"
      aria-labelledby="logoTitle logoDesc"
    >
      <title id="logoTitle">Banking Connect Logo</title>
      <desc id="logoDesc">Animated logo showing a bank connecting to a link icon.</desc>

      {/* --- Connection Line (Animated) --- */}
      {/* The line will be hidden by default and drawn using CSS animation */}
      <path
        id="connect-line"
        d={`M ${logoWidth * 0.4} ${logoHeight * 0.45} L ${logoWidth * 0.7} ${logoHeight * 0.55}`}
        stroke={color}
        strokeWidth="5"
        fill="none"
        strokeLinecap="round"
        strokeDasharray="1000" // Set a large dash array for the drawing animation
        strokeDashoffset="1000"
        className="connect-line-animate" // CSS class for animation
      />
      
      {/* --- Bank Icon (Left) --- */}
      <g
        transform={`translate(${logoWidth * 0.15}, ${logoHeight * 0.2}) scale(${size / 150})`}
        fill={color}
        className="bank-icon-animate" // CSS class for slight pulse animation
      >
        {/* Bank shape (simple house/building) */}
        <path d="M 5 20 L 5 45 L 45 45 L 45 20 Z" stroke="none" />
        {/* Roof */}
        <path d="M 0 25 L 25 5 L 50 25 Z" fill={color} />
        {/* Windows (simple lines) */}
        <line x1="15" y1="30" x2="15" y2="40" stroke="white" strokeWidth="2" strokeLinecap="round" />
        <line x1="35" y1="30" x2="35" y2="40" stroke="white" strokeWidth="2" strokeLinecap="round" />
      </g>

      {/* --- Link/Connect Icon (Right) --- */}
      <g
        transform={`translate(${logoWidth * 0.75}, ${logoHeight * 0.3}) scale(${size / 150})`}
        stroke={color}
        strokeWidth="4"
        fill="none"
        strokeLinecap="round"
        className="link-icon-animate" // CSS class for slight pulse animation
      >
        {/* Link chain part 1 (rotated) */}
        <path d="M 0 10 C 0 0, 10 0, 10 10 L 10 30 C 10 40, 0 40, 0 30 Z" transform="rotate(-45 20 20) translate(-10 20)" />
        {/* Link chain part 2 (rotated and offset) */}
        <path d="M 0 10 C 0 0, 10 0, 10 10 L 10 30 C 10 40, 0 40, 0 30 Z" transform="rotate(45 20 20) translate(10 -10)" />
      </g>

    </svg>
  );
};

export default BankingConnectLogo;
