// frontend/app/(dashboard)/admin/page.tsx
"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { Users, TrendingDown, CreditCard, Activity } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Topbar } from "@/components/Topbar";
import { AgentActivityFeed } from "@/components/AgentActivityFeed";
import { studentsApi, feesApi, agentLogsApi } from "@/lib/api";
import { formatRupees } from "@/lib/utils";
import { Skeleton } from "@/components/ui/skeleton";
import { useAuthStore } from "@/lib/auth-store";

function toList<T>(payload: unknown): T[] {
  if (Array.isArray(payload)) return payload;
  if (!payload || typeof payload !== "object") return [];

  const candidateKeys = ["items", "results", "data"];
  for (const key of candidateKeys) {
    const value = (payload as Record<string, unknown>)[key];
    if (Array.isArray(value)) return value as T[];
  }

  return [];
}

interface FeeSummary {
  id: number;
  student_id: number;
  fee_type: string | null;
  balance_due: number | string | null;
  due_date: string | null;
}

interface AgentLogSummary {
  action_taken?: unknown;
}

export default function AdminDashboard() {
  const { user } = useAuthStore();
  const mobileLinks = [
    { href: "/admin", label: "Overview" },
    { href: "/admin/students", label: "Students" },
    { href: "/admin/agents", label: "AI Agents" },
    { href: "/admin/fees", label: "Fees" },
  ];

  const { data: students, isLoading: loadingStudents } = useQuery({
    queryKey: ["students"],
    queryFn: () =>
      studentsApi.list({ is_active: true }).then((r) => toList(r.data)),
  });

  const { data: overdueFees, isLoading: loadingFees } = useQuery({
    queryKey: ["fees", "overdue"],
    queryFn: () =>
      feesApi.list({ status: "overdue" }).then((r) => toList<FeeSummary>(r.data)),
  });

  const { data: agentLogs } = useQuery({
    queryKey: ["agent-logs"],
    queryFn: () =>
      agentLogsApi.list({ limit: 5 }).then((r) => toList<AgentLogSummary>(r.data)),
    refetchInterval: 10000,   // refresh every 10 seconds
  });

  // Count students at risk from recent agent logs
  const highRiskCount = agentLogs?.filter(
    (log: AgentLogSummary) => String(log.action_taken ?? "").includes("HIGH")
  ).length ?? 0;

  const totalOverdue = overdueFees?.reduce(
    (sum: number, fee: { balance_due: number | string | null }) =>
      sum + Number(fee.balance_due ?? 0),
    0
  ) ?? 0;

  const statCards = [
    {
      label:   "Total students",
      value:   loadingStudents ? "—" : (students?.length ?? 0).toString(),
      icon:    Users,
      colour:  "text-blue-600",
      bg:      "bg-blue-50",
      loading: loadingStudents,
    },
    {
      label:   "At-risk students",
      value:   highRiskCount.toString(),
      icon:    TrendingDown,
      colour:  "text-red-600",
      bg:      "bg-red-50",
      loading: false,
    },
    {
      label:   "Overdue fees",
      value:   loadingFees ? "—" : formatRupees(totalOverdue),
      icon:    CreditCard,
      colour:  "text-amber-600",
      bg:      "bg-amber-50",
      loading: loadingFees,
    },
    {
      label:   "Recent agent runs",
      value:   (agentLogs?.length ?? 0).toString(),
      icon:    Activity,
      colour:  "text-green-600",
      bg:      "bg-green-50",
      loading: false,
    },
  ];

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <Topbar
        title="Admin Dashboard"
        subtitle={`Welcome, ${user?.full_name ?? "Admin"}`}
      />

      <div className="flex-1 space-y-6 overflow-auto p-4 sm:p-6">
        <div className="md:hidden">
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
        {/* Stat cards */}
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {statCards.map(({ label, value, icon: Icon, colour, bg, loading }) => (
            <Card key={label} className="border-slate-200">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-3">
                  <p className="text-xs text-slate-500">{label}</p>
                  <div className={`w-8 h-8 rounded-lg ${bg} flex items-center
                                   justify-center`}>
                    <Icon className={`w-4 h-4 ${colour}`} />
                  </div>
                </div>
                {loading ? (
                  <Skeleton className="h-7 w-20" />
                ) : (
                  <p className="text-2xl font-semibold text-slate-800">
                    {value}
                  </p>
                )}
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Live agent feed */}
          <Card className="border-slate-200 lg:col-span-1">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-green-500
                                 animate-pulse" />
                Live AI Agent Activity
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <AgentActivityFeed />
            </CardContent>
          </Card>

          {/* Overdue fees table */}
          <Card className="border-slate-200">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold">
                Overdue Fees
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loadingFees ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-10 w-full" />
                  ))}
                </div>
              ) : overdueFees?.length === 0 ? (
                <p className="text-sm text-slate-400 text-center py-6">
                  No overdue fees
                </p>
              ) : (
                <div className="space-y-2">
                  {overdueFees?.slice(0, 6).map(
                    (fee: FeeSummary) => (
                      <div
                        key={fee.id}
                        className="flex items-center justify-between
                                   py-2 border-b border-slate-50 last:border-0"
                      >
                        <div>
                          <p className="text-xs font-medium text-slate-700 capitalize">
                            {(fee.fee_type ?? "unknown fee").replace("_", " ")} - Student #{fee.student_id}
                          </p>
                          <p className="text-xs text-slate-400">
                            Due: {fee.due_date ?? "N/A"}
                          </p>
                        </div>
                        <span className="text-xs font-semibold text-red-600">
                          {formatRupees(Number(fee.balance_due ?? 0))}
                        </span>
                      </div>
                    )
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
