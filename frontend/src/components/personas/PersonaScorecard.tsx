import type { PersonaRunResult } from "../../types/navigation";
import { Link } from "react-router-dom";
import { ExternalLink } from "lucide-react";

const OUTCOME_COLORS: Record<string, string> = {
  completed: "text-green-700 bg-green-50",
  abandoned: "text-red-700 bg-red-50",
  blocked: "text-amber-700 bg-amber-50",
};

const OUTCOME_ACCENT: Record<string, string> = {
  completed: "border-t-green-400",
  abandoned: "border-t-red-400",
  blocked: "border-t-amber-400",
};

interface Props {
  result: PersonaRunResult;
}

export default function PersonaScorecard({ result }: Props) {
  const outcomeColor =
    OUTCOME_COLORS[result.outcome] || "text-surface-700 bg-surface-50";
  const accentColor =
    OUTCOME_ACCENT[result.outcome] || "border-t-surface-400";
  const maxFriction = 10;
  const frictionWidth = Math.min(
    (result.friction_count / maxFriction) * 100,
    100
  );

  return (
    <div
      className={`bg-white rounded-xl border border-surface-200 border-t-2 ${accentColor} p-4 shadow-sm animate-fade-in`}
    >
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-sm">{result.persona_name}</h3>
        <div className="flex items-center gap-2">
          <span className={`text-lg font-black tabular-nums ${
            result.ux_risk_index >= 70 ? "text-red-600" :
            result.ux_risk_index >= 40 ? "text-amber-600" :
            "text-green-600"
          }`}>
            {result.ux_risk_index.toFixed(0)}
          </span>
          <span
            className={`text-xs font-medium px-2 py-0.5 rounded-full ${outcomeColor}`}
          >
            {result.outcome}
          </span>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-y-2 gap-x-4 text-sm">
        <div className="flex justify-between">
          <span className="text-surface-500">Steps</span>
          <span className="font-mono font-medium">{result.total_steps}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-surface-500">Retries</span>
          <span className="font-mono font-medium">{result.retries}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-surface-500">Backtracks</span>
          <span className="font-mono font-medium">{result.backtracks}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-surface-500">Time</span>
          <span className="font-mono font-medium">
            {result.time_seconds.toFixed(1)}s
          </span>
        </div>
      </div>
      {/* Friction bar */}
      <div className="mt-3 pt-3 border-t border-surface-100">
        <div className="flex items-center justify-between text-sm mb-1">
          <span className="text-surface-500">Friction</span>
          <span className="font-mono font-medium text-amber-600">
            {result.friction_count}
          </span>
        </div>
        <div className="h-1.5 bg-surface-100 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-amber-400 to-red-500 rounded-full transition-all duration-500"
            style={{ width: `${frictionWidth}%` }}
          />
        </div>
      </div>
      <div className="mt-3 pt-3 border-t border-surface-100">
        <Link
          to={`/report/${result.session_id}`}
          className="text-xs text-primary-600 hover:text-primary-700 flex items-center gap-1"
        >
          View Full Report <ExternalLink className="w-3 h-3" />
        </Link>
      </div>
    </div>
  );
}
