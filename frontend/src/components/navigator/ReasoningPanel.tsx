import type { NavigationStep, FrictionCategory } from "../../types/navigation";
import { Brain, MousePointerClick, Keyboard, ArrowDown, ArrowUp, ArrowLeft, Clock, CheckCircle2 } from "lucide-react";

const ACTION_ICONS: Record<string, typeof Brain> = {
  click: MousePointerClick,
  type: Keyboard,
  scroll_down: ArrowDown,
  scroll_up: ArrowUp,
  go_back: ArrowLeft,
  wait: Clock,
  done: CheckCircle2,
};

const FRICTION_COLORS: Record<FrictionCategory, string> = {
  navigation: "bg-blue-50 text-blue-700",
  contrast: "bg-purple-50 text-purple-700",
  affordance: "bg-orange-50 text-orange-700",
  copy: "bg-yellow-50 text-yellow-700",
  error: "bg-red-50 text-red-700",
  performance: "bg-cyan-50 text-cyan-700",
  accessibility: "bg-pink-50 text-pink-700",
};

interface Props {
  step: NavigationStep;
}

export default function ReasoningPanel({ step }: Props) {
  const Icon = ACTION_ICONS[step.plan.action_type] || Brain;

  return (
    <div className="bg-white rounded-lg border border-surface-200 p-3 animate-slide-up">
      <div className="flex items-start gap-2">
        <div className="mt-0.5 p-1.5 rounded-md bg-primary-50">
          <Icon className="w-3.5 h-3.5 text-primary-600" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs font-mono font-medium text-primary-700 uppercase">
              {step.plan.action_type}
            </span>
            {step.plan.target_element && (
              <span className="text-xs text-surface-500 truncate">
                → {step.plan.target_element}
              </span>
            )}
            {step.plan.input_text && (
              <span className="text-xs text-surface-500 font-mono truncate">
                "{step.plan.input_text}"
              </span>
            )}
          </div>
          <p className="text-sm text-surface-700 mt-1 leading-relaxed">
            {step.plan.reasoning}
          </p>
          {/* Page understanding block */}
          {step.perception && (step.perception.page_purpose || step.perception.page_description) && (
            <div className="mt-2 p-2 rounded bg-blue-50 border border-blue-100">
              <span className="text-[10px] font-mono font-semibold text-blue-600 uppercase">Page Understanding</span>
              {step.perception.page_purpose && (
                <p className="text-xs text-blue-700 mt-0.5">{step.perception.page_purpose}</p>
              )}
              <p className="text-xs text-blue-600 mt-0.5 opacity-70 truncate">{step.perception.page_description}</p>
              <span className="text-[10px] text-blue-500 font-mono">
                {step.perception.elements?.length || 0} elements
                {step.perception.has_modal_or_overlay && " · modal detected"}
                {step.perception.loading_state && " · loading"}
              </span>
            </div>
          )}
          {step.evaluation && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {step.evaluation.progress_made && (
                <span className="text-xs px-1.5 py-0.5 rounded bg-green-50 text-green-700">
                  Progress
                </span>
              )}
              {step.evaluation.goal_achieved && (
                <span className="text-xs px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 font-medium">
                  Goal Achieved
                </span>
              )}
              {step.evaluation.friction_items?.length ? (
                step.evaluation.friction_items.map((f, i) => (
                  <span
                    key={i}
                    className={`text-xs px-1.5 py-0.5 rounded ${FRICTION_COLORS[f.category] || "bg-gray-50 text-gray-700"}`}
                    title={`${f.severity} severity`}
                  >
                    <span className="font-semibold">{f.category}</span>: {f.description}
                  </span>
                ))
              ) : (
                step.evaluation.friction_detected?.map((f, i) => (
                  <span
                    key={i}
                    className="text-xs px-1.5 py-0.5 rounded bg-amber-50 text-amber-700"
                  >
                    {f}
                  </span>
                ))
              )}
            </div>
          )}
        </div>
        <div className="text-xs font-mono text-surface-400">
          {step.plan.confidence.toFixed(2)}
        </div>
      </div>
    </div>
  );
}
