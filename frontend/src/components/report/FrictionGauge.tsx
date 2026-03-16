import { RadialBarChart, RadialBar, PolarAngleAxis } from "recharts";

interface Props {
  score: number;
}

export default function FrictionGauge({ score }: Props) {
  const rounded = Math.round(score);
  const color =
    rounded <= 30 ? "#16a34a" : rounded <= 60 ? "#d97706" : "#dc2626";
  const label =
    rounded <= 30 ? "Low Friction" : rounded <= 60 ? "Moderate" : "High Friction";

  return (
    <div className="flex flex-col items-center">
      <div className="relative">
        <RadialBarChart
          width={180}
          height={180}
          cx={90}
          cy={90}
          innerRadius={60}
          outerRadius={80}
          barSize={12}
          data={[{ value: rounded, fill: color }]}
          startAngle={210}
          endAngle={-30}
        >
          <PolarAngleAxis
            type="number"
            domain={[0, 100]}
            angleAxisId={0}
            tick={false}
          />
          <RadialBar
            background
            dataKey="value"
            cornerRadius={6}
          />
        </RadialBarChart>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-3xl font-bold" style={{ color }}>
            {rounded}
          </span>
          <span className="text-xs text-surface-500">/100</span>
        </div>
      </div>
      <span className="text-sm font-medium mt-1" style={{ color }}>
        {label}
      </span>
    </div>
  );
}
