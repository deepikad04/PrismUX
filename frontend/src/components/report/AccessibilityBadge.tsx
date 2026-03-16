import { Shield, ShieldCheck, ShieldAlert } from "lucide-react";
import type { FrictionItem } from "../../types/navigation";

interface Props {
  items: FrictionItem[];
}

export default function AccessibilityBadge({ items }: Props) {
  const a11yIssues = items.filter(
    (item) => item.category === "accessibility"
  );
  const count = a11yIssues.length;

  const grade =
    count === 0 ? "AAA" : count <= 2 ? "AA" : "Needs Work";
  const color =
    count === 0
      ? "text-green-600 bg-green-50 border-green-200"
      : count <= 2
        ? "text-amber-600 bg-amber-50 border-amber-200"
        : "text-red-600 bg-red-50 border-red-200";
  const Icon =
    count === 0 ? ShieldCheck : count <= 2 ? Shield : ShieldAlert;

  return (
    <div className="flex flex-col items-center gap-2">
      <div
        className={`w-16 h-16 rounded-full border-2 flex items-center justify-center ${color}`}
      >
        <Icon className="w-7 h-7" />
      </div>
      <span className={`text-lg font-bold ${color.split(" ")[0]}`}>
        {grade}
      </span>
      <span className="text-xs text-surface-500">
        {count === 0
          ? "No a11y issues"
          : `${count} a11y issue${count > 1 ? "s" : ""}`}
      </span>
    </div>
  );
}
