import type { ReactNode } from "react";
import { Link, useLocation } from "react-router-dom";

function PrismLogo() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none" className="shrink-0">
      {/* Prism triangle */}
      <polygon
        points="14,3 25,24 3,24"
        fill="url(#prism-fill)"
        stroke="url(#prism-stroke)"
        strokeWidth="1.5"
      />
      {/* Refracted light beams */}
      <line x1="18" y1="14" x2="26" y2="10" stroke="#ef4444" strokeWidth="1.5" opacity="0.8" />
      <line x1="19" y1="16" x2="27" y2="16" stroke="#22c55e" strokeWidth="1.5" opacity="0.8" />
      <line x1="18" y1="18" x2="26" y2="22" stroke="#3b82f6" strokeWidth="1.5" opacity="0.8" />
      {/* Incoming light */}
      <line x1="1" y1="16" x2="9" y2="16" stroke="white" strokeWidth="1.5" opacity="0.6" />
      <defs>
        <linearGradient id="prism-fill" x1="3" y1="24" x2="25" y2="3">
          <stop offset="0%" stopColor="#7c3aed" stopOpacity="0.2" />
          <stop offset="100%" stopColor="#a78bfa" stopOpacity="0.3" />
        </linearGradient>
        <linearGradient id="prism-stroke" x1="3" y1="24" x2="25" y2="3">
          <stop offset="0%" stopColor="#7c3aed" />
          <stop offset="100%" stopColor="#a78bfa" />
        </linearGradient>
      </defs>
    </svg>
  );
}

const NAV_LINKS = [
  { to: "/", label: "Home" },
  { to: "/history", label: "History" },
  { to: "/compare", label: "Compare" },
];

const TECH_BADGES = [
  "Gemini 2.0 Flash",
  "Google ADK",
  "Playwright",
  "React 19",
  "FastAPI",
  "Tailwind v4",
];

export default function Layout({ children }: { children: ReactNode }) {
  const location = useLocation();

  return (
    <div className="min-h-screen flex flex-col bg-gradient-to-br from-surface-50 via-white to-primary-50/30">
      {/* Top accent bar */}
      <div className="h-1 bg-gradient-to-r from-primary-500 via-purple-500 to-primary-600 animate-gradient" />

      {/* Header */}
      <header className="sticky top-0 z-50 glass border-b border-surface-200/50">
        <div className="max-w-7xl mx-auto px-4 h-14 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 font-bold text-lg group">
            <PrismLogo />
            <span className="bg-gradient-to-r from-primary-700 via-purple-600 to-primary-500 bg-clip-text text-transparent">
              PrismUX
            </span>
          </Link>
          <nav className="flex items-center gap-1">
            {NAV_LINKS.map((link) => {
              const isActive =
                link.to === "/"
                  ? location.pathname === "/"
                  : location.pathname.startsWith(link.to);
              return (
                <Link
                  key={link.to}
                  to={link.to}
                  className={`relative px-3 py-1.5 rounded-lg text-sm font-medium transition-all ${
                    isActive
                      ? "text-primary-700"
                      : "text-surface-600 hover:text-surface-900 hover:bg-surface-100"
                  }`}
                >
                  {link.label}
                  {isActive && (
                    <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-4/5 h-0.5 bg-gradient-to-r from-primary-500 to-purple-500 rounded-full" />
                  )}
                </Link>
              );
            })}
          </nav>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1">{children}</main>

      {/* Footer */}
      <footer className="border-t border-surface-200/50 bg-white/50 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 py-8">
          {/* Tech badges */}
          <div className="flex flex-wrap items-center justify-center gap-2 mb-4">
            <span className="text-xs text-surface-500 mr-1">Built with</span>
            {TECH_BADGES.map((tech) => (
              <span
                key={tech}
                className="px-2.5 py-1 rounded-full bg-surface-100 text-[11px] font-medium text-surface-600 border border-surface-200"
              >
                {tech}
              </span>
            ))}
          </div>
          {/* Tagline + hackathon badge */}
          <div className="flex flex-col items-center gap-2">
            <div className="flex items-center gap-2">
              <PrismLogo />
              <span className="text-sm font-semibold bg-gradient-to-r from-primary-700 to-purple-600 bg-clip-text text-transparent">
                PrismUX
              </span>
              <span className="text-xs text-surface-400">
                AI-Powered UX Testing
              </span>
            </div>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-gradient-to-r from-primary-50 to-purple-50 border border-primary-200 text-[11px] font-medium text-primary-700">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" />
              </svg>
              Gemini Live Agent Challenge 2026
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
