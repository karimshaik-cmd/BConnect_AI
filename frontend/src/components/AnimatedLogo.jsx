import React from "react";

export default function AnimatedLogo({ size = 60 }) {
  return (
    <div className="flex items-center gap-2">
      <style>{`
        @keyframes arrowInTop {
          0% { transform: rotate(-180deg) translateY(-40px); opacity: 0; }
          60% { transform: rotate(15deg) translateY(5px); opacity: 1; }
          100% { transform: rotate(0deg) translateY(0); opacity: 1; }
        }

        @keyframes arrowInBottom {
          0% { transform: rotate(180deg) translateY(40px); opacity: 0; }
          60% { transform: rotate(-15deg) translateY(-5px); opacity: 1; }
          100% { transform: rotate(0deg) translateY(0); opacity: 1; }
        }

        @keyframes drawTop {
          to { stroke-dashoffset: 0; }
        }

        @keyframes drawBottom {
          to { stroke-dashoffset: 0; }
        }

        @keyframes logoGlow {
          0% { filter: drop-shadow(0 0 0px rgba(0, 195, 255, 0)); }
          50% { filter: drop-shadow(0 0 10px rgba(0, 195, 255, 0.8)); }
          100% { filter: drop-shadow(0 0 0px rgba(0, 195, 255, 0)); }
        }
        @keyframes logoGlowPulse {
          0% { filter: drop-shadow(0 0 0px rgba(0, 195, 255, 0)); }
          50% { filter: drop-shadow(0 0 8px rgba(0, 195, 255, 0.4)); }
          100% { filter: drop-shadow(0 0 0px rgba(0, 195, 255, 0)); }
        }

        @keyframes textReveal {
          0% { opacity: 0; transform: translateX(20px); }
          70% { opacity: 1; transform: translateX(0); }
          100% { opacity: 1; transform: translateX(0); }
        }

        @keyframes ringPulse {
          0%, 100% { opacity: 0.3; transform: scale(1); }
          50% { opacity: 0.6; transform: scale(1.05); }
        }

        .b-shape {
          animation: logoGlowPulse 3s ease-in-out 0s infinite;
        }
        .arrow-top {
          animation: arrowInTop 3s ease-out infinite, drawTop 3s ease-out infinite;
        }
        .arrow-bottom {
          animation: arrowInBottom 3s ease-out infinite, drawBottom 3s ease-out infinite;
        }
        .text-connect {
          animation: textReveal 3s ease-out 3s forwards;
        }
        .ring {
          position: absolute;
          border: 1px solid rgba(59, 130, 246, 0.3);
          border-radius: 50%;
          animation: ringPulse 3s ease-in-out infinite;
        }
        .ring-1 {
          width: ${size * 0.857}px;
          height: ${size * 0.857}px;
          top: ${size * 0.143}px;
          left: ${size * 0.143}px;
          animation-delay: 0s;
        }
        .ring-2 {
          width: ${size}px;
          height: ${size}px;
          top: ${size * 0.071}px;
          left: ${size * 0.071}px;
          animation-delay: 1s;
        }
        .ring-3 {
          width: ${size * 1.143}px;
          height: ${size * 1.143}px;
          top: 0;
          left: 0;
          animation-delay: 2s;
        }
      `}</style>

      {/* Logo with Neural Rings */}
      <div style={{ position: 'relative', width: size * 1.143, height: size * 1.143 }}>
        {/* SVG "B" Shape - Centered in middle of rings */}
        <svg
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 120 120"
          width={size}
          height={size}
          className="b-shape"
          style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 1 }}

        >
          {/* Top arrow */}
          <path
            className="arrow-top"
            d="M40 15 h20 a20 20 0 0 1 0 40 h-20 l15-15 -15-15Z"
            fill="url(#grad1)"
            stroke="url(#grad1)"
            stroke-width="3"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-dasharray="200"
            stroke-dashoffset="200"
          />
          {/* Bottom arrow */}
          <path
            className="arrow-bottom"
            d="M40 65 h20 a20 20 0 0 1 0 40 h-20 l15-15 -15-15Z"
            fill="url(#grad1)"
            stroke="url(#grad1)"
            stroke-width="3"
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-dasharray="200"
            stroke-dashoffset="200"
          />
          <defs>
            <linearGradient id="grad1" x1="0" x2="1" y1="0" y2="1">
              <stop offset="0%" stopColor="#1e6ff7" />
              <stop offset="100%" stopColor="#00e5ff" />
            </linearGradient>
          </defs>
        </svg>

        {/* Neural Rings - After SVG */}
        <div className="ring ring-1"></div>
        <div className="ring ring-2"></div>
        <div className="ring ring-3"></div>
      </div>


    </div>
  );
}
