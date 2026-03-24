// frontend/components/RiskBadge.tsx

import { cn } from "@/lib/utils";

interface RiskBadgeProps {
  level: string;
  size?: "sm" | "md";
}

const config: Record<string, { label: string; classes: string }> = {
  HIGH:    { label: "High Risk",  classes: "bg-red-50 text-red-700 border-red-200" },
  MEDIUM:  { label: "Medium",     classes: "bg-amber-50 text-amber-700 border-amber-200" },
  LOW:     { label: "Low Risk",   classes: "bg-green-50 text-green-700 border-green-200" },
  NONE:    { label: "No Risk",    classes: "bg-slate-50 text-slate-500 border-slate-200" },
};

export function RiskBadge({ level, size = "sm" }: RiskBadgeProps) {
  const c = config[level] ?? config.NONE;
  return (
    <span className={cn(
      "inline-flex items-center border rounded-full font-medium",
      size === "sm" ? "text-xs px-2 py-0.5" : "text-sm px-3 py-1",
      c.classes
    )}>
      {c.label}
    </span>
  );
}