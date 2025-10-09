import React from 'react';

// Inlined BankingLogo component, maintaining the futuristic aesthetic
function BankingLogo() {
  // Omitted useEffect animation for simplicity in the chat view, but kept the structure
  return (
    <div className="banking-logo-container">
      <div className="banking-logo-svg">
        <div className="circle-outer"></div>
        <div className="circle-inner"></div>
        <svg
          className="logo-arrows"
          viewBox="0 0 120 120"
          xmlns="http://www.w3.org/2000/svg"
          aria-hidden
        >
          <defs>
            <linearGradient id="arrowColor" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#00eaff" />
              <stop offset="50%" stopColor="#009dff" />
              <stop offset="100%" stopColor="#005eff" />
            </linearGradient>

            <filter id="softGlow" x="-50%" y="-50%" width="200%" height="200%">
              <feGaussianBlur stdDeviation="3" result="blur" />
              <feMerge>
                <feMergeNode in="blur" />
                <feMergeNode in="SourceGraphic" />
              </feMerge>
            </filter>
          </defs>

          {/* Outer glowing circle */}
          <circle
            cx="60"
            cy="60"
            r="50"
            stroke="url(#arrowColor)"
            strokeWidth="3"
            fill="none"
            filter="url(#softGlow)"
          />

          {/* Arrows for data flow indication */}
          <g transform="translate(60,60) rotate(-40) scale(2.1) translate(-11,-11)">
            <path
              d="M1.056 21.928c0-6.531 5.661-9.034 10.018-9.375V18.1L22.7 9.044 11.073 0v4.836a10.5 10.5 0 0 0-7.344 3.352C-.618 12.946-.008 21 .076 21.928z"
              fill="url(#arrowColor)"
              filter="url(#softGlow)"
            />
          </g>

          <g transform="translate(60,60) rotate(140) scale(2.1) translate(-11,-11)">
            <path
              d="M1.056 21.928c0-6.531 5.661-9.034 10.018-9.375V18.1L22.7 9.044 11.073 0v4.836a10.5 10.5 0 0 0-7.344 3.352C-.618 12.946-.008 21 .076 21.928z"
              fill="url(#arrowColor)"
              filter="url(#softGlow)"
            />
          </g>
        </svg>

        <div className="tech-dots">
          <span className="dot dot1"></span>
          <span className="dot dot2"></span>
          <span className="dot dot3"></span>
          <span className="dot dot4"></span>
        </div>
      </div>
    </div>
  );
}

export default BankingLogo;