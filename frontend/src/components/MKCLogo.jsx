export default function MKCLogo({ size = 200, className = '' }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 200 240"
      width={size}
      height={size * 1.2}
      className={`mkc-logo-svg ${className}`}
      fill="none"
    >
      <defs>
        {/* Holographic Cyan-to-Blue Gradient (top-light to bottom-dark) */}
        <linearGradient id="holoCyan" x1="50%" y1="0%" x2="50%" y2="100%">
          <stop offset="0%" stopColor="#FFFFFF" />
          <stop offset="15%" stopColor="#B3FFFF" />
          <stop offset="40%" stopColor="#4DE8FF" />
          <stop offset="70%" stopColor="#00C8F0" />
          <stop offset="100%" stopColor="#0088CC" />
        </linearGradient>

        {/* Deeper shadow tone for bevel edges */}
        <linearGradient id="holoDark" x1="50%" y1="0%" x2="50%" y2="100%">
          <stop offset="0%" stopColor="#00AADD" />
          <stop offset="50%" stopColor="#007799" />
          <stop offset="100%" stopColor="#004466" />
        </linearGradient>

        {/* Specular white highlight gradient */}
        <linearGradient id="holoHighlight" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stopColor="#FFFFFF" stopOpacity="0.95" />
          <stop offset="50%" stopColor="#CCFFFF" stopOpacity="0.6" />
          <stop offset="100%" stopColor="#66E5FF" stopOpacity="0.2" />
        </linearGradient>

        {/* Subtle ambient bloom glow */}
        <filter id="ambientGlow" x="-25%" y="-25%" width="150%" height="150%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>

        {/* Intense small-node glow */}
        <filter id="nodeGlow" x="-80%" y="-80%" width="260%" height="260%">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>

      {/* ============================================================
          1. FLOOR GLOW REFLECTION (bright cyan horizontal line + sparks)
          ============================================================ */}
      <line x1="55" y1="228" x2="145" y2="228" stroke="#00E5FF" strokeWidth="2" strokeLinecap="round" opacity="0.9" filter="url(#ambientGlow)" />
      <line x1="75" y1="228" x2="125" y2="228" stroke="#FFFFFF" strokeWidth="1" strokeLinecap="round" opacity="0.85" />
      {/* Tiny sparks near floor */}
      <g opacity="0.7" filter="url(#nodeGlow)">
        <circle cx="62" cy="226" r="1" fill="#80FFFF" />
        <circle cx="138" cy="226" r="1" fill="#80FFFF" />
        <circle cx="85" cy="224" r="0.8" fill="#FFFFFF" />
        <circle cx="115" cy="224" r="0.8" fill="#FFFFFF" />
        <circle cx="100" cy="223" r="1.2" fill="#FFFFFF" />
      </g>

      {/* ============================================================
          2. BACKGROUND BLURRED AMBIENT GLOW LAYER
          ============================================================ */}
      <g filter="url(#ambientGlow)" opacity="0.4" fill="#00CCEE">
        {/* Star */}
        <polygon points="100,5 108,18 100,31 92,18" />
        {/* Shaft */}
        <rect x="96" y="30" width="8" height="150" rx="1" />
        {/* Crossbar */}
        <line x1="52" y1="46" x2="148" y2="46" stroke="#00CCEE" strokeWidth="6" strokeLinecap="round" />
        {/* Left arm */}
        <path d="M 100 210 C 65 200, 30 170, 22 120 L 10 102 L 32 112 C 42 150, 65 185, 100 196 Z" />
        {/* Right arm */}
        <path d="M 100 210 C 135 200, 170 170, 178 120 L 190 102 L 168 112 C 158 150, 135 185, 100 196 Z" />
      </g>

      {/* ============================================================
          3. MAIN CRISP EMBLEM LAYER
          ============================================================ */}

      {/* ----------------------------------------------------------
          A. TOP 4-POINT STAR FINIAL
          ---------------------------------------------------------- */}
      <polygon points="100,3 109,18 100,33 91,18" fill="url(#holoCyan)" stroke="#003355" strokeWidth="1" strokeLinejoin="round" />
      <path d="M 100 8 L 104 18 L 100 28 L 96 18 Z" fill="url(#holoHighlight)" stroke="none" />
      <circle cx="100" cy="18" r="2" fill="#FFFFFF" filter="url(#nodeGlow)" />

      {/* ----------------------------------------------------------
          B. SHORT NECK (star to crossbar)
          ---------------------------------------------------------- */}
      <rect x="96" y="33" width="8" height="10" rx="1" fill="url(#holoCyan)" stroke="#003355" strokeWidth="1" />

      {/* ----------------------------------------------------------
          C. HORIZONTAL CROSSBAR / STOCK
          ---------------------------------------------------------- */}
      {/* Main bar */}
      <rect x="52" y="42" width="96" height="8" rx="2" fill="url(#holoCyan)" stroke="#003355" strokeWidth="1" />
      {/* Left angled wing tip */}
      <polygon points="52,42 42,46 52,50" fill="url(#holoCyan)" stroke="#003355" strokeWidth="1" strokeLinejoin="round" />
      {/* Right angled wing tip */}
      <polygon points="148,42 158,46 148,50" fill="url(#holoCyan)" stroke="#003355" strokeWidth="1" strokeLinejoin="round" />
      {/* Specular highlight line */}
      <line x1="52" y1="46" x2="148" y2="46" stroke="#FFFFFF" strokeWidth="0.8" opacity="0.85" />

      {/* ----------------------------------------------------------
          D. CENTRAL VERTICAL SHAFT (full-height anchor spine + K spine)
          ---------------------------------------------------------- */}
      <rect x="96" y="43" width="8" height="153" rx="1" fill="url(#holoCyan)" stroke="#003355" strokeWidth="1" />
      {/* Center highlight line */}
      <line x1="100" y1="50" x2="100" y2="194" stroke="#FFFFFF" strokeWidth="1" opacity="0.85" />

      {/* ----------------------------------------------------------
          E. LETTER 'M' — LEFT MONOGRAM (thick angular strokes)
          ---------------------------------------------------------- */}
      <path
        d="M 34 130 
           L 34 76 
           L 67 104 
           L 95 76 
           V 90 
           L 72 114 
           L 46 92 
           V 130 Z"
        fill="url(#holoCyan)"
        stroke="#003355"
        strokeWidth="1"
        strokeLinejoin="round"
      />
      {/* M specular highlight */}
      <path d="M 34 76 L 67 104 L 95 76" stroke="#FFFFFF" strokeWidth="0.8" fill="none" opacity="0.8" />

      {/* ----------------------------------------------------------
          F. LETTER 'K' — CENTER DIAGONALS (sharp angular arms)
          ---------------------------------------------------------- */}
      {/* Upper-right diagonal */}
      <polygon
        points="105,96 132,72 140,80 112,104"
        fill="url(#holoCyan)"
        stroke="#003355"
        strokeWidth="1"
        strokeLinejoin="round"
      />
      {/* Lower-right diagonal */}
      <polygon
        points="112,104 140,128 132,136 105,112"
        fill="url(#holoCyan)"
        stroke="#003355"
        strokeWidth="1"
        strokeLinejoin="round"
      />
      {/* K specular highlights */}
      <line x1="105" y1="96" x2="132" y2="72" stroke="#FFFFFF" strokeWidth="0.8" opacity="0.8" />
      <line x1="112" y1="104" x2="140" y2="128" stroke="#FFFFFF" strokeWidth="0.8" opacity="0.8" />

      {/* ----------------------------------------------------------
          G. LETTER 'C' — RIGHT CRESCENT (bold open arc)
          ---------------------------------------------------------- */}
      <path
        d="M 162 78 
           C 130 68, 126 140, 162 130 
           L 156 140 
           C 118 152, 118 56, 156 68 Z"
        fill="url(#holoCyan)"
        stroke="#003355"
        strokeWidth="1"
        strokeLinejoin="round"
      />
      {/* C specular highlight */}
      <path d="M 162 78 C 130 68, 126 140, 162 130" stroke="#FFFFFF" strokeWidth="0.8" fill="none" opacity="0.8" />

      {/* ----------------------------------------------------------
          H. ANCHOR ARMS — SWEEPING UPWARD WITH SHARP BARBED FLUKE TIPS
          ---------------------------------------------------------- */}
      
      {/* LEFT ARM — outer sweep + barbed trident tip */}
      <path
        d="M 100 196 
           C 70 192, 38 170, 24 128 
           L 12 108 
           L 8 100 
           L 26 114 
           L 34 128 
           C 48 160, 70 180, 96 186 Z"
        fill="url(#holoCyan)"
        stroke="#003355"
        strokeWidth="1"
        strokeLinejoin="round"
      />
      {/* Left barb secondary spike */}
      <polygon points="12,108 4,94 22,108" fill="url(#holoCyan)" stroke="#003355" strokeWidth="1" strokeLinejoin="round" />
      
      {/* RIGHT ARM — outer sweep + barbed trident tip (mirrored) */}
      <path
        d="M 100 196 
           C 130 192, 162 170, 176 128 
           L 188 108 
           L 192 100 
           L 174 114 
           L 166 128 
           C 152 160, 130 180, 104 186 Z"
        fill="url(#holoCyan)"
        stroke="#003355"
        strokeWidth="1"
        strokeLinejoin="round"
      />
      {/* Right barb secondary spike */}
      <polygon points="188,108 196,94 178,108" fill="url(#holoCyan)" stroke="#003355" strokeWidth="1" strokeLinejoin="round" />

      {/* Arm inner specular highlights */}
      <path d="M 100 196 C 70 192, 38 170, 24 128 L 12 108" stroke="#FFFFFF" strokeWidth="0.8" fill="none" opacity="0.75" />
      <path d="M 100 196 C 130 192, 162 170, 176 128 L 188 108" stroke="#FFFFFF" strokeWidth="0.8" fill="none" opacity="0.75" />

      {/* ----------------------------------------------------------
          I. BOTTOM GOTHIC V-POINT CONVERGENCE
          ---------------------------------------------------------- */}
      <polygon points="100,220 86,194 114,194" fill="url(#holoCyan)" stroke="#003355" strokeWidth="1" strokeLinejoin="round" />
      <line x1="100" y1="194" x2="100" y2="220" stroke="#FFFFFF" strokeWidth="0.8" opacity="0.85" />

      {/* ============================================================
          4. STRUCTURAL INTERSECTION NODES
          ============================================================ */}
      <g filter="url(#nodeGlow)">
        {/* Star center */}
        <circle cx="100" cy="18" r="1.5" fill="#FFFFFF" />
        {/* Crossbar ends */}
        <circle cx="42" cy="46" r="2" fill="#80FFFF" stroke="#003355" strokeWidth="0.6" />
        <circle cx="158" cy="46" r="2" fill="#80FFFF" stroke="#003355" strokeWidth="0.6" />
        {/* M peak */}
        <circle cx="67" cy="104" r="2" fill="#FFFFFF" stroke="#003355" strokeWidth="0.6" />
        {/* K junction */}
        <circle cx="112" cy="104" r="2" fill="#80FFFF" stroke="#003355" strokeWidth="0.6" />
        {/* C tips */}
        <circle cx="162" cy="78" r="2" fill="#FFFFFF" stroke="#003355" strokeWidth="0.6" />
        <circle cx="162" cy="130" r="2" fill="#FFFFFF" stroke="#003355" strokeWidth="0.6" />
        {/* Left barb tip */}
        <circle cx="8" cy="100" r="2" fill="#80FFFF" stroke="#003355" strokeWidth="0.6" />
        {/* Right barb tip */}
        <circle cx="192" cy="100" r="2" fill="#80FFFF" stroke="#003355" strokeWidth="0.6" />
        {/* Bottom point */}
        <circle cx="100" cy="220" r="2.5" fill="#FFFFFF" stroke="#003355" strokeWidth="0.6" className="animate-pulse-glow" />
      </g>
    </svg>
  );
}
