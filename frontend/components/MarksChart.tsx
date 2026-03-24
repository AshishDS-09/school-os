// frontend/components/MarksChart.tsx
"use client";

import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine,
} from "recharts";
import { format } from "date-fns";

interface Mark {
  id:         number;
  subject:    string;
  exam_type:  string;
  exam_date:  string;
  score:      number;
  max_score:  number;
  percentage: number;
}

interface MarksChartProps {
  marks:   Mark[];
  subject?: string;   // filter to one subject if provided
}

// Colour per subject
const SUBJECT_COLOURS: Record<string, string> = {
  Mathematics:      "#3B82F6",
  Science:          "#10B981",
  English:          "#8B5CF6",
  Hindi:            "#F59E0B",
  "Social Studies": "#EF4444",
  "Computer Science":"#06B6D4",
  Physics:          "#F97316",
  Chemistry:        "#84CC16",
  Biology:          "#EC4899",
};

function getColour(subject: string): string {
  return SUBJECT_COLOURS[subject] ?? "#94A3B8";
}

// Custom tooltip
function CustomTooltip({ active, payload, label }: {
  active?: boolean;
  payload?: { name: string; value: number; color: string }[];
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-slate-200 rounded-lg shadow-sm p-3">
      <p className="text-xs text-slate-500 mb-1">{label}</p>
      {payload.map((p) => (
        <div key={p.name} className="flex items-center gap-2">
          <div
            className="w-2 h-2 rounded-full"
            style={{ background: p.color }}
          />
          <span className="text-xs font-medium text-slate-700">
            {p.name}: {p.value}%
          </span>
        </div>
      ))}
    </div>
  );
}

export function MarksChart({ marks, subject }: MarksChartProps) {
  // Group by date → subject → percentage
  const filtered = subject
    ? marks.filter((m) => m.subject === subject)
    : marks;

  if (filtered.length === 0) {
    return (
      <div className="flex items-center justify-center h-40 text-sm text-slate-400">
        No marks data available yet.
      </div>
    );
  }

  // Get unique subjects from filtered marks
  const subjects = [...new Set(filtered.map((m) => m.subject))];

  // Build chart data: one row per unique exam date
  const dateMap: Record<string, Record<string, number>> = {};
  filtered.forEach((m) => {
    const d = m.exam_date.slice(0, 10);
    if (!dateMap[d]) dateMap[d] = {};
    dateMap[d][m.subject] = Math.round(m.percentage);
  });

  const chartData = Object.entries(dateMap)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([date, subjectScores]) => ({
      date:  format(new Date(date), "dd MMM"),
      ...subjectScores,
    }));

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4">
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-semibold text-slate-800">
          Performance Trend
        </p>
        {/* Subject colour legend */}
        <div className="flex flex-wrap gap-3 justify-end">
          {subjects.map((s) => (
            <div key={s} className="flex items-center gap-1">
              <div
                className="w-2 h-2 rounded-full"
                style={{ background: getColour(s) }}
              />
              <span className="text-xs text-slate-500">{s}</span>
            </div>
          ))}
        </div>
      </div>

      <ResponsiveContainer width="100%" height={220}>
        <LineChart data={chartData} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
          <XAxis
            dataKey="date"
            tick={{ fontSize: 11, fill: "#94A3B8" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            domain={[0, 100]}
            tick={{ fontSize: 11, fill: "#94A3B8" }}
            axisLine={false}
            tickLine={false}
          />
          {/* Pass mark reference line */}
          <ReferenceLine
            y={40}
            stroke="#FCA5A5"
            strokeDasharray="4 4"
            label={{ value: "Pass", fontSize: 10, fill: "#F87171", position: "right" }}
          />
          <Tooltip content={<CustomTooltip />} />
          {subjects.map((s) => (
            <Line
              key={s}
              type="monotone"
              dataKey={s}
              stroke={getColour(s)}
              strokeWidth={2}
              dot={{ r: 3, fill: getColour(s) }}
              activeDot={{ r: 5 }}
              connectNulls
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}