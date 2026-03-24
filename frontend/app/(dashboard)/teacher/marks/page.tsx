"use client";

import { useQuery } from "@tanstack/react-query";
import { Topbar } from "@/components/Topbar";
import { MarksEntry } from "@/components/MarksEntry";
import { studentsApi } from "@/lib/api";
import { Skeleton } from "@/components/ui/skeleton";

export default function TeacherMarksPage() {
  const { data: students, isLoading } = useQuery({
    queryKey: ["students", "active"],
    queryFn: () => studentsApi.list({ is_active: true }).then((r) => r.data),
  });

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <Topbar
        title="Marks"
        subtitle="Enter student marks and trigger academic agent checks"
      />

      <div className="flex-1 overflow-auto p-4 sm:p-6">
        {isLoading ? (
          <Skeleton className="h-64 w-full" />
        ) : (
          <MarksEntry students={students ?? []} />
        )}
      </div>
    </div>
  );
}
