import type { PersonaRunResult } from "../../types/navigation";

const OUTCOME_COLORS: Record<string, string> = {
  completed: "text-green-700",
  abandoned: "text-red-600",
  blocked: "text-amber-600",
  error: "text-red-600",
};

const ACTION_ICONS: Record<string, string> = {
  click: "pointer",
  type: "keyboard",
  scroll_down: "arrow-down",
  scroll_up: "arrow-up",
  done: "check",
  go_back: "arrow-left",
  hover: "hand",
  wait: "clock",
  press_key: "key",
};

const PERSONA_COLORS = [
  { bg: "bg-blue-50", border: "border-blue-300", dot: "bg-blue-500", text: "text-blue-700" },
  { bg: "bg-purple-50", border: "border-purple-300", dot: "bg-purple-500", text: "text-purple-700" },
  { bg: "bg-emerald-50", border: "border-emerald-300", dot: "bg-emerald-500", text: "text-emerald-700" },
  { bg: "bg-amber-50", border: "border-amber-300", dot: "bg-amber-500", text: "text-amber-700" },
];

interface Props {
  results: PersonaRunResult[];
}

export default function DivergenceView({ results }: Props) {
  if (!results.length) return null;

  const maxSteps = Math.max(...results.map((r) => r.path.length));

  return (
    <div className="space-y-4">
      {/* Risk Index headline row */}
      <div className="flex gap-3">
        {results.map((r, pi) => {
          const colors = PERSONA_COLORS[pi % PERSONA_COLORS.length];
          return (
            <div
              key={r.session_id}
              className={`flex-1 ${colors.bg} rounded-xl border ${colors.border} p-4 text-center`}
            >
              <div className={`text-3xl font-black tabular-nums ${
                r.ux_risk_index >= 70 ? "text-red-600" :
                r.ux_risk_index >= 40 ? "text-amber-600" :
                "text-green-600"
              }`}>
                {r.ux_risk_index.toFixed(0)}
              </div>
              <div className={`text-sm font-semibold ${colors.text} mt-1`}>
                {r.persona_name}
              </div>
              <div className={`text-xs mt-0.5 ${OUTCOME_COLORS[r.outcome] || "text-surface-500"}`}>
                {r.outcome}
              </div>
            </div>
          );
        })}
      </div>

      {/* Verdicts */}
      <div className="space-y-2">
        {results.map((r, pi) => {
          const colors = PERSONA_COLORS[pi % PERSONA_COLORS.length];
          return (
            <div
              key={r.session_id}
              className={`flex items-center gap-3 ${colors.bg} rounded-lg px-4 py-2 border ${colors.border}`}
            >
              <div className={`w-2 h-2 rounded-full ${colors.dot} shrink-0`} />
              <span className={`text-xs font-semibold ${colors.text} min-w-[120px]`}>
                {r.persona_name}
              </span>
              <span className="text-xs text-surface-700">{r.verdict}</span>
            </div>
          );
        })}
      </div>

      {/* Side-by-side path timeline */}
      <div className="bg-white rounded-xl border border-surface-200 overflow-hidden shadow-sm">
        <div className="grid border-b border-surface-200" style={{ gridTemplateColumns: `60px repeat(${results.length}, 1fr)` }}>
          <div className="px-3 py-2 text-[10px] font-semibold text-surface-400 uppercase tracking-wider">
            Step
          </div>
          {results.map((r, pi) => {
            const colors = PERSONA_COLORS[pi % PERSONA_COLORS.length];
            return (
              <div
                key={r.session_id}
                className={`px-3 py-2 text-xs font-semibold ${colors.text} border-l border-surface-200`}
              >
                {r.persona_name}
              </div>
            );
          })}
        </div>

        {Array.from({ length: maxSteps }, (_, stepIdx) => (
          <div
            key={stepIdx}
            className={`grid border-b border-surface-100 ${stepIdx % 2 === 0 ? "bg-surface-50/50" : ""}`}
            style={{ gridTemplateColumns: `60px repeat(${results.length}, 1fr)` }}
          >
            <div className="px-3 py-1.5 text-xs font-mono text-surface-400 flex items-center">
              {stepIdx}
            </div>
            {results.map((r) => {
              const pathStep = r.path[stepIdx];
              if (!pathStep) {
                return (
                  <div
                    key={r.session_id}
                    className="px-3 py-1.5 border-l border-surface-100 text-xs text-surface-300 italic"
                  >
                    {stepIdx === r.path.length && r.outcome !== "completed" ? "abandoned" : ""}
                  </div>
                );
              }
              return (
                <div
                  key={r.session_id}
                  className={`px-3 py-1.5 border-l border-surface-100 text-xs ${
                    pathStep.friction ? "bg-red-50/60" : ""
                  }`}
                >
                  <span className="font-mono text-surface-500">
                    {ACTION_ICONS[pathStep.action] ? pathStep.action : pathStep.action}
                  </span>
                  {pathStep.target && (
                    <span className="text-surface-700 ml-1">
                      {pathStep.target.length > 25
                        ? pathStep.target.slice(0, 22) + "..."
                        : pathStep.target}
                    </span>
                  )}
                  {pathStep.friction && (
                    <span className="ml-1 text-red-500 font-bold" title="Friction detected">
                      !
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
}
