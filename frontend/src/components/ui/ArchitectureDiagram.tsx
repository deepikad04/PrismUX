/**
 * Interactive SVG architecture diagram showing the PrismUX system.
 * Animated arrows and color-coded layers for visual impact.
 */
export default function ArchitectureDiagram() {
  return (
    <svg
      viewBox="0 0 900 620"
      className="w-full max-w-4xl mx-auto"
      xmlns="http://www.w3.org/2000/svg"
    >
      <defs>
        {/* Gradients */}
        <linearGradient id="grad-frontend" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#818cf8" />
        </linearGradient>
        <linearGradient id="grad-backend" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#2563eb" />
          <stop offset="100%" stopColor="#3b82f6" />
        </linearGradient>
        <linearGradient id="grad-cloud" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#059669" />
          <stop offset="100%" stopColor="#10b981" />
        </linearGradient>
        <linearGradient id="grad-arrow" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#6366f1" />
          <stop offset="100%" stopColor="#2563eb" />
        </linearGradient>
        {/* Arrow marker */}
        <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill="#6366f1" />
        </marker>
        <marker id="arrowhead-green" markerWidth="10" markerHeight="7" refX="10" refY="3.5" orient="auto">
          <polygon points="0 0, 10 3.5, 0 7" fill="#059669" />
        </marker>
        {/* Icon symbols */}
        <symbol id="ico-eye" viewBox="0 0 24 24">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          <circle cx="12" cy="12" r="3" fill="currentColor" opacity="0.5" />
        </symbol>
        <symbol id="ico-lightbulb" viewBox="0 0 24 24">
          <path d="M12 2a7 7 0 00-4 12.7V17h8v-2.3A7 7 0 0012 2z" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          <line x1="9" y1="21" x2="15" y2="21" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" />
        </symbol>
        <symbol id="ico-cursor" viewBox="0 0 24 24">
          <path d="M5 3v16l4-4 3 6h3l-3-6h6z" fill="currentColor" />
        </symbol>
        <symbol id="ico-check" viewBox="0 0 24 24">
          <path d="M4 12l5 5L20 6" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
        </symbol>
        <symbol id="ico-cloud" viewBox="0 0 24 24">
          <path d="M18 10h-1.26A8 8 0 109 20h9a5 5 0 000-10z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </symbol>
        <symbol id="ico-database" viewBox="0 0 24 24">
          <ellipse cx="12" cy="5" rx="9" ry="3" fill="none" stroke="currentColor" strokeWidth="2" />
          <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" fill="none" stroke="currentColor" strokeWidth="2" />
          <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" fill="none" stroke="currentColor" strokeWidth="2" />
        </symbol>
        <symbol id="ico-box" viewBox="0 0 24 24">
          <path d="M21 16V8a2 2 0 00-1-1.73l-7-4a2 2 0 00-2 0l-7 4A2 2 0 003 8v8a2 2 0 001 1.73l7 4a2 2 0 002 0l7-4A2 2 0 0021 16z" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M3.27 6.96L12 12.01l8.73-5.05M12 22.08V12" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
        </symbol>
        <symbol id="ico-sparkle" viewBox="0 0 24 24">
          <path d="M12 3l1.5 5.5L19 10l-5.5 1.5L12 17l-1.5-5.5L5 10l5.5-1.5z" fill="currentColor" opacity="0.3" stroke="currentColor" strokeWidth="1.5" strokeLinejoin="round" />
          <path d="M19 15l.5 2 2 .5-2 .5-.5 2-.5-2-2-.5 2-.5z" fill="currentColor" />
        </symbol>
        <symbol id="ico-activity" viewBox="0 0 24 24">
          <path d="M22 12h-4l-3 9L9 3l-3 9H2" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
        </symbol>
      </defs>

      {/* ======= FRONTEND LAYER ======= */}
      <rect x="40" y="20" width="820" height="130" rx="16" fill="url(#grad-frontend)" opacity="0.1" stroke="#6366f1" strokeWidth="2" />
      <text x="60" y="50" fontSize="14" fontWeight="700" fill="#6366f1" fontFamily="system-ui">FRONTEND</text>
      <text x="160" y="50" fontSize="11" fill="#6366f1" opacity="0.7" fontFamily="system-ui">React 19 + TypeScript + Tailwind CSS v4</text>

      {/* Frontend boxes */}
      {[
        { x: 60, label: "Home", sub: "URL + Goal Input" },
        { x: 220, label: "Session", sub: "Live Navigation" },
        { x: 380, label: "ThoughtStream", sub: "PPAE Thoughts" },
        { x: 540, label: "Report", sub: "Friction Analysis" },
        { x: 700, label: "Compare", sub: "Multi-Persona" },
      ].map((box) => (
        <g key={box.label}>
          <rect x={box.x} y="65" width="140" height="60" rx="10" fill="white" stroke="#6366f1" strokeWidth="1.5" />
          <text x={box.x + 70} y="90" textAnchor="middle" fontSize="12" fontWeight="600" fill="#4338ca" fontFamily="system-ui">{box.label}</text>
          <text x={box.x + 70} y="108" textAnchor="middle" fontSize="9" fill="#6366f1" opacity="0.7" fontFamily="system-ui">{box.sub}</text>
        </g>
      ))}

      {/* ======= Animated arrows: Frontend → Backend ======= */}
      <line x1="290" y1="150" x2="290" y2="185" stroke="#6366f1" strokeWidth="2" markerEnd="url(#arrowhead)" strokeDasharray="6 3">
        <animate attributeName="stroke-dashoffset" from="18" to="0" dur="1.5s" repeatCount="indefinite" />
      </line>
      <text x="300" y="172" fontSize="9" fill="#6366f1" fontFamily="monospace">SSE</text>

      <line x1="610" y1="150" x2="610" y2="185" stroke="#6366f1" strokeWidth="2" markerEnd="url(#arrowhead)" strokeDasharray="6 3">
        <animate attributeName="stroke-dashoffset" from="18" to="0" dur="1.5s" repeatCount="indefinite" />
      </line>
      <text x="620" y="172" fontSize="9" fill="#6366f1" fontFamily="monospace">REST</text>

      {/* ======= BACKEND LAYER ======= */}
      <rect x="40" y="190" width="820" height="210" rx="16" fill="url(#grad-backend)" opacity="0.1" stroke="#2563eb" strokeWidth="2" />
      <text x="60" y="220" fontSize="14" fontWeight="700" fill="#2563eb" fontFamily="system-ui">BACKEND</text>
      <text x="160" y="220" fontSize="11" fill="#2563eb" opacity="0.7" fontFamily="system-ui">FastAPI + Google ADK + Playwright</text>

      {/* Backend core: PPAE loop */}
      <rect x="60" y="240" width="360" height="140" rx="12" fill="white" stroke="#2563eb" strokeWidth="1.5" />
      <text x="240" y="265" textAnchor="middle" fontSize="12" fontWeight="700" fill="#1e40af" fontFamily="system-ui">PPAE Navigation Loop</text>

      {/* PPAE phases */}
      {[
        { x: 80, label: "Perceive", color: "#3b82f6", icon: "ico-eye" },
        { x: 175, label: "Plan", color: "#8b5cf6", icon: "ico-lightbulb" },
        { x: 260, label: "Act", color: "#2563eb", icon: "ico-cursor" },
        { x: 340, label: "Evaluate", color: "#059669", icon: "ico-check" },
      ].map((phase) => (
        <g key={phase.label}>
          <rect x={phase.x} y="280" width="70" height="45" rx="8" fill={phase.color} opacity="0.15" stroke={phase.color} strokeWidth="1" />
          <use href={`#${phase.icon}`} x={phase.x + 27} y="284" width="16" height="16" style={{ color: phase.color }} />
          <text x={phase.x + 35} y="316" textAnchor="middle" fontSize="9" fontWeight="600" fill={phase.color} fontFamily="system-ui">{phase.label}</text>
        </g>
      ))}

      {/* PPAE arrows */}
      <line x1="152" y1="302" x2="172" y2="302" stroke="#6366f1" strokeWidth="1.5" markerEnd="url(#arrowhead)">
        <animate attributeName="stroke-dashoffset" from="8" to="0" dur="0.8s" repeatCount="indefinite" />
      </line>
      <line x1="247" y1="302" x2="257" y2="302" stroke="#6366f1" strokeWidth="1.5" markerEnd="url(#arrowhead)">
        <animate attributeName="stroke-dashoffset" from="8" to="0" dur="0.8s" repeatCount="indefinite" />
      </line>
      <line x1="332" y1="302" x2="337" y2="302" stroke="#6366f1" strokeWidth="1.5" markerEnd="url(#arrowhead)">
        <animate attributeName="stroke-dashoffset" from="8" to="0" dur="0.8s" repeatCount="indefinite" />
      </line>

      {/* Loop arrow back */}
      <path d="M 375 330 Q 375 360 240 360 Q 80 360 80 330" fill="none" stroke="#6366f1" strokeWidth="1" strokeDasharray="4 2" markerEnd="url(#arrowhead)">
        <animate attributeName="stroke-dashoffset" from="24" to="0" dur="2s" repeatCount="indefinite" />
      </path>
      <text x="230" y="372" textAnchor="middle" fontSize="8" fill="#6366f1" fontFamily="monospace">loop until goal</text>

      {/* Backend services */}
      {[
        { x: 450, y: 240, w: 180, label: "Google ADK Agent", sub: "LlmAgent + LoopAgent", color: "#2563eb" },
        { x: 450, y: 310, w: 180, label: "Persona Engine", sub: "4 personas × friction lens", color: "#7c3aed" },
        { x: 660, y: 240, w: 180, label: "Gemini Vision", sub: "2.0 Flash (multimodal)", color: "#dc2626" },
        { x: 660, y: 310, w: 180, label: "Playwright Browser", sub: "Headless Chromium", color: "#0891b2" },
      ].map((svc) => (
        <g key={svc.label}>
          <rect x={svc.x} y={svc.y} width={svc.w} height="55" rx="10" fill="white" stroke={svc.color} strokeWidth="1.5" />
          <text x={svc.x + svc.w / 2} y={svc.y + 25} textAnchor="middle" fontSize="11" fontWeight="600" fill={svc.color} fontFamily="system-ui">{svc.label}</text>
          <text x={svc.x + svc.w / 2} y={svc.y + 42} textAnchor="middle" fontSize="9" fill={svc.color} opacity="0.7" fontFamily="system-ui">{svc.sub}</text>
        </g>
      ))}

      {/* ======= Animated arrows: Backend → Cloud ======= */}
      <line x1="290" y1="400" x2="290" y2="440" stroke="#059669" strokeWidth="2" markerEnd="url(#arrowhead-green)" strokeDasharray="6 3">
        <animate attributeName="stroke-dashoffset" from="18" to="0" dur="1.5s" repeatCount="indefinite" />
      </line>
      <line x1="540" y1="400" x2="540" y2="440" stroke="#059669" strokeWidth="2" markerEnd="url(#arrowhead-green)" strokeDasharray="6 3">
        <animate attributeName="stroke-dashoffset" from="18" to="0" dur="1.5s" repeatCount="indefinite" />
      </line>
      <line x1="750" y1="400" x2="750" y2="440" stroke="#059669" strokeWidth="2" markerEnd="url(#arrowhead-green)" strokeDasharray="6 3">
        <animate attributeName="stroke-dashoffset" from="18" to="0" dur="1.5s" repeatCount="indefinite" />
      </line>

      {/* ======= GOOGLE CLOUD LAYER ======= */}
      <rect x="40" y="450" width="820" height="150" rx="16" fill="url(#grad-cloud)" opacity="0.1" stroke="#059669" strokeWidth="2" />
      <text x="60" y="480" fontSize="14" fontWeight="700" fill="#059669" fontFamily="system-ui">GOOGLE CLOUD</text>
      <text x="210" y="480" fontSize="11" fill="#059669" opacity="0.7" fontFamily="system-ui">Cloud Run + Managed Services</text>

      {/* Cloud services */}
      {[
        { x: 60, label: "Cloud Run", sub: "Container hosting", icon: "ico-cloud" },
        { x: 240, label: "Firestore", sub: "Session storage", icon: "ico-database" },
        { x: 420, label: "Cloud Storage", sub: "Screenshots (GCS)", icon: "ico-box" },
        { x: 600, label: "Gemini API", sub: "Vision + Language", icon: "ico-sparkle" },
        { x: 750, label: "Cloud Logging", sub: "Observability", icon: "ico-activity" },
      ].map((svc) => (
        <g key={svc.label}>
          <rect x={svc.x} y="495" width="140" height="75" rx="10" fill="white" stroke="#059669" strokeWidth="1.5" />
          <use href={`#${svc.icon}`} x={svc.x + 60} y="508" width="20" height="20" style={{ color: "#059669" }} />
          <text x={svc.x + 70} y="545" textAnchor="middle" fontSize="11" fontWeight="600" fill="#047857" fontFamily="system-ui">{svc.label}</text>
          <text x={svc.x + 70} y="560" textAnchor="middle" fontSize="9" fill="#059669" opacity="0.7" fontFamily="system-ui">{svc.sub}</text>
        </g>
      ))}
    </svg>
  );
}
