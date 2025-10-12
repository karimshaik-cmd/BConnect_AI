import React from "react";

export default function SidebarLogo({ size = 24 }) {
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
          0% { stroke-dashoffset: 200; }
          50% { stroke-dashoffset: 0; }
          100% { stroke-dashoffset: 200; }
        }

        @keyframes drawBottom {
          0% { stroke-dashoffset: 200; }
          50% { stroke-dashoffset: 0; }
          100% { stroke-dashoffset: 200; }
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

        .b-shape {
          animation: logoGlowPulse 3s ease-in-out 0s infinite;
        }
        .arrow-top {
          animation: arrowInTop 3s ease-out infinite, drawTop 3s ease-in-out infinite;
        }
        .arrow-bottom {
          animation: arrowInBottom 3s ease-out infinite, drawBottom 5s ease-in-out infinite;
        }
        .text-connect {
          animation: textReveal 3s ease-out 3s infinite;
        }
      `}</style>

      {/* SVG "B" Shape */}
      <svg
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 120 120"
        width={size}
        height={size}
        className="b-shape"
      >
        {/* Top arrow */}
        <path
          className="arrow-top"
          d="M60 15 h20 a20 20 0 0 1 0 40 h-20 l15-15 -15-15Z"
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
          d="M60 65 h20 a20 20 0 0 1 0 40 h-20 l15-15 -15-15Z"
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

      {/* Text */}
      <h1 className="text-xl font-bold text-white tracking-wide opacity-0 text-connect">
        Banking Connect
      </h1>
    </div>
  );
}
