import type { StepSummary } from "../../types/navigation";
import {
  MousePointerClick,
  Keyboard,
  ArrowDown,
  ArrowUp,
  ArrowLeft,
  Clock,
  CheckCircle2,
  Hand,
  Pause,
  type LucideIcon,
} from "lucide-react";

const ACTION_ICONS: Record<string, LucideIcon> = {
  click: MousePointerClick,
  type: Keyboard,
  scroll_down: ArrowDown,
  scroll_up: ArrowUp,
  go_back: ArrowLeft,
  wait: Clock,
  done: CheckCircle2,
  hover: Hand,
  press_key: Pause,
};

interface Props {
  steps: StepSummary[];
}

export default function StepTimeline({ steps }: Props) {
  return (
    <div className="relative">
      <div className="absolute left-5 top-0 bottom-0 w-px bg-surface-200" />

      <div className="space-y-0">
        {steps.map((step, i) => {
          const Icon = ACTION_ICONS[step.action_type] || MousePointerClick;
          const hasFriction = step.friction_detected.length > 0;

          return (
            <div
              key={step.step_number}
              className="relative flex gap-4 py-3 animate-fade-in"
              style={{ animationDelay: `${i * 50}ms` }}
            >
              <div
                className={`relative z-10 flex items-center justify-center w-10 h-10 rounded-full border-2 shrink-0 ${
                  hasFriction
                    ? "border-amber-400 bg-amber-50"
                    : step.action_type === "done"
                      ? "border-green-400 bg-green-50"
                      : "border-surface-300 bg-white"
                }`}
              >
                <Icon
                  className={`w-4 h-4 ${
                    hasFriction
                      ? "text-amber-600"
                      : step.action_type === "done"
                        ? "text-green-600"
                        : "text-surface-500"
                  }`}
                />
              </div>

              <div
                className={`flex-1 rounded-xl border p-3 ${
                  hasFriction
                    ? "border-amber-200 bg-amber-50/50"
                    : "border-surface-200 bg-white"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-mono font-semibold text-primary-600">
                      Step {step.step_number}
                    </span>
                    <span className="text-xs font-mono uppercase text-surface-500">
                      {step.action_type}
                    </span>
                    {step.target && (
                      <span className="text-xs text-surface-400 truncate max-w-[200px]">
                        &rarr; {step.target}
                      </span>
                    )}
                  </div>
                  <span className="text-xs font-mono text-surface-400">
                    {step.confidence.toFixed(2)}
                  </span>
                </div>
                {step.reasoning && (
                  <p className="text-xs text-surface-600 mt-1 leading-relaxed">
                    {step.reasoning}
                  </p>
                )}
                {hasFriction && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {step.friction_detected.map((f, j) => (
                      <span
                        key={j}
                        className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 font-medium"
                      >
                        {f}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
