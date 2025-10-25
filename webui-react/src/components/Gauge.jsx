// src/components/Gauge.jsx
// A semi-circle gauge with a needle that points to the given percentage (0-100).

export default function Gauge({ value = 0 }) {
  // 1. Normalize/clamp the input to [0,100]
  const clamped = Math.max(0, Math.min(100, Number(value) || 0));

  // 2. Convert 0..100 to an angle on a 240deg arc (-120deg to +120deg)
  const angle = -120 + (clamped / 100) * 240;

  // 3. Color hint for the needle (red at 0, green at 100)
  const hue = clamped * 1.2; // 0..120
  const needleColor = `hsl(${hue} 90% 35%)`;

  return (
    <div className="w-full flex flex-col items-center">
      <svg viewBox="0 0 200 120" className="w-full max-w-md">
        {/* Background arc (gray) */}
        <path
          d="M20,120 A80,80 0 1,1 180,120"
          fill="none"
          stroke="#eee"
          strokeWidth="16"
        />

        {/* Colored arc gradient */}
        <defs>
          <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#ef4444" />    {/* red */}
            <stop offset="50%" stopColor="#f59e0b" />   {/* amber */}
            <stop offset="100%" stopColor="#22c55e" />  {/* green */}
          </linearGradient>
        </defs>

        <path
          d="M20,120 A80,80 0 1,1 180,120"
          fill="none"
          stroke="url(#g)"
          strokeWidth="10"
        />

        {/* Needle (the pointer) */}
        <g transform={`translate(100,120) rotate(${angle})`}>
          {/* the pointer arm */}
          <rect
            x="-2"
            y="-70"
            width="4"
            height="70"
            fill={needleColor}
            rx="2"
          />
          {/* center pivot */}
          <circle cx="0" cy="0" r="6" fill="#111" />
        </g>

        {/* Numeric label under the arc */}
        <text
          x="100"
          y="115"
          textAnchor="middle"
          fontSize="14"
          fill="#111"
          direction="ltr"
        >
          {Math.round(clamped)}%
        </text>
      </svg>
    </div>
  );
}
