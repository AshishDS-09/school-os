// frontend/app/(dashboard)/teacher/page.tsx
"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Topbar } from "@/components/Topbar";
import { AttendanceGrid } from "@/components/AttendanceGrid";
import { MarksEntry } from "@/components/MarksEntry";
import { studentsApi } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { Skeleton } from "@/components/ui/skeleton";

export default function TeacherDashboard() {
  const { user } = useAuthStore();
  const [tab, setTab] = useState("attendance");
  const today = new Date();
  const academicYearStart =
    today.getMonth() >= 3 ? today.getFullYear() : today.getFullYear() - 1;
  const academicYearLabel = `${academicYearStart}-${String(
    (academicYearStart + 1) % 100
  ).padStart(2, "0")}`;
  const mobileLinks = [
    { href: "/teacher", label: "Dashboard" },
    { href: "/teacher/attendance", label: "Attendance" },
    { href: "/teacher/marks", label: "Marks" },
    { href: "/teacher/students", label: "Students" },
  ];

  // Load all students for this teacher's school
  const { data: students, isLoading } = useQuery({
    queryKey: ["students", "active"],
    queryFn: () => studentsApi.list({ is_active: true }).then((r) => r.data),
  });

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <Topbar
        title="Teacher Dashboard"
        subtitle={`Welcome, ${user?.full_name}`}
      />

      <div className="flex-1 overflow-auto p-4 sm:p-6">
        <div className="mb-4 md:hidden">
          <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
            <div className="flex min-w-max items-center gap-2 p-2">
              <span className="px-2 py-1 text-xs font-medium text-slate-500">
                Navigation
              </span>
              {mobileLinks.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded-lg px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-50"
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
        </div>
        {/* Summary cards */}
        <div className="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {[
            {
              label: "Students in school",
              value: isLoading ? "—" : students?.length ?? 0,
            },
            {
              label: "Today's date",
              value: new Date().toLocaleDateString("en-IN", {
                day: "numeric",
                month: "short",
                year: "numeric",
              }),
            },
            { label: "Academic year", value: academicYearLabel },
          ].map(({ label, value }) => (
            <div
              key={label}
              className="bg-white border border-slate-200 rounded-xl p-4"
            >
              <p className="text-xs text-slate-500 mb-1">{label}</p>
              {isLoading && label === "Students in school" ? (
                <Skeleton className="h-7 w-12" />
              ) : (
                <p className="text-xl font-semibold text-slate-800">
                  {value}
                </p>
              )}
            </div>
          ))}
        </div>

        {/* Tabs */}
        <Tabs value={tab} onValueChange={setTab}>
          <TabsList className="mb-4 w-full bg-slate-100 sm:w-fit">
            <TabsTrigger
              value="attendance"
              className="flex-1 text-sm sm:flex-none"
            >
              Mark Attendance
            </TabsTrigger>
            <TabsTrigger value="marks" className="flex-1 text-sm sm:flex-none">
              Enter Marks
            </TabsTrigger>
          </TabsList>

          <TabsContent value="attendance">
            {isLoading ? (
              <div className="space-y-2">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Skeleton key={i} className="h-12 w-full" />
                ))}
              </div>
            ) : (
              <AttendanceGrid students={students ?? []} />
            )}
          </TabsContent>

          <TabsContent value="marks">
            {isLoading ? (
              <Skeleton className="h-64 w-full" />
            ) : (
              <MarksEntry students={students ?? []} />
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
