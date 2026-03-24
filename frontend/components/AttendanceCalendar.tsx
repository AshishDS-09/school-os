// frontend/components/AttendanceCalendar.tsx
"use client";

import { useMemo } from "react";
import { format, startOfMonth, endOfMonth,
         eachDayOfInterval, isSameDay, getDay } from "date-fns";
import { cn } from "@/lib/utils";

interface AttendanceRecord {
  date:   string;
  status: "present" | "absent" | "late" | "excused";
}

interface AttendanceCalendarProps {
  records:  AttendanceRecord[];
  month?:   Date;  // defaults to current month
}

const STATUS_DOT: Record<string, string> = {
  present: "bg-green-500",
  absent:  "bg-red-500",
  late:    "bg-amber-400",
  excused: "bg-blue-400",
};

export function AttendanceCalendar({
  records,
  month = new Date(),
}: AttendanceCalendarProps) {
  // Build lookup: "2024-11-15" → status
  const lookup = useMemo(() => {
    const map: Record<string, string> = {};
    records.forEach((r) => { map[r.date.slice(0, 10)] = r.status; });
    return map;
  }, [records]);

  const days       = eachDayOfInterval({
    start: startOfMonth(month),
    end:   endOfMonth(month),
  });
  const startDay   = getDay(startOfMonth(month)); // 0=Sun

  // Count per status for the summary row
  const counts = useMemo(() => {
    const c = { present: 0, absent: 0, late: 0, excused: 0 };
    records.forEach((r) => {
      if (r.status in c) c[r.status as keyof typeof c]++;
    });
    return c;
  }, [records]);

  return (
    <div className="bg-white border border-slate-200 rounded-xl p-4">
      {/* Month heading */}
      <div className="flex items-center justify-between mb-4">
        <p className="text-sm font-semibold text-slate-800">
          {format(month, "MMMM yyyy")}
        </p>
        {/* Legend */}
        <div className="flex items-center gap-3">
          {Object.entries(STATUS_DOT).map(([status, dot]) => (
            <div key={status} className="flex items-center gap-1">
              <div className={cn("w-2 h-2 rounded-full", dot)} />
              <span className="text-xs text-slate-400 capitalize">{status}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Day-of-week headers */}
      <div className="grid grid-cols-7 mb-1">
        {["Sun","Mon","Tue","Wed","Thu","Fri","Sat"].map((d) => (
          <div key={d} className="text-center text-xs text-slate-400 py-1">
            {d}
          </div>
        ))}
      </div>

      {/* Calendar grid */}
      <div className="grid grid-cols-7 gap-1">
        {/* Empty cells before the 1st */}
        {Array.from({ length: startDay }).map((_, i) => (
          <div key={`empty-${i}`} />
        ))}

        {days.map((day) => {
          const key    = format(day, "yyyy-MM-dd");
          const status = lookup[key];
          const isToday = isSameDay(day, new Date());

          return (
            <div
              key={key}
              className={cn(
                "relative flex flex-col items-center justify-center",
                "h-9 rounded-lg text-xs font-medium transition-colors",
                isToday
                  ? "bg-blue-50 text-blue-700 ring-1 ring-blue-300"
                  : "text-slate-700 hover:bg-slate-50",
              )}
            >
              <span>{format(day, "d")}</span>
              {status && (
                <div className={cn(
                  "w-1.5 h-1.5 rounded-full absolute bottom-1",
                  STATUS_DOT[status] ?? "bg-slate-300"
                )} />
              )}
            </div>
          );
        })}
      </div>

      {/* Summary row */}
      <div className="mt-4 pt-3 border-t border-slate-100 flex gap-4 justify-center">
        {[
          { label: "Present", count: counts.present, colour: "text-green-600" },
          { label: "Absent",  count: counts.absent,  colour: "text-red-600"   },
          { label: "Late",    count: counts.late,    colour: "text-amber-600" },
        ].map(({ label, count, colour }) => (
          <div key={label} className="text-center">
            <p className={cn("text-lg font-semibold", colour)}>{count}</p>
            <p className="text-xs text-slate-400">{label}</p>
          </div>
        ))}
      </div>
    </div>
  );
}