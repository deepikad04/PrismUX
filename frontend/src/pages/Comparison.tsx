import { useState, useEffect } from "react";
import {
  Play,
  Loader2,
  Users,
  Trophy,
  AlertTriangle,
  CheckCircle2,
  Clock,
} from "lucide-react";
import Layout from "../components/ui/Layout";
import PersonaScorecard from "../components/personas/PersonaScorecard";
import ComparisonBarChart from "../components/report/ComparisonBarChart";
import ComparisonRadar from "../components/report/ComparisonRadar";
import FrictionHeatmap from "../components/report/FrictionHeatmap";
import DivergenceView from "../components/personas/DivergenceView";
import type { ComparisonResult, PersonaConfig } from "../types/navigation";

const PERSONA_KEYS = [
  "impatient",
  "cautious",
  "accessibility",
  "non_native_english",
];

const PERSONA_DESCRIPTIONS: Record<string, string> = {
  impatient: "Rushes through, picks first CTA, low tolerance",
  cautious: "Reads everything, uses nav menus, checks security",
  accessibility: "Flags small targets, missing ARIA, poor contrast",
  non_native_english: "Confused by jargon, idioms, and complex copy",
};

export default function Comparison() {
  const [url, setUrl] = useState("");
  const [goal, setGoal] = useState("");
  const [selectedPersonas, setSelectedPersonas] = useState<string[]>([
    "impatient",
    "cautious",
  ]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<ComparisonResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [personas, setPersonas] = useState<PersonaConfig[]>([]);
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    fetch("/api/personas")
      .then((r) => r.json())
      .then(setPersonas)
      .catch(() => {});
  }, []);

  // Timer for loading state
  useEffect(() => {
    if (!loading) {
      setElapsed(0);
      return;
    }
    const t = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(t);
  }, [loading]);

  function togglePersona(key: string) {
    setSelectedPersonas((prev) =>
      prev.includes(key)
        ? prev.filter((p) => p !== key)
        : [...prev, key],
    );
  }

  async function handleCompare() {
    if (!url.trim() || !goal.trim() || selectedPersonas.length < 2) return;
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const res = await fetch("/api/personas/compare", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url: url.trim(),
          goal: goal.trim(),
          personas: selectedPersonas,
        }),
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(`HTTP ${res.status}: ${text}`);
      }
      const data = await res.json();
      if (!data.results || data.results.length === 0) {
        throw new Error("Comparison completed but no persona results were returned. Check backend logs.");
      }
      setResult(data);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Comparison failed",
      );
    } finally {
      setLoading(false);
    }
  }

  // Find best/worst persona from results
  const bestPersona = result?.results.reduce((best, r) =>
    r.ux_risk_index < best.ux_risk_index ? r : best,
  );
  const worstPersona = result?.results.reduce((worst, r) =>
    r.ux_risk_index > worst.ux_risk_index ? r : worst,
  );

  return (
    <Layout>
      <div className="max-w-5xl mx-auto px-4 py-8">
        <div className="mb-6">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <Users className="w-5 h-5 text-primary-600" />
            Persona Comparison
          </h1>
          <p className="text-surface-500 text-sm mt-1">
            Same goal, different users. See how each persona navigates and where
            they struggle.
          </p>
        </div>

        {/* Input form */}
        <div className="bg-white rounded-2xl border border-surface-200 p-6 shadow-sm space-y-4 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-surface-700 mb-1">
                Website URL
              </label>
              <input
                type="url"
                placeholder="https://example.com"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-surface-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-surface-700 mb-1">
                Navigation Goal
              </label>
              <input
                type="text"
                placeholder="Find the pricing page and sign up"
                value={goal}
                onChange={(e) => setGoal(e.target.value)}
                className="w-full px-3 py-2 rounded-lg border border-surface-300 text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-surface-700 mb-2">
              Personas ({selectedPersonas.length} selected)
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {PERSONA_KEYS.map((key) => {
                const p = personas.find((pp) => pp.key === key);
                const label = p?.name || key;
                const isSelected = selectedPersonas.includes(key);
                return (
                  <button
                    key={key}
                    onClick={() => togglePersona(key)}
                    className={`text-left px-3 py-2.5 rounded-lg border transition-all ${
                      isSelected
                        ? "border-primary-400 bg-primary-50 ring-1 ring-primary-200"
                        : "border-surface-200 hover:border-surface-300"
                    }`}
                  >
                    <span className={`text-sm font-medium ${isSelected ? "text-primary-700" : "text-surface-700"}`}>
                      {label}
                    </span>
                    <span className="block text-xs text-surface-400 mt-0.5">
                      {PERSONA_DESCRIPTIONS[key] || p?.description || ""}
                    </span>
                  </button>
                );
              })}
            </div>
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 rounded-lg px-3 py-2 flex items-center gap-2">
              <AlertTriangle className="w-4 h-4 shrink-0" />
              {error}
            </div>
          )}

          <button
            onClick={handleCompare}
            disabled={
              loading ||
              !url.trim() ||
              !goal.trim() ||
              selectedPersonas.length < 2
            }
            className="flex items-center gap-2 px-5 py-2.5 bg-gradient-to-r from-primary-600 to-primary-700 text-white rounded-xl font-medium text-sm hover:from-primary-700 hover:to-primary-800 transition-all shadow-lg shadow-primary-600/25 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            {loading ? "Running comparison..." : "Compare Personas"}
          </button>
        </div>

        {/* Loading progress */}
        {loading && (
          <div className="bg-white rounded-2xl border border-surface-200 p-6 mb-8 shadow-sm">
            <div className="flex items-center gap-3 mb-4">
              <Loader2 className="w-5 h-5 animate-spin text-primary-600" />
              <span className="text-sm font-medium text-surface-700">
                Running {selectedPersonas.length} personas sequentially...
              </span>
              <span className="text-xs text-surface-400 ml-auto flex items-center gap-1">
                <Clock className="w-3.5 h-3.5" />
                {elapsed}s
              </span>
            </div>
            <div className="space-y-2">
              {selectedPersonas.map((key, i) => {
                const p = personas.find((pp) => pp.key === key);
                const estimatedPerPersona = 45;
                const personaIdx = Math.floor(elapsed / estimatedPerPersona);
                const status =
                  i < personaIdx
                    ? "done"
                    : i === personaIdx
                      ? "running"
                      : "waiting";
                return (
                  <div
                    key={key}
                    className={`flex items-center gap-3 px-3 py-2 rounded-lg text-sm ${
                      status === "done"
                        ? "bg-green-50 text-green-700"
                        : status === "running"
                          ? "bg-primary-50 text-primary-700"
                          : "bg-surface-50 text-surface-400"
                    }`}
                  >
                    {status === "done" ? (
                      <CheckCircle2 className="w-4 h-4 text-green-500" />
                    ) : status === "running" ? (
                      <Loader2 className="w-4 h-4 animate-spin text-primary-500" />
                    ) : (
                      <Clock className="w-4 h-4" />
                    )}
                    <span className="font-medium">
                      {p?.name || key}
                    </span>
                    <span className="text-xs ml-auto">
                      {status === "done"
                        ? "Complete"
                        : status === "running"
                          ? "Navigating..."
                          : "Waiting"}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="animate-fade-in">
            {/* Winner banner */}
            {bestPersona && worstPersona && bestPersona !== worstPersona && (
              <div className="bg-gradient-to-r from-primary-50 to-purple-50 rounded-2xl border border-primary-200 p-5 mb-6">
                <div className="flex items-center gap-2 mb-2">
                  <Trophy className="w-5 h-5 text-primary-600" />
                  <h2 className="text-sm font-semibold text-primary-900">Key Insight</h2>
                </div>
                <p className="text-sm text-surface-700">
                  <strong>{bestPersona.persona_name}</strong> had the smoothest experience
                  (risk score: {bestPersona.ux_risk_index.toFixed(0)}), while{" "}
                  <strong>{worstPersona.persona_name}</strong> struggled the most
                  (risk score: {worstPersona.ux_risk_index.toFixed(0)}).
                  {worstPersona.friction_count > bestPersona.friction_count && (
                    <> The gap of{" "}
                    {worstPersona.friction_count - bestPersona.friction_count} extra
                    friction points suggests the site needs attention for{" "}
                    {worstPersona.persona_name.toLowerCase()} users.</>
                  )}
                </p>
              </div>
            )}

            {/* Persona scorecards — prominent at top */}
            <h2 className="text-base font-semibold mb-3 text-surface-900">
              Persona Results
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6 stagger-children">
              {result.results.map((r) => (
                <PersonaScorecard key={r.session_id} result={r} />
              ))}
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-6 stagger-children">
              <div className="bg-white rounded-xl border border-surface-200 p-5 shadow-sm hover-lift">
                <h3 className="text-sm font-semibold mb-4 text-surface-700">
                  Performance Radar
                </h3>
                <ComparisonRadar results={result.results} />
              </div>
              <div className="bg-white rounded-xl border border-surface-200 p-5 shadow-sm hover-lift">
                <h3 className="text-sm font-semibold mb-4 text-surface-700">
                  Metric Comparison
                </h3>
                <ComparisonBarChart results={result.results} />
              </div>
            </div>

            {/* Friction heatmap */}
            <div className="bg-white rounded-xl border border-surface-200 p-5 mb-6 shadow-sm hover-lift animate-slide-up" style={{ animationDelay: "200ms" }}>
              <h3 className="text-sm font-semibold mb-4 text-surface-700">
                Friction by Category
              </h3>
              <FrictionHeatmap results={result.results} />
            </div>

            {/* Path divergence */}
            <div className="mb-6">
              <h3 className="text-sm font-semibold mb-3 text-surface-700">
                Navigation Paths (Side by Side)
              </h3>
              <DivergenceView results={result.results} />
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
