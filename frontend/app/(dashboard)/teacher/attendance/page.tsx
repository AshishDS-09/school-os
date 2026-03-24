"use client";

import { useQuery } from "@tanstack/react-query";
import { Topbar } from "@/components/Topbar";
import { AttendanceGrid } from "@/components/AttendanceGrid";
import { studentsApi } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

export default function TeacherAttendancePage() {
  const { data: students, isLoading } = useQuery({
    queryKey: ["students", "active"],
    queryFn: () => studentsApi.list({ is_active: true }).then((r) => r.data),
  });

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <Topbar
        title="Attendance"
        subtitle="Mark attendance and save to trigger attendance agent activity"
      />

      <div className="flex-1 overflow-auto p-4 sm:p-6">
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3, 4, 5].map((i) => (
              <Skeleton key={i} className="h-12 w-full" />
            ))}
          </div>
        ) : (
          <AttendanceGrid students={students ?? []} />
        )}
      </div>
    </div>
  );
}
