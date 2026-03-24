// frontend/app/(dashboard)/finance/page.tsx
"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  CreditCard, TrendingUp, AlertCircle,
  CheckCircle2, Clock, IndianRupee,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from "recharts";
import { Topbar }     from "@/components/Topbar";
import { StatCard }   from "@/components/StatCard";
import { EmptyState } from "@/components/EmptyState";
import { Button }     from "@/components/ui/button";
import { Badge }      from "@/components/ui/badge";
import { useToast }   from "@/components/ui/use-toast";
import { financeApi } from "@/lib/api";
import { formatRupees, formatDate, cn } from "@/lib/utils";

type FeeStatus = "pending" | "due" | "overdue" | "paid" | "partial" | "waived";

interface FeeRecord {
  id:            number;
  student_id:    number;
  fee_type:      string;
  amount:        number;
  amount_paid:   number;
  balance_due:   number;
  due_date:      string;
  paid_date?:    string;
  status:        FeeStatus;
  academic_year: string;
  reminder_count:number;
}

const STATUS_STYLE: Record<string, string> = {
  paid:    "bg-green-50 text-green-700 border-green-200",
  overdue: "bg-red-50 text-red-700 border-red-200",
  due:     "bg-amber-50 text-amber-700 border-amber-200",
  pending: "bg-slate-50 text-slate-600 border-slate-200",
  partial: "bg-blue-50 text-blue-700 border-blue-200",
};

export default function FinanceDashboard() {
  const { toast } = useToast();
  const qc = useQueryClient();
  const [activeStatus, setActiveStatus] = useState<string>("all");

  const { data: allFees = [], isLoading } = useQuery({
    queryKey: ["fees", "all"],
    queryFn:  () => financeApi.allFees().then((r) => r.data as FeeRecord[]),
  });

  // Mark fee as paid mutation
  const markPaid = useMutation({
    mutationFn: ({ id, amount }: { id: number; amount: number }) =>
      financeApi.updateFee(id, {
        amount_paid:    amount,
        status:         "paid",
        paid_date:      new Date().toISOString().split("T")[0],
        receipt_number: `REC-${Date.now()}`,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["fees"] });
      toast({ title: "Payment recorded", description: "Fee marked as paid" });
    },
  });

  // ── Derived stats ──────────────────────────────────────────────
  const totalCollected = allFees
    .filter((f) => f.status === "paid")
    .reduce((s, f) => s + f.amount, 0);

  const totalPending = allFees
    .filter((f) => ["due", "overdue", "partial"].includes(f.status))
    .reduce((s, f) => s + f.balance_due, 0);

  const overdueCount = allFees.filter((f) => f.status === "overdue").length;

  const collectionRate =
    allFees.length > 0
      ? Math.round(
          (allFees.filter((f) => f.status === "paid").length / allFees.length) * 100
        )
      : 0;

  // Build bar chart data per fee type
  const byType: Record<string, { collected: number; pending: number }> = {};
  allFees.forEach((f) => {
    const t = f.fee_type.replace("_", " ");
    if (!byType[t]) byType[t] = { collected: 0, pending: 0 };
    if (f.status === "paid") byType[t].collected += f.amount;
    else                     byType[t].pending   += f.balance_due;
  });
  const chartData = Object.entries(byType).map(([name, vals]) => ({
    name, ...vals,
  }));

  // Filter fees by active tab
  const filtered =
    activeStatus === "all"
      ? allFees
      : allFees.filter((f) => f.status === activeStatus);

  const filterTabs = [
    { key: "all",     label: "All" },
    { key: "overdue", label: "Overdue" },
    { key: "due",     label: "Due" },
    { key: "paid",    label: "Paid" },
  ];

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <Topbar title="Finance Dashboard" subtitle="Fee collection and recovery" />

      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Total collected"
            value={formatRupees(totalCollected)}
            icon={CheckCircle2}
            iconBg="bg-green-50"
            iconColor="text-green-600"
            sub={`${collectionRate}% collection rate`}
            trend="up"
          />
          <StatCard
            label="Pending amount"
            value={formatRupees(totalPending)}
            icon={Clock}
            iconBg="bg-amber-50"
            iconColor="text-amber-600"
            sub="awaiting payment"
            trend="down"
          />
          <StatCard
            label="Overdue fees"
            value={overdueCount}
            icon={AlertCircle}
            iconBg="bg-red-50"
            iconColor="text-red-600"
            sub="need immediate attention"
            trend={overdueCount > 0 ? "down" : "up"}
          />
          <StatCard
            label="Collection rate"
            value={`${collectionRate}%`}
            icon={TrendingUp}
            iconBg="bg-blue-50"
            iconColor="text-blue-600"
            sub="this academic year"
            trend={collectionRate >= 70 ? "up" : "down"}
          />
        </div>

        {/* Bar chart */}
        {chartData.length > 0 && (
          <div className="bg-white border border-slate-200 rounded-xl p-4">
            <p className="text-sm font-semibold text-slate-800 mb-4">
              Collection by fee type
            </p>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={chartData} margin={{ top: 0, right: 0, bottom: 0, left: -20 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
                <XAxis
                  dataKey="name"
                  tick={{ fontSize: 11, fill: "#94A3B8" }}
                  axisLine={false} tickLine={false}
                />
                <YAxis
                  tickFormatter={(v) => `₹${(v/1000).toFixed(0)}k`}
                  tick={{ fontSize: 11, fill: "#94A3B8" }}
                  axisLine={false} tickLine={false}
                />
                <Tooltip
                  formatter={(value) =>
                    typeof value === "number" ? formatRupees(value) : ""
                  }
                  contentStyle={{
                    fontSize: 12, borderRadius: 8,
                    border: "1px solid #E2E8F0",
                  }}
                />
                <Bar dataKey="collected" name="Collected" fill="#10B981" radius={[3,3,0,0]} />
                <Bar dataKey="pending"   name="Pending"   fill="#FCA5A5" radius={[3,3,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Fee records table with filter tabs */}
        <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
          <div className="flex items-center gap-1 px-4 pt-3 pb-0 border-b
                          border-slate-100">
            {filterTabs.map(({ key, label }) => (
              <button
                key={key}
                onClick={() => setActiveStatus(key)}
                className={cn(
                  "px-3 py-2 text-xs font-medium rounded-t-lg -mb-px",
                  "border-b-2 transition-colors",
                  activeStatus === key
                    ? "border-blue-600 text-blue-700"
                    : "border-transparent text-slate-500 hover:text-slate-700"
                )}
              >
                {label}
                <span className="ml-1.5 text-slate-400">
                  {key === "all"
                    ? allFees.length
                    : allFees.filter((f) => f.status === key).length}
                </span>
              </button>
            ))}
          </div>

          {isLoading ? (
            <div className="py-8 text-center text-sm text-slate-400">
              Loading...
            </div>
          ) : filtered.length === 0 ? (
            <EmptyState
              icon={CreditCard}
              title="No fees in this category"
            />
          ) : (
            <div className="divide-y divide-slate-50">
              {filtered.map((fee) => (
                <div
                  key={fee.id}
                  className="flex items-center justify-between px-4 py-3
                             hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-lg bg-slate-100 flex
                                    items-center justify-center">
                      <IndianRupee className="w-4 h-4 text-slate-500" />
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-800 capitalize">
                        Student #{fee.student_id} — {fee.fee_type.replace("_"," ")}
                      </p>
                      <p className="text-xs text-slate-400">
                        Due: {formatDate(fee.due_date)}
                        {fee.reminder_count > 0 && (
                          <span className="ml-2 text-blue-500">
                            · {fee.reminder_count} reminder{fee.reminder_count > 1 ? "s" : ""} sent
                          </span>
                        )}
                      </p>
                    </div>
                  </div>

                  <div className="flex items-center gap-3">
                    <div className="text-right">
                      <p className="text-sm font-semibold text-slate-800">
                        {formatRupees(fee.balance_due)}
                      </p>
                      <Badge
                        variant="outline"
                        className={cn(
                          "text-xs mt-0.5",
                          STATUS_STYLE[fee.status] ?? ""
                        )}
                      >
                        {fee.status}
                      </Badge>
                    </div>

                    {/* Mark as paid button for due/overdue fees */}
                    {(fee.status === "due" || fee.status === "overdue") && (
                      <Button
                        size="sm"
                        variant="outline"
                        className="text-xs h-7 border-green-300 text-green-700
                                   hover:bg-green-50"
                        onClick={() =>
                          markPaid.mutate({ id: fee.id, amount: fee.amount })
                        }
                        disabled={markPaid.isPending}
                      >
                        Mark paid
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
