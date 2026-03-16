import { PieChart, Pie, Cell, Tooltip } from "recharts";
import type { FrictionItem } from "../../types/navigation";

const SEVERITY_COLORS: Record<string, string> = {
  critical: "#dc2626",
  high: "#ef4444",
  medium: "#f59e0b",
  low: "#3b82f6",
};

interface Props {
  items: FrictionItem[];
}

export default function SeverityChart({ items }: Props) {
  const counts = items.reduce<Record<string, number>>((acc, item) => {
    acc[item.severity] = (acc[item.severity] || 0) + 1;
    return acc;
  }, {});

  const data = Object.entries(counts).map(([severity, count]) => ({
    name: severity,
    value: count,
  }));

  if (data.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-full text-surface-400 text-sm">
        No issues
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center">
      <PieChart width={140} height={140}>
        <Pie
          data={data}
          cx={70}
          cy={70}
          innerRadius={35}
          outerRadius={55}
          dataKey="value"
          strokeWidth={2}
        >
          {data.map((entry) => (
            <Cell
              key={entry.name}
              fill={SEVERITY_COLORS[entry.name] || "#94a3b8"}
            />
          ))}
        </Pie>
        <Tooltip />
      </PieChart>
      <div className="flex flex-wrap gap-2 mt-2 justify-center">
        {data.map((d) => (
          <span
            key={d.name}
            className="flex items-center gap-1 text-xs text-surface-600"
          >
            <span
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: SEVERITY_COLORS[d.name] }}
            />
            {d.name} ({d.value})
          </span>
        ))}
      </div>
    </div>
  );
}
