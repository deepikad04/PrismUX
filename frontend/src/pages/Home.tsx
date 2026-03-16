import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import {
  Play,
  Zap,
  ArrowRight,
  Eye,
  Users,
  AlertTriangle,
  Brain,
  GitCompareArrows,
  FileText,
  Clock,
  Layers,
} from "lucide-react";
import Layout from "../components/ui/Layout";
import PersonaSelector from "../components/personas/PersonaSelector";

/* ─── PPAE Steps ─── */
const PPAE_STEPS = [
  {
    icon: Eye,
    title: "Perceive",
    desc: "AI vision analyzes the screenshot, detecting every element and bounding box",
    color: "text-blue-600",
    bg: "bg-blue-100",
    ring: "ring-blue-200",
  },
  {
    icon: Brain,
    title: "Plan",
    desc: "Picks the best action from candidates and reasons about the navigation path",
    color: "text-purple-600",
    bg: "bg-purple-100",
    ring: "ring-purple-200",
  },
  {
    icon: Play,
    title: "Act",
    desc: "Executes clicks, scrolls, and text input through Playwright automation",
    color: "text-primary-600",
    bg: "bg-primary-100",
    ring: "ring-primary-200",
  },
  {
    icon: AlertTriangle,
    title: "Evaluate",
    desc: "Measures progress toward the goal and detects friction, accessibility issues",
    color: "text-amber-600",
    bg: "bg-amber-100",
    ring: "ring-amber-200",
  },
];

/* ─── Feature Cards ─── */
const FEATURES = [
  {
    icon: Eye,
    title: "AI Vision Analysis",
    desc: "Gemini detects every UI element, bounding box, and accessibility issue in a single multimodal API call.",
    accent: "border-l-blue-500",
    iconColor: "text-blue-600",
    iconBg: "bg-blue-50",
  },
  {
    icon: Users,
    title: "Persona-Based Testing",
    desc: "4 built-in personas plus a custom builder evaluate friction through different user lenses.",
    accent: "border-l-purple-500",
    iconColor: "text-purple-600",
    iconBg: "bg-purple-50",
  },
  {
    icon: Brain,
    title: "Live Thought Stream",
    desc: "Watch the AI think in real-time as it perceives, plans, acts, and evaluates during navigation.",
    accent: "border-l-green-500",
    iconColor: "text-green-600",
    iconBg: "bg-green-50",
  },
  {
    icon: AlertTriangle,
    title: "Friction Detection",
    desc: "Categorized findings with severity levels, measured evidence, and actionable improvement suggestions.",
    accent: "border-l-amber-500",
    iconColor: "text-amber-600",
    iconBg: "bg-amber-50",
  },
  {
    icon: GitCompareArrows,
    title: "Before / After Comparison",
    desc: "Spatial friction markers on screenshots show exactly where usability issues occur.",
    accent: "border-l-cyan-500",
    iconColor: "text-cyan-600",
    iconBg: "bg-cyan-50",
  },
  {
    icon: FileText,
    title: "Export Reports",
    desc: "Generate stakeholder-ready PDF, CSV, and JSON reports with one click.",
    accent: "border-l-red-500",
    iconColor: "text-red-600",
    iconBg: "bg-red-50",
  },
];

/* ─── Stats ─── */
const STATS = [
  { value: "7", label: "App Pages", icon: Layers },
  { value: "4+", label: "Personas", icon: Users },
  { value: "7", label: "Friction Categories", icon: AlertTriangle },
  { value: "88", label: "Tests", icon: FileText },
];

/* ─── Rotating keywords ─── */
const KEYWORDS = [
  "navigation issues",
  "accessibility gaps",
  "copy confusion",
  "small tap targets",
  "low contrast text",
];

function useRotatingKeyword(words: string[], intervalMs = 2500) {
  const [idx, setIdx] = useState(0);
  useEffect(() => {
    const timer = setInterval(() => setIdx((i) => (i + 1) % words.length), intervalMs);
    return () => clearInterval(timer);
  }, [words.length, intervalMs]);
  return words[idx];
}

/* ─── Intersection Observer hook ─── */
function useInView(threshold = 0.2) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const obs = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setVisible(true); },
      { threshold },
    );
    obs.observe(el);
    return () => obs.disconnect();
  }, [threshold]);
  return { ref, visible };
}

/* ─── Main Component ─── */
export default function Home() {
  const navigate = useNavigate();
  const [url, setUrl] = useState("");
  const [goal, setGoal] = useState("");
  const [persona, setPersona] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const keyword = useRotatingKeyword(KEYWORDS);

  const howItWorks = useInView();
  const features = useInView();
  const stats = useInView();

  async function handleStart() {
    if (!url.trim() || !goal.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url.trim(), goal: goal.trim(), persona }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `HTTP ${res.status}`);
      }
      const session = await res.json();
      navigate(`/session/${session.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create session");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Layout>
      {/* ═══════ SECTION 1: HERO ═══════ */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-600 via-primary-500 to-purple-700 animate-gradient" />
        <div className="absolute inset-0 bg-grid" />
        {/* Floating orbs */}
        <div className="absolute top-10 left-10 w-72 h-72 bg-white/10 rounded-full blur-3xl animate-float" />
        <div className="absolute bottom-10 right-10 w-96 h-96 bg-purple-300/20 rounded-full blur-3xl animate-float" style={{ animationDelay: "1.5s" }} />

        {/* Prism SVG decoration */}
        <div className="absolute right-[10%] top-1/2 -translate-y-1/2 opacity-20 animate-float hidden lg:block" style={{ animationDelay: "0.5s" }}>
          <svg width="200" height="200" viewBox="0 0 200 200" fill="none">
            <polygon points="100,10 190,170 10,170" stroke="white" strokeWidth="2" fill="none" />
            <line x1="130" y1="80" x2="190" y2="60" stroke="#ef4444" strokeWidth="2" opacity="0.8" />
            <line x1="135" y1="95" x2="195" y2="95" stroke="#22c55e" strokeWidth="2" opacity="0.8" />
            <line x1="130" y1="110" x2="190" y2="130" stroke="#3b82f6" strokeWidth="2" opacity="0.8" />
            <line x1="5" y1="95" x2="70" y2="95" stroke="white" strokeWidth="2" opacity="0.5" />
          </svg>
        </div>

        <div className="relative max-w-3xl mx-auto px-4 py-24 text-center text-white">
          <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-white/15 text-sm font-medium mb-6 backdrop-blur-sm border border-white/20">
            <svg width="16" height="16" viewBox="0 0 28 28" fill="none">
              <polygon points="14,3 25,24 3,24" fill="none" stroke="white" strokeWidth="2" />
              <line x1="18" y1="14" x2="26" y2="10" stroke="#ef4444" strokeWidth="1.5" />
              <line x1="19" y1="16" x2="27" y2="16" stroke="#22c55e" strokeWidth="1.5" />
              <line x1="18" y1="18" x2="26" y2="22" stroke="#3b82f6" strokeWidth="1.5" />
            </svg>
            AI-Powered UX Testing Agent
          </div>
          <h1 className="text-5xl md:text-6xl font-bold tracking-tight leading-tight">
            Find friction
            <br />
            <span className="text-primary-200">before your users do</span>
          </h1>
          <p className="mt-5 text-lg text-white/80 max-w-lg mx-auto leading-relaxed">
            PrismUX uses AI vision to navigate your UI as different personas,
            detecting{" "}
            <span className="text-white font-semibold inline-block min-w-[160px] text-left transition-all duration-300">
              {keyword}
            </span>{" "}
            in real-time.
          </p>

          {/* Scroll hint */}
          <div className="mt-10 flex flex-col items-center gap-1 text-white/40">
            <span className="text-xs">Scroll to explore</span>
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" className="animate-bounce">
              <path d="M5 8l5 5 5-5" />
            </svg>
          </div>
        </div>
      </div>

      {/* ═══════ SECTION 2: HOW IT WORKS ═══════ */}
      <div ref={howItWorks.ref} className="max-w-5xl mx-auto px-4 py-20">
        <div className="text-center mb-12">
          <h2 className="text-3xl font-bold text-surface-900">How It Works</h2>
          <p className="text-surface-500 mt-2">The PPAE loop runs autonomously on every page</p>
        </div>
        <div className={`grid grid-cols-1 md:grid-cols-4 gap-6 relative ${howItWorks.visible ? "stagger-children" : ""}`}>
          {/* Connector line (desktop only) */}
          <svg className="absolute top-12 left-0 w-full h-1 hidden md:block pointer-events-none" preserveAspectRatio="none">
            <line
              x1="12.5%" y1="50%" x2="87.5%" y2="50%"
              stroke="#e9ecef"
              strokeWidth="2"
              strokeDasharray="8 4"
              className={howItWorks.visible ? "animate-dash-draw" : ""}
            />
          </svg>
          {PPAE_STEPS.map((step, i) => (
            <div key={step.title} className="flex flex-col items-center text-center relative">
              <div className={`w-16 h-16 rounded-2xl ${step.bg} ring-4 ${step.ring} flex items-center justify-center mb-4 relative z-10 bg-white`}>
                <span className="absolute -top-2 -right-2 w-6 h-6 rounded-full bg-surface-800 text-white text-xs font-bold flex items-center justify-center">
                  {i + 1}
                </span>
                <step.icon className={`w-7 h-7 ${step.color}`} />
              </div>
              <h3 className="font-semibold text-surface-900">{step.title}</h3>
              <p className="text-sm text-surface-500 mt-1 max-w-[200px]">{step.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* ═══════ SECTION 3: FEATURES ═══════ */}
      <div className="bg-surface-50/80 border-y border-surface-200/50">
        <div ref={features.ref} className="max-w-5xl mx-auto px-4 py-20">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-surface-900">Everything You Need</h2>
            <p className="text-surface-500 mt-2">From live agent navigation to stakeholder-ready reports</p>
          </div>
          <div className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 ${features.visible ? "stagger-children" : ""}`}>
            {FEATURES.map((f) => (
              <div
                key={f.title}
                className={`bg-white rounded-xl border border-surface-200 border-l-4 ${f.accent} p-5 hover-lift`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <div className={`p-2 rounded-lg ${f.iconBg}`}>
                    <f.icon className={`w-5 h-5 ${f.iconColor}`} />
                  </div>
                  <h3 className="font-semibold text-surface-800">{f.title}</h3>
                </div>
                <p className="text-sm text-surface-500 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ═══════ SECTION 4: STATS ═══════ */}
      <div ref={stats.ref} className="max-w-4xl mx-auto px-4 py-16">
        <div className={`grid grid-cols-2 md:grid-cols-4 gap-4 ${stats.visible ? "stagger-children" : ""}`}>
          {STATS.map((s) => (
            <div key={s.label} className="text-center bg-white rounded-xl border border-surface-200 p-6 hover-lift">
              <div className="flex justify-center mb-2">
                <s.icon className="w-5 h-5 text-primary-400" />
              </div>
              <div className={`text-4xl font-black text-primary-700 tabular-nums ${stats.visible ? "animate-number-pop" : "opacity-0"}`}>
                {s.value}
              </div>
              <div className="text-xs text-surface-500 uppercase tracking-wider mt-1 font-medium">
                {s.label}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* ═══════ SECTION 5: TECH STACK ═══════ */}
      <div className="text-center pb-12">
        <p className="text-xs text-surface-400 uppercase tracking-widest font-medium mb-3">Powered By</p>
        <div className="flex flex-wrap justify-center gap-3 max-w-2xl mx-auto px-4">
          {["Gemini 2.5 Flash", "Google ADK", "Playwright", "React 19", "FastAPI", "Tailwind v4", "Firestore"].map((tech) => (
            <span
              key={tech}
              className="px-3 py-1.5 rounded-full bg-white border border-surface-200 text-xs font-medium text-surface-600 shadow-sm"
            >
              {tech}
            </span>
          ))}
        </div>
      </div>

      {/* ═══════ SECTION 6: FORM CARD ═══════ */}
      <div className="max-w-2xl mx-auto px-4 pb-12">
        <div className="text-center mb-6">
          <h2 className="text-2xl font-bold text-surface-900">Try It Now</h2>
          <p className="text-surface-500 text-sm mt-1">Enter any URL and goal to start an AI navigation session</p>
        </div>
        <div className="glass rounded-2xl p-6 space-y-5 shadow-xl shadow-primary-900/5 prism-border">
          <div>
            <label htmlFor="url" className="block text-sm font-medium text-surface-700 mb-1.5">
              Website URL
            </label>
            <input
              id="url"
              type="url"
              placeholder="https://example.com"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-surface-300 bg-white/80 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 placeholder:text-surface-400"
            />
          </div>
          <div>
            <label htmlFor="goal" className="block text-sm font-medium text-surface-700 mb-1.5">
              Navigation Goal
            </label>
            <textarea
              id="goal"
              rows={2}
              placeholder="Find the pricing page and locate the free trial signup button"
              value={goal}
              onChange={(e) => setGoal(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl border border-surface-300 bg-white/80 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 placeholder:text-surface-400 resize-none"
            />
          </div>

          <PersonaSelector selected={persona} onSelect={setPersona} />

          {error && (
            <div className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={handleStart}
              disabled={loading || !url.trim() || !goal.trim()}
              className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-gradient-to-r from-primary-600 to-purple-600 text-white rounded-xl font-medium text-sm hover:from-primary-700 hover:to-purple-700 transition-all shadow-lg shadow-primary-600/25 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <Play className="w-4 h-4" />
              )}
              {loading ? "Creating session..." : "Start Navigation"}
            </button>
            <button
              onClick={() => {
                setUrl("http://demo-site:80");
                setGoal("Find the pricing page and sign up for a free trial");
              }}
              className="flex items-center gap-2 px-4 py-3 bg-amber-50 text-amber-700 border border-amber-200 rounded-xl font-medium text-sm hover:bg-amber-100 transition-all"
            >
              <Zap className="w-4 h-4" />
              Try Demo
            </button>
          </div>
        </div>
      </div>

      {/* ═══════ SECTION 7: QUICK LINKS ═══════ */}
      <div className="max-w-3xl mx-auto px-4 pb-16">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-xl mx-auto">
          {[
            { to: "/compare", icon: Users, label: "Compare Personas", desc: "Run multiple personas side by side" },
            { to: "/history", icon: Clock, label: "Session History", desc: "Review past navigation sessions" },
          ].map((link) => (
            <button
              key={link.to}
              onClick={() => navigate(link.to)}
              className="flex items-center gap-3 p-4 bg-white rounded-xl border border-surface-200 text-left hover-lift group"
            >
              <div className="p-2 rounded-lg bg-surface-50 group-hover:bg-primary-50 transition-colors">
                <link.icon className="w-5 h-5 text-surface-400 group-hover:text-primary-600 transition-colors" />
              </div>
              <div>
                <div className="text-sm font-semibold text-surface-800 flex items-center gap-1">
                  {link.label}
                  <ArrowRight className="w-3.5 h-3.5 text-surface-400 group-hover:text-primary-600 transition-transform group-hover:translate-x-0.5" />
                </div>
                <div className="text-xs text-surface-500">{link.desc}</div>
              </div>
            </button>
          ))}
        </div>
      </div>
    </Layout>
  );
}
