// frontend/components/AttendanceGrid.tsx
"use client";

import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { attendanceApi } from "@/lib/api";
import { useToast } from "@/components/ui/use-toast";
import { Button } from "@/components/ui/button";
import { Badge }  from "@/components/ui/badge";
import { Loader2, CheckCircle2, XCircle, Clock } from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth-store";
import { emitLocalAgentLog } from "@/lib/local-agent-log";

interface Student {
  id:          number;
  first_name:  string;
  last_name:   string;
  roll_number: string;
  class_id:    number;
}

type AttendanceStatus = "present" | "absent" | "late";

interface AttendanceState {
  [studentId: number]: AttendanceStatus;
}

const buildAttendanceState = (students: Student[], status: AttendanceStatus): AttendanceState =>
  students.reduce<AttendanceState>((acc, student) => {
    acc[student.id] = status;
    return acc;
  }, {});

const STATUS_CONFIG = {
  present: {
    label:  "Present",
    icon:   CheckCircle2,
    colour: "bg-green-50 border-green-300 text-green-700",
    active: "bg-green-500 text-white border-green-500",
  },
  absent: {
    label:  "Absent",
    icon:   XCircle,
    colour: "bg-red-50 border-red-300 text-red-700",
    active: "bg-red-500 text-white border-red-500",
  },
  late: {
    label:  "Late",
    icon:   Clock,
    colour: "bg-amber-50 border-amber-300 text-amber-700",
    active: "bg-amber-500 text-white border-amber-500",
  },
} as const;

export function AttendanceGrid({ students }: { students: Student[] }) {
  const { toast }  = useToast();
  const qc         = useQueryClient();
  const { user }   = useAuthStore();
  const now        = new Date();
  const today      = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;

  // Track status per student — default everyone to "present"
  const [attendance, setAttendance] = useState<AttendanceState>(
    () => buildAttendanceState(students, "present")
  );
  const [submitting, setSubmitting] = useState(false);

  const setStatus = (studentId: number, status: AttendanceStatus) => {
    setAttendance((prev) => ({ ...prev, [studentId]: status }));
  };

  // Mark all present at once
  const markAllPresent = () => {
    setAttendance(buildAttendanceState(students, "present"));
  };

  const submitAttendance = async () => {
    setSubmitting(true);
    let success = 0;
    let failed  = 0;

    // Submit one by one — API processes them sequentially
    for (const student of students) {
      try {
        await attendanceApi.mark({
          student_id: student.id,
          class_id:   student.class_id,
          date:       today,
          status:     attendance[student.id] ?? "present",
        });
        success++;
      } catch {
        failed++;
      }
    }

    setSubmitting(false);
    qc.invalidateQueries({ queryKey: ["attendance"] });

    const absentCount = Object.values(attendance).filter((s) => s === "absent").length;
    if (user?.school_id && success > 0) {
      emitLocalAgentLog(user.school_id, {
        agent_name: "attendance_agent",
        trigger: "attendance_saved",
        action_taken:
          absentCount >= 3
            ? `HIGH absences detected: ${absentCount} students marked absent.`
            : `Attendance saved for ${success} students.`,
        outcome: "success",
        duration_ms: null,
        cost_usd: 0,
      });
    }

    if (failed === 0) {
      toast({
        title:       "Attendance saved",
        description: `${success} students marked for ${today}`,
      });
    } else {
      toast({
        title:       "Partially saved",
        description: `${success} saved, ${failed} failed`,
        variant:     "destructive",
      });
    }
  };

  // Counts for summary
  const counts = {
    present: Object.values(attendance).filter((s) => s === "present").length,
    absent:  Object.values(attendance).filter((s) => s === "absent").length,
    late:    Object.values(attendance).filter((s) => s === "late").length,
  };

  return (
    <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
      {/* Header */}
      <div className="flex flex-col gap-3 px-4 py-3 border-b border-slate-100
                      lg:flex-row lg:items-center lg:justify-between">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:gap-4">
          <p className="text-sm font-medium text-slate-700">
            {today} - {students.length} students
          </p>
          <div className="flex flex-wrap gap-2">
            <Badge variant="outline" className="text-xs bg-green-50 text-green-700
                                                border-green-200">
              {counts.present} present
            </Badge>
            <Badge variant="outline" className="text-xs bg-red-50 text-red-700
                                                border-red-200">
              {counts.absent} absent
            </Badge>
            {counts.late > 0 && (
              <Badge variant="outline" className="text-xs bg-amber-50
                                                  text-amber-700 border-amber-200">
                {counts.late} late
              </Badge>
            )}
          </div>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="outline"
            size="sm"
            className="text-xs h-7"
            onClick={markAllPresent}
          >
            All present
          </Button>
          <Button
            size="sm"
            className="text-xs h-7 bg-blue-600 hover:bg-blue-700"
            onClick={submitAttendance}
            disabled={submitting}
          >
            {submitting && (
              <Loader2 className="w-3 h-3 mr-1.5 animate-spin" />
            )}
            Save attendance
          </Button>
        </div>
      </div>

      {/* Student rows */}
      <div className="divide-y divide-slate-50">
        {students.map((student) => {
          const current = attendance[student.id] ?? "present";
          return (
            <div
              key={student.id}
              className="flex flex-col gap-3 px-4 py-3 hover:bg-slate-50
                         transition-colors sm:flex-row sm:items-center
                         sm:justify-between"
            >
              {/* Student info */}
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-full bg-blue-50 flex items-center
                                justify-center text-xs font-semibold text-blue-600">
                  {student.first_name.charAt(0)}
                </div>
                <div>
                  <p className="text-sm font-medium text-slate-800">
                    {student.first_name} {student.last_name}
                  </p>
                  <p className="text-xs text-slate-400">
                    Roll #{student.roll_number}
                  </p>
                </div>
              </div>

              {/* Status buttons */}
              <div className="flex flex-wrap gap-1.5 sm:justify-end">
                {(
                  Object.entries(STATUS_CONFIG) as [
                    AttendanceStatus,
                    (typeof STATUS_CONFIG)[AttendanceStatus]
                  ][]
                ).map(([status, config]) => (
                  <button
                    key={status}
                    onClick={() => setStatus(student.id, status)}
                    className={cn(
                      "px-3 py-1 text-xs rounded-lg border font-medium",
                      "transition-all duration-150",
                      current === status
                        ? config.active
                        : "bg-white border-slate-200 text-slate-500 hover:border-slate-300"
                    )}
                  >
                    {config.label}
                  </button>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
