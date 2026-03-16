import { useEffect, useRef } from "react";
import { Eye, Brain, MousePointerClick, CheckCircle2 } from "lucide-react";
import type { ThoughtEvent } from "../../types/navigation";

const PHASE_CONFIG: Record<
  string,
  { icon: typeof Eye; color: string; bg: string }
> = {
  perceive: { icon: Eye, color: "text-blue-600", bg: "bg-blue-50" },
  plan: { icon: Brain, color: "text-purple-600", bg: "bg-purple-50" },
  act: { icon: MousePointerClick, color: "text-primary-600", bg: "bg-primary-50" },
  evaluate: { icon: CheckCircle2, color: "text-green-600", bg: "bg-green-50" },
};

interface Props {
  thoughts: ThoughtEvent[];
}

export default function ThoughtStream({ thoughts }: Props) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [thoughts.length]);

  if (!thoughts.length) {
    return (
      <div className="text-sm text-surface-400 text-center py-8 font-mono">
        Agent thoughts will stream here...
      </div>
    );
  }

  return (
    <div className="space-y-1 overflow-y-auto max-h-[calc(100vh-280px)] pr-1">
      {thoughts.map((t, i) => {
        const config = PHASE_CONFIG[t.phase] || PHASE_CONFIG.perceive;
        const Icon = config.icon;
        const isFriction =
          t.message.toLowerCase().includes("friction") ||
          (t.data?.friction_count && Number(t.data.friction_count) > 0);

        return (
          <div
            key={i}
            className={`flex items-start gap-2 px-2 py-1.5 rounded-lg animate-fade-in ${
              isFriction ? "bg-amber-50 border border-amber-200" : ""
            }`}
            style={{ animationDelay: `${Math.min(i * 30, 300)}ms` }}
          >
            <div className={`mt-0.5 p-1 rounded ${config.bg} shrink-0`}>
              <Icon className={`w-3 h-3 ${config.color}`} />
            </div>
            <div className="min-w-0 flex-1">
              <span className={`text-[10px] font-mono uppercase font-semibold ${config.color}`}>
                {t.phase}
              </span>
              <p className="text-xs text-surface-700 leading-relaxed font-mono">
                {t.message}
              </p>
            </div>
          </div>
        );
      })}
      <div ref={endRef} />
    </div>
  );
}
