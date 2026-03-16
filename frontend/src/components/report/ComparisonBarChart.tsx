import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Legend,
} from "recharts";
import type { PersonaRunResult } from "../../types/navigation";

const COLORS = ["#5c7cfa", "#f59e0b", "#10b981", "#ef4444"];

interface Props {
  results: PersonaRunResult[];
}

export default function ComparisonBarChart({ results }: Props) {
  const data = [
    {
      metric: "Steps",
      ...Object.fromEntries(
        results.map((r) => [r.persona_name, r.total_steps])
      ),
    },
    {
      metric: "Retries",
      ...Object.fromEntries(
        results.map((r) => [r.persona_name, r.retries])
      ),
    },
    {
      metric: "Backtracks",
      ...Object.fromEntries(
        results.map((r) => [r.persona_name, r.backtracks])
      ),
    },
    {
      metric: "Friction",
      ...Object.fromEntries(
        results.map((r) => [r.persona_name, r.friction_count])
      ),
    },
  ];

  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e9ecef" />
        <XAxis dataKey="metric" tick={{ fontSize: 12 }} />
        <YAxis tick={{ fontSize: 12 }} />
        <Tooltip />
        <Legend />
        {results.map((r, i) => (
          <Bar
            key={r.persona_key}
            dataKey={r.persona_name}
            fill={COLORS[i % COLORS.length]}
            radius={[4, 4, 0, 0]}
          />
        ))}
      </BarChart>
    </ResponsiveContainer>
  );
}
