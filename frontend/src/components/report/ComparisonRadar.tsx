import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { PersonaRunResult } from "../../types/navigation";

const COLORS = ["#5c7cfa", "#f59e0b", "#10b981", "#ef4444"];

interface Props {
  results: PersonaRunResult[];
}

/**
 * Radar chart comparing persona performance across multiple dimensions.
 * Normalizes each metric to 0-100 scale for visual comparison.
 */
export default function ComparisonRadar({ results }: Props) {
  if (results.length === 0) return null;

  // Compute max values for normalization
  const maxSteps = Math.max(...results.map((r) => r.total_steps), 1);
  const maxTime = Math.max(...results.map((r) => r.time_seconds), 1);
  const maxFriction = Math.max(...results.map((r) => r.friction_count), 1);
  const maxRetries = Math.max(...results.map((r) => r.retries), 1);
  const maxScore = Math.max(...results.map((r) => r.friction_score), 1);

  const dimensions = [
    { key: "Steps", extract: (r: PersonaRunResult) => (r.total_steps / maxSteps) * 100 },
    { key: "Time", extract: (r: PersonaRunResult) => (r.time_seconds / maxTime) * 100 },
    { key: "Friction", extract: (r: PersonaRunResult) => (r.friction_count / maxFriction) * 100 },
    { key: "Retries", extract: (r: PersonaRunResult) => (r.retries / maxRetries) * 100 },
    { key: "Score", extract: (r: PersonaRunResult) => (r.friction_score / maxScore) * 100 },
  ];

  const data = dimensions.map((dim) => {
    const point: Record<string, string | number> = { dimension: dim.key };
    results.forEach((r) => {
      point[r.persona_name] = Math.round(dim.extract(r));
    });
    return point;
  });

  return (
    <ResponsiveContainer width="100%" height={320}>
      <RadarChart data={data} cx="50%" cy="50%" outerRadius="75%">
        <PolarGrid stroke="#e5e7eb" />
        <PolarAngleAxis dataKey="dimension" tick={{ fontSize: 11, fill: "#6b7280" }} />
        <PolarRadiusAxis angle={90} domain={[0, 100]} tick={false} axisLine={false} />
        {results.map((r, i) => (
          <Radar
            key={r.persona_key}
            name={r.persona_name}
            dataKey={r.persona_name}
            stroke={COLORS[i % COLORS.length]}
            fill={COLORS[i % COLORS.length]}
            fillOpacity={0.15}
            strokeWidth={2}
          />
        ))}
        <Legend />
      </RadarChart>
    </ResponsiveContainer>
  );
}
