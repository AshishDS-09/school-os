"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { subMonths, format } from "date-fns";
import {
  BookOpen, CreditCard, Bell, CalendarDays,
  CheckCircle2, AlertCircle, Clock,
} from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import { Topbar } from "@/components/Topbar";
import { StatCard } from "@/components/StatCard";
import { AttendanceCalendar } from "@/components/AttendanceCalendar";
import { MarksChart } from "@/components/MarksChart";
import { EmptyState } from "@/components/EmptyState";
import { RiskBadge } from "@/components/RiskBadge";
import { parentApi, type ParentStudent } from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { formatRupees, formatDate, cn } from "@/lib/utils";

type ParentPortalTab = "overview" | "attendance" | "marks" | "fees" | "alerts";

export function ParentPortalView({
  initialTab = "overview",
}: {
  initialTab?: ParentPortalTab;
}) {
  const { user } = useAuthStore();
  const [tab, setTab] = useState<ParentPortalTab>(initialTab);

  const { data: child, isLoading: loadingChild } = useQuery<ParentStudent | null>({
    queryKey: ["parent", "child"],
    queryFn: () => parentApi.getMyChild({
      user_id: user?.user_id,
      email: user?.email,
    }),
    enabled: !!user,
  });

  const fromDate = format(subMonths(new Date(), 1), "yyyy-MM-dd");

  const { data: attendance = [] } = useQuery({
    queryKey: ["parent", "attendance", child?.id],
    queryFn: () =>
      child ? parentApi.getAttendance(child.id, fromDate).then((r) => r.data) : [],
    enabled: !!child,
  });

  const { data: marks = [] } = useQuery({
    queryKey: ["parent", "marks", child?.id],
    queryFn: () =>
      child ? parentApi.getMarks(child.id).then((r) => r.data) : [],
    enabled: !!child,
  });

  const { data: fees = [] } = useQuery({
    queryKey: ["parent", "fees", child?.id],
    queryFn: () =>
      child ? parentApi.getFees(child.id).then((r) => r.data) : [],
    enabled: !!child,
  });

  const { data: notifications = [] } = useQuery({
    queryKey: ["parent", "notifications", user?.user_id],
    queryFn: () =>
      user ? parentApi.getNotifications(user.user_id).then((r) => r.data) : [],
    enabled: !!user,
  });

  const presentCount = attendance.filter(
    (a: { status: string }) => a.status === "present"
  ).length;
  const absentCount = attendance.filter(
    (a: { status: string }) => a.status === "absent"
  ).length;
  const attendancePct =
    attendance.length > 0
      ? Math.round((presentCount / attendance.length) * 100)
      : 0;

  const avgMarks =
    marks.length > 0
      ? Math.round(
          marks.reduce(
            (sum: number, mark: { percentage: number }) => sum + mark.percentage,
            0
          ) / marks.length
        )
      : 0;

  const pendingFees = fees.filter(
    (f: { status: string }) => f.status === "due" || f.status === "overdue"
  );
  const totalDue = pendingFees.reduce(
    (sum: number, fee: { balance_due: number }) => sum + fee.balance_due,
    0
  );

  const unreadNotifs = notifications.slice(0, 5);

  if (loadingChild) {
    return (
      <div className="flex flex-col h-full overflow-hidden">
        <Topbar title="Parent Portal" subtitle="Loading your child's data..." />
        <div className="flex-1 flex items-center justify-center">
          <div className="w-8 h-8 rounded-full border-2 border-blue-600 border-t-transparent animate-spin" />
        </div>
      </div>
    );
  }

  if (!child) {
    return (
      <div className="flex flex-col h-full overflow-hidden">
        <Topbar
          title="Parent Portal"
          subtitle="We couldn't identify a linked student for this account."
        />
        <div className="flex-1 overflow-auto p-6">
          <EmptyState
            icon={Bell}
            title="No linked student found"
            body="This account is signed in, but the student record could not be matched safely. That protects student data from being shown to the wrong parent."
          />
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <Topbar
        title="Parent Portal"
        subtitle={`${child.first_name} ${child.last_name} — Roll #${child.roll_number}`}
      />

      <div className="flex-1 overflow-auto p-6 space-y-6">
        <div className="bg-white border border-slate-200 rounded-xl p-4 flex items-center gap-4">
          <div className="w-14 h-14 rounded-full bg-blue-100 flex items-center justify-center text-xl font-bold text-blue-600">
            {child.first_name.charAt(0)}
          </div>
          <div className="flex-1">
            <p className="text-base font-semibold text-slate-800">
              {child.first_name} {child.last_name}
            </p>
            <p className="text-sm text-slate-500">
              Roll #{child.roll_number}
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs text-slate-400 mb-1">AI risk status</p>
            <RiskBadge level={avgMarks < 40 ? "HIGH" : avgMarks < 60 ? "MEDIUM" : "LOW"} />
          </div>
        </div>

        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Attendance this month"
            value={`${attendancePct}%`}
            icon={CalendarDays}
            iconBg="bg-green-50"
            iconColor="text-green-600"
            sub={`${presentCount} present, ${absentCount} absent`}
            trend={attendancePct >= 75 ? "up" : "down"}
          />
          <StatCard
            label="Average marks"
            value={`${avgMarks}%`}
            icon={BookOpen}
            iconBg="bg-blue-50"
            iconColor="text-blue-600"
            sub={`${marks.length} exams recorded`}
            trend={avgMarks >= 60 ? "up" : "down"}
          />
          <StatCard
            label="Pending fees"
            value={formatRupees(totalDue)}
            icon={CreditCard}
            iconBg={totalDue > 0 ? "bg-red-50" : "bg-green-50"}
            iconColor={totalDue > 0 ? "text-red-600" : "text-green-600"}
            sub={totalDue > 0 ? `${pendingFees.length} dues` : "All paid"}
            trend={totalDue > 0 ? "down" : "up"}
          />
          <StatCard
            label="Notifications"
            value={notifications.length}
            icon={Bell}
            iconBg="bg-purple-50"
            iconColor="text-purple-600"
            sub="from school"
          />
        </div>

        <Tabs value={tab} onValueChange={(value) => setTab(value as ParentPortalTab)}>
          <TabsList className="bg-slate-100">
            <TabsTrigger value="overview" className="text-sm">Overview</TabsTrigger>
            <TabsTrigger value="attendance" className="text-sm">Attendance</TabsTrigger>
            <TabsTrigger value="marks" className="text-sm">Marks</TabsTrigger>
            <TabsTrigger value="fees" className="text-sm">Fees</TabsTrigger>
            <TabsTrigger value="alerts" className="text-sm">
              Alerts
              {unreadNotifs.length > 0 && (
                <Badge className="ml-1.5 h-4 w-4 p-0 text-xs justify-center bg-red-500 text-white border-0">
                  {unreadNotifs.length}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="mt-4 space-y-4">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
              <MarksChart marks={marks} />
              <AttendanceCalendar records={attendance} />
            </div>
          </TabsContent>

          <TabsContent value="attendance" className="mt-4">
            <AttendanceCalendar records={attendance} />
          </TabsContent>

          <TabsContent value="marks" className="mt-4 space-y-4">
            <MarksChart marks={marks} />
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100">
                <p className="text-sm font-semibold text-slate-800">All marks</p>
              </div>
              {marks.length === 0 ? (
                <EmptyState icon={BookOpen} title="No marks recorded yet" />
              ) : (
                <div className="divide-y divide-slate-50">
                  {marks.map((m: {
                    id: number; subject: string; exam_type: string; exam_date: string;
                    percentage: number; score: number; max_score: number;
                  }) => (
                    <div key={m.id} className="flex items-center justify-between px-4 py-3">
                      <div>
                        <p className="text-sm font-medium text-slate-800">{m.subject}</p>
                        <p className="text-xs text-slate-400 capitalize">
                          {m.exam_type.replace("_", " ")} · {formatDate(m.exam_date)}
                        </p>
                      </div>
                      <div className="text-right">
                        <p className={cn(
                          "text-sm font-semibold",
                          m.percentage < 40 ? "text-red-600" :
                          m.percentage < 60 ? "text-amber-600" : "text-green-600"
                        )}>
                          {Math.round(m.percentage)}%
                        </p>
                        <p className="text-xs text-slate-400">{m.score}/{m.max_score}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="fees" className="mt-4">
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100">
                <p className="text-sm font-semibold text-slate-800">Fee records</p>
              </div>
              {fees.length === 0 ? (
                <EmptyState icon={CreditCard} title="No fee records found" />
              ) : (
                <div className="divide-y divide-slate-50">
                  {fees.map((f: {
                    id: number; fee_type: string; amount: number; balance_due: number;
                    due_date: string; status: string; paid_date?: string;
                  }) => {
                    const isPaid = f.status === "paid";
                    const isOverdue = f.status === "overdue";
                    return (
                      <div key={f.id} className="flex items-center justify-between px-4 py-3">
                        <div className="flex items-center gap-3">
                          <div className={cn(
                            "w-8 h-8 rounded-lg flex items-center justify-center",
                            isPaid ? "bg-green-50" :
                            isOverdue ? "bg-red-50" : "bg-amber-50"
                          )}>
                            {isPaid ? (
                              <CheckCircle2 className="w-4 h-4 text-green-600" />
                            ) : isOverdue ? (
                              <AlertCircle className="w-4 h-4 text-red-600" />
                            ) : (
                              <Clock className="w-4 h-4 text-amber-600" />
                            )}
                          </div>
                          <div>
                            <p className="text-sm font-medium text-slate-800 capitalize">
                              {f.fee_type.replace("_", " ")} fee
                            </p>
                            <p className="text-xs text-slate-400">
                              {isPaid ? `Paid on ${formatDate(f.paid_date!)}` : `Due: ${formatDate(f.due_date)}`}
                            </p>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className={cn(
                            "text-sm font-semibold",
                            isPaid ? "text-green-600" :
                            isOverdue ? "text-red-600" : "text-amber-600"
                          )}>
                            {formatRupees(f.balance_due)}
                          </p>
                          <p className="text-xs text-slate-400 capitalize">{f.status}</p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </TabsContent>

          <TabsContent value="alerts" className="mt-4">
            <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
              <div className="px-4 py-3 border-b border-slate-100">
                <p className="text-sm font-semibold text-slate-800">School alerts</p>
              </div>
              {notifications.length === 0 ? (
                <EmptyState
                  icon={Bell}
                  title="No alerts yet"
                  body="AI agents will send alerts here when action is needed."
                />
              ) : (
                <div className="divide-y divide-slate-50">
                  {notifications.map((n: {
                    id: number; notification_type: string; content: string;
                    channel: string; created_at: string; triggered_by?: string;
                  }) => (
                    <div key={n.id} className="px-4 py-3">
                      <div className="flex items-center gap-2 mb-1">
                        <Badge variant="outline" className="text-xs capitalize">
                          {n.notification_type.replace("_", " ")}
                        </Badge>
                        <span className="text-xs text-slate-400 capitalize">
                          via {n.channel}
                        </span>
                        {n.triggered_by && (
                          <span className="text-xs text-blue-500">
                            · {n.triggered_by.replace("_", " ")}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-slate-700 whitespace-pre-line">{n.content}</p>
                      <p className="text-xs text-slate-400 mt-1">{formatDate(n.created_at)}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
