// frontend/components/StatCard.tsx

import { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";

interface StatCardProps {
  label:    string;
  value:    string | number;
  icon:     LucideIcon;
  iconBg:   string;    // e.g. "bg-blue-50"
  iconColor:string;    // e.g. "text-blue-600"
  sub?:     string;    // small grey subtitle below value
  loading?: boolean;
  trend?:   "up" | "down" | "neutral";
}

export function StatCard({
  label, value, icon: Icon, iconBg, iconColor, sub, loading, trend,
}: StatCardProps) {
  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4">
      <div className="flex items-start justify-between mb-3">
        <p className="text-xs text-slate-500 leading-tight">{label}</p>
        <div className={cn("w-8 h-8 rounded-lg flex items-center justify-center shrink-0", iconBg)}>
          <Icon className={cn("w-4 h-4", iconColor)} />
        </div>
      </div>

      {loading ? (
        <Skeleton className="h-7 w-24 mb-1" />
      ) : (
        <p className="text-2xl font-semibold text-slate-800 leading-none mb-1">
          {value}
        </p>
      )}

      {sub && (
        <p className={cn(
          "text-xs mt-1",
          trend === "up"   ? "text-green-600" :
          trend === "down" ? "text-red-500"   : "text-slate-400"
        )}>
          {trend === "up" ? "↑ " : trend === "down" ? "↓ " : ""}{sub}
        </p>
      )}
    </div>
  );
}