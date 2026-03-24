"use client";

import { useQuery } from "@tanstack/react-query";
import { Topbar } from "@/components/Topbar";
import { studentsApi } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

interface Student {
  id: number;
  first_name: string;
  last_name: string;
  roll_number: string;
  class_id: number;
}

export default function TeacherStudentsPage() {
  const { data: students, isLoading } = useQuery({
    queryKey: ["students", "active"],
    queryFn: () => studentsApi.list({ is_active: true }).then((r) => r.data as Student[]),
  });

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <Topbar
        title="Students"
        subtitle="View active students in your school"
      />

      <div className="flex-1 overflow-auto p-4 sm:p-6">
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <Skeleton key={i} className="h-14 w-full" />
            ))}
          </div>
        ) : (
          <div className="overflow-hidden rounded-xl border border-slate-200 bg-white">
            <div className="divide-y divide-slate-100">
              {(students ?? []).map((student) => (
                <div
                  key={student.id}
                  className="flex items-center justify-between px-4 py-3"
                >
                  <div>
                    <p className="text-sm font-medium text-slate-800">
                      {student.first_name} {student.last_name}
                    </p>
                    <p className="text-xs text-slate-500">
                      Roll #{student.roll_number}
                    </p>
                  </div>
                  <span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs text-blue-700">
                    Class {student.class_id}
                  </span>
                </div>
              ))}
              {(students ?? []).length === 0 && (
                <p className="px-4 py-6 text-center text-sm text-slate-400">
                  No active students found
                </p>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
