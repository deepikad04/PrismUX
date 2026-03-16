import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  Loader2,
  Download,
  FileText,
  TrendingUp,
  ShieldAlert,
  Lightbulb,
  ChevronDown,
  ChevronUp,
  Play,
  ExternalLink,
} from "lucide-react";
import Layout from "../components/ui/Layout";
import FrictionGauge from "../components/report/FrictionGauge";
import SeverityChart from "../components/report/SeverityChart";
import StepTimeline from "../components/report/StepTimeline";
import AccessibilityBadge from "../components/report/AccessibilityBadge";
import AnnotatedScreenshots from "../components/report/AnnotatedScreenshots";
import type { FrictionReport } from "../types/navigation";

const SEVERITY_ORDER = ["critical", "high", "medium", "low"] as const;

const SEVERITY_STYLES: Record<string, { card: string; badge: string }> = {
  critical: {
    card: "border-l-4 border-l-red-500 bg-red-50/60",
    badge: "bg-red-100 text-red-800",
  },
  high: {
    card: "border-l-4 border-l-orange-400 bg-orange-50/40",
    badge: "bg-orange-100 text-orange-800",
  },
  medium: {
    card: "border-l-4 border-l-amber-400 bg-amber-50/30",
    badge: "bg-amber-100 text-amber-800",
  },
  low: {
    card: "border-l-4 border-l-blue-300 bg-blue-50/30",
    badge: "bg-blue-100 text-blue-800",
  },
};

function getRiskLabel(score: number) {
  if (score >= 80) return { text: "Poor UX", color: "text-red-600", bg: "bg-red-50" };
  if (score >= 60) return { text: "Needs Work", color: "text-orange-600", bg: "bg-orange-50" };
  if (score >= 40) return { text: "Fair", color: "text-amber-600", bg: "bg-amber-50" };
  if (score >= 20) return { text: "Good", color: "text-green-600", bg: "bg-green-50" };
  return { text: "Excellent", color: "text-emerald-600", bg: "bg-emerald-50" };
}

export default function Report() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [report, setReport] = useState<FrictionReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [pdfLoading, setPdfLoading] = useState(false);
  const [showTimeline, setShowTimeline] = useState(false);

  useEffect(() => {
    if (!sessionId) return;
    fetch(`/api/reports/${sessionId}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then(setReport)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [sessionId]);

  function downloadJSON() {
    if (!report) return;
    const blob = new Blob([JSON.stringify(report, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `prismux-report-${sessionId}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  async function downloadCSV() {
    if (!sessionId) return;
    try {
      const res = await fetch(`/api/reports/${sessionId}/csv`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `prismux-friction-${sessionId}.csv`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("CSV download failed:", err);
    }
  }

  async function downloadPDF() {
    if (!sessionId || pdfLoading) return;
    setPdfLoading(true);
    try {
      const res = await fetch(`/api/reports/${sessionId}/pdf`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `prismux-report-${sessionId}.pdf`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("PDF download failed:", err);
    } finally {
      setPdfLoading(false);
    }
  }

  if (loading) {
    return (
      <Layout>
        <div className="flex flex-col items-center justify-center py-24 gap-3">
          <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
          <span className="text-surface-600 font-medium">Analyzing session friction...</span>
          <span className="text-xs text-surface-400">This usually takes a few seconds</span>
        </div>
      </Layout>
    );
  }

  if (error || !report) {
    return (
      <Layout>
        <div className="max-w-md mx-auto px-4 py-16 text-center">
          <AlertTriangle className="w-10 h-10 text-red-400 mx-auto mb-3" />
          <p className="text-red-600 font-medium">{error || "Report not found"}</p>
          <Link to="/history" className="text-sm text-primary-600 mt-3 inline-block hover:underline">
            Back to session history
          </Link>
        </div>
      </Layout>
    );
  }

  const risk = getRiskLabel(report.ux_risk_index);
  const criticalCount = report.friction_items.filter((f) => f.severity === "critical").length;

  // Sort friction items by severity
  const sortedFriction = [...report.friction_items].sort(
    (a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity),
  );

  return (
    <Layout>
      <div className="max-w-3xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-start justify-between">
            <div>
              <h1 className="text-xl font-bold text-surface-900">UX Friction Report</h1>
              <p className="text-sm text-surface-500 mt-1 flex items-center gap-1.5">
                <ExternalLink className="w-3.5 h-3.5" />
                {report.url}
              </p>
              {report.persona && (
                <span className="inline-block mt-1.5 text-xs px-2 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200">
                  {report.persona} persona
                </span>
              )}
            </div>
            <div className="flex items-center gap-1.5 no-print">
              <button
                onClick={downloadPDF}
                disabled={pdfLoading}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
              >
                {pdfLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileText className="w-3.5 h-3.5" />}
                {pdfLoading ? "..." : "PDF"}
              </button>
              <button
                onClick={downloadCSV}
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-sm border border-surface-300 rounded-lg hover:bg-surface-50 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                CSV
              </button>
              <button
                onClick={downloadJSON}
                className="flex items-center gap-1.5 px-2.5 py-1.5 text-sm border border-surface-300 rounded-lg hover:bg-surface-50 transition-colors"
              >
                <Download className="w-3.5 h-3.5" />
                JSON
              </button>
            </div>
          </div>
        </div>

        {/* Hero score card */}
        <div className={`rounded-2xl border p-6 mb-6 ${risk.bg} border-surface-200 animate-scale-in`}>
          <div className="flex items-center gap-6">
            <div className="shrink-0">
              <FrictionGauge score={report.friction_score} />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-3 mb-1">
                <span className={`text-4xl font-black tabular-nums ${risk.color}`}>
                  {report.ux_risk_index.toFixed(0)}
                </span>
                <span className="text-sm text-surface-400">/100 risk</span>
                <span className={`text-sm font-semibold ${risk.color}`}>{risk.text}</span>
              </div>

              {/* Quick stats */}
              <div className="flex items-center gap-4 mt-2 text-sm text-surface-600">
                <span className="flex items-center gap-1">
                  {report.status === "completed" ? (
                    <CheckCircle2 className="w-4 h-4 text-green-500" />
                  ) : (
                    <AlertTriangle className="w-4 h-4 text-amber-500" />
                  )}
                  <span className="capitalize">{report.status}</span>
                </span>
                <span>{report.total_steps} steps</span>
                <span>{report.total_time_seconds.toFixed(0)}s</span>
                <span className="font-medium">
                  {report.friction_items.length} issue{report.friction_items.length !== 1 ? "s" : ""}
                  {criticalCount > 0 && (
                    <span className="text-red-600 ml-1">({criticalCount} critical)</span>
                  )}
                </span>
              </div>

              {/* Inline severity + a11y */}
              <div className="flex items-center gap-4 mt-3">
                <div className="w-32">
                  <SeverityChart items={report.friction_items} />
                </div>
                <AccessibilityBadge items={report.friction_items} />
              </div>
            </div>
          </div>
        </div>

        {/* Error classification banner */}
        {report.error_classification &&
          report.error_classification.error_type !== "none" && (
            <div className="bg-red-50 rounded-xl border border-red-200 p-4 mb-6 flex items-start gap-3">
              <ShieldAlert className="w-5 h-5 text-red-500 mt-0.5 shrink-0" />
              <div>
                <span className="text-sm font-semibold text-red-800">
                  {report.error_classification.error_type.replace("_", " ").toUpperCase()}
                </span>
                <p className="text-sm text-red-700 mt-0.5">{report.error_classification.details}</p>
                <span
                  className={`inline-block mt-1 text-xs px-2 py-0.5 rounded-full ${
                    report.error_classification.recoverable
                      ? "bg-amber-100 text-amber-800"
                      : "bg-red-100 text-red-800"
                  }`}
                >
                  {report.error_classification.recoverable ? "Recoverable" : "Non-recoverable"}
                </span>
              </div>
            </div>
          )}

        {/* Executive summary */}
        {report.executive_summary && (
          <div className="bg-white rounded-xl border border-surface-200 p-5 mb-6 shadow-sm">
            <h2 className="text-sm font-semibold text-surface-900 mb-2">Summary</h2>
            <p className="text-sm text-surface-700 leading-relaxed">{report.executive_summary}</p>
          </div>
        )}

        {/* Top priorities */}
        {report.improvement_priorities.length > 0 && (
          <div className="bg-gradient-to-br from-primary-50 to-purple-50 rounded-xl border border-primary-200 p-5 mb-8 shadow-sm">
            <h2 className="text-sm font-semibold text-primary-900 mb-3 flex items-center gap-1.5">
              <TrendingUp className="w-4 h-4 text-primary-600" />
              What to Fix First
            </h2>
            <div className="space-y-2">
              {report.improvement_priorities.map((p, i) => (
                <div key={i} className="flex items-start gap-3">
                  <span className="shrink-0 w-6 h-6 rounded-full bg-primary-600 text-white text-xs font-bold flex items-center justify-center">
                    {i + 1}
                  </span>
                  <p className="text-sm text-surface-800 pt-0.5">{p}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Friction items */}
        {sortedFriction.length > 0 && (
          <div className="mb-8">
            <h2 className="text-base font-semibold text-surface-900 mb-3">
              Issues Found ({sortedFriction.length})
            </h2>
            <div className="space-y-3">
              {sortedFriction.map((item, i) => {
                const styles = SEVERITY_STYLES[item.severity] || SEVERITY_STYLES.low;
                return (
                  <div
                    key={i}
                    className={`rounded-xl overflow-hidden ${styles.card} animate-slide-up`}
                    style={{ animationDelay: `${i * 60}ms` }}
                  >
                    <div className="p-4">
                      <div className="flex items-center gap-2 mb-1.5">
                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${styles.badge}`}>
                          {item.severity}
                        </span>
                        <span className="text-xs text-surface-500 font-medium uppercase tracking-wide">
                          {item.category}
                        </span>
                        <span className="ml-auto text-[10px] text-surface-400">Step {item.evidence_step}</span>
                      </div>
                      <p className="text-sm text-surface-800 font-medium">{item.description}</p>
                    </div>
                    {item.improvement_suggestion && (
                      <div className="px-4 py-3 bg-white/70 flex items-start gap-2">
                        <Lightbulb className="w-4 h-4 text-amber-500 shrink-0 mt-0.5" />
                        <div>
                          <span className="text-[10px] font-semibold uppercase text-amber-700 tracking-wider">Fix</span>
                          <p className="text-sm text-surface-700 mt-0.5">{item.improvement_suggestion}</p>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {sortedFriction.length === 0 && (
          <div className="text-center py-12 mb-8">
            <CheckCircle2 className="w-10 h-10 text-green-500 mx-auto mb-2" />
            <p className="text-surface-600 font-medium">No friction points detected</p>
            <p className="text-sm text-surface-400 mt-1">The navigation flow appears smooth for this goal.</p>
          </div>
        )}

        {/* Annotated screenshots */}
        {sessionId && sortedFriction.length > 0 && (
          <div className="mb-8">
            <AnnotatedScreenshots
              sessionId={sessionId}
              frictionItems={sortedFriction}
            />
          </div>
        )}

        {/* Step timeline (collapsible) */}
        <div className="mb-8">
          <button
            onClick={() => setShowTimeline((p) => !p)}
            className="flex items-center gap-2 text-sm font-semibold text-surface-700 hover:text-surface-900 transition-colors mb-3"
          >
            {showTimeline ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
            Step-by-Step Timeline ({report.step_timeline.length} steps)
          </button>
          {showTimeline && <StepTimeline steps={report.step_timeline} />}
        </div>

        {/* Actions footer */}
        <div className="flex items-center justify-center gap-3 py-4 border-t border-surface-200 no-print">
          <Link
            to={`/replay/${sessionId}`}
            className="flex items-center gap-1.5 px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Play className="w-3.5 h-3.5" />
            Watch Replay
          </Link>
          <Link
            to="/history"
            className="flex items-center gap-1.5 px-4 py-2 text-sm border border-surface-300 rounded-lg hover:bg-surface-50 transition-colors"
          >
            All Sessions
          </Link>
        </div>
      </div>
    </Layout>
  );
}
