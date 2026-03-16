import { AlertTriangle } from "lucide-react";

interface Props {
  reason: string;
}

export default function RecoveryBadge({ reason }: Props) {
  return (
    <div className="flex items-center gap-2 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2 animate-slide-up">
      <div className="p-1 rounded-full bg-amber-100">
        <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
      </div>
      <div>
        <div className="text-xs font-medium text-amber-800">
          Recovery Triggered
        </div>
        <div className="text-xs text-amber-600">{reason}</div>
      </div>
    </div>
  );
}
