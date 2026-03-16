import type { NavigationStep } from "../../types/navigation";
import ReasoningPanel from "./ReasoningPanel";
import RecoveryBadge from "./RecoveryBadge";

interface Props {
  steps: NavigationStep[];
  selectedStep: number | null;
  onSelectStep: (step: number) => void;
}

export default function StepLog({ steps, selectedStep, onSelectStep }: Props) {
  if (!steps.length) {
    return (
      <div className="text-sm text-surface-400 text-center py-8">
        Navigation steps will appear here...
      </div>
    );
  }

  return (
    <div className="space-y-2 overflow-y-auto max-h-[calc(100vh-280px)]">
      {steps.map((step) => (
        <div key={step.step_number}>
          {step.is_recovery && step.recovery_reason && (
            <RecoveryBadge reason={step.recovery_reason} />
          )}
          <button
            onClick={() => onSelectStep(step.step_number)}
            className={`w-full text-left transition-all ${
              selectedStep === step.step_number
                ? "ring-1 ring-primary-400 rounded-lg"
                : ""
            }`}
          >
            <ReasoningPanel step={step} />
          </button>
        </div>
      ))}
    </div>
  );
}
