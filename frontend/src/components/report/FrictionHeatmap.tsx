import type { PersonaRunResult } from "../../types/navigation";

const CATEGORIES = [
  "navigation",
  "contrast",
  "affordance",
  "copy",
  "error",
  "performance",
  "accessibility",
  "other",
];


interface Props {
  results: PersonaRunResult[];
}

/**
 * Heatmap grid: friction categories (rows) × personas (columns).
 * Cell intensity shows count; darker = more friction in that category.
 */
export default function FrictionHeatmap({ results }: Props) {
  if (results.length === 0) return null;

  // Find max count for intensity scaling
  const allCounts = results.flatMap((r) =>
    CATEGORIES.map((cat) => r.friction_by_category[cat] || 0)
  );
  const maxCount = Math.max(...allCounts, 1);

  function getIntensity(count: number): string {
    if (count === 0) return "bg-surface-50 text-surface-300";
    const ratio = count / maxCount;
    if (ratio > 0.75) return "bg-red-200 text-red-900";
    if (ratio > 0.5) return "bg-red-100 text-red-800";
    if (ratio > 0.25) return "bg-amber-100 text-amber-800";
    return "bg-amber-50 text-amber-700";
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr>
            <th className="text-left text-xs font-medium text-surface-500 uppercase tracking-wider py-2 px-3">
              Category
            </th>
            {results.map((r) => (
              <th
                key={r.persona_key}
                className="text-center text-xs font-medium text-surface-500 uppercase tracking-wider py-2 px-3"
              >
                {r.persona_name}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {CATEGORIES.map((cat) => (
            <tr key={cat} className="border-t border-surface-100">
              <td className="py-2 px-3 text-xs font-semibold text-surface-700 capitalize">
                {cat}
              </td>
              {results.map((r) => {
                const count = r.friction_by_category[cat] || 0;
                return (
                  <td key={r.persona_key} className="py-2 px-3 text-center">
                    <span
                      className={`inline-flex items-center justify-center w-8 h-8 rounded-lg text-xs font-bold ${getIntensity(count)}`}
                    >
                      {count}
                    </span>
                  </td>
                );
              })}
            </tr>
          ))}
          {/* Totals row */}
          <tr className="border-t-2 border-surface-300">
            <td className="py-2 px-3 text-xs font-bold text-surface-800">
              Total
            </td>
            {results.map((r) => (
              <td key={r.persona_key} className="py-2 px-3 text-center">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-lg text-xs font-bold bg-surface-800 text-white">
                  {r.friction_count}
                </span>
              </td>
            ))}
          </tr>
          {/* Friction score row */}
          <tr className="border-t border-surface-200">
            <td className="py-2 px-3 text-xs font-bold text-surface-800">
              Score
            </td>
            {results.map((r) => {
              const scoreColor =
                r.friction_score <= 25
                  ? "text-green-700 bg-green-50"
                  : r.friction_score <= 50
                    ? "text-amber-700 bg-amber-50"
                    : "text-red-700 bg-red-50";
              return (
                <td key={r.persona_key} className="py-2 px-3 text-center">
                  <span
                    className={`inline-flex items-center justify-center px-2 h-8 rounded-lg text-xs font-bold ${scoreColor}`}
                  >
                    {r.friction_score.toFixed(0)}
                  </span>
                </td>
              );
            })}
          </tr>
        </tbody>
      </table>
    </div>
  );
}
