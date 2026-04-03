"use client";

import { useQuery } from "@tanstack/react-query";
import { Bell, TriangleAlert } from "lucide-react";
import { Topbar } from "@/components/Topbar";
import { AgentActivityFeed } from "@/components/AgentActivityFeed";
import { agentLogsApi } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { timeAgo } from "@/lib/utils";

interface AgentLog {
  id: number;
  agent_name?: string;
  action_taken?: string | null;
  outcome?: string;
  created_at?: string;
}

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

function isAlert(log: AgentLog): boolean {
  const text = String(log.action_taken ?? "");
  return log.outcome === "error" || text.includes("HIGH") || text.includes("MEDIUM");
}

export default function AdminAlertsPage() {
  const { data: logs, isLoading } = useQuery({
    queryKey: ["admin", "alerts"],
    queryFn: () =>
      agentLogsApi.list({ limit: 100 }).then((r) => toList<AgentLog>(r.data)),
    refetchInterval: 10000,
  });

  const alerts = (logs ?? []).filter(isAlert).slice(0, 20);

  return (
    <div className="flex h-full flex-col overflow-hidden">
      <Topbar
        title="Alerts"
        subtitle="High-risk events and recent AI escalations"
      />

      <div className="flex-1 space-y-6 overflow-auto p-4 sm:p-6">
        <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr]">
          <Card className="border-slate-200">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                <TriangleAlert className="h-4 w-4 text-amber-500" />
                Recent Alerts
              </CardTitle>
            </CardHeader>
            <CardContent>
              {isLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3, 4].map((item) => (
                    <Skeleton key={item} className="h-14 w-full" />
                  ))}
                </div>
              ) : alerts.length === 0 ? (
                <p className="py-8 text-center text-sm text-slate-400">
                  No active alerts right now.
                </p>
              ) : (
                <div className="space-y-3">
                  {alerts.map((log) => (
                    <div
                      key={log.id}
                      className="rounded-xl border border-slate-200 bg-white p-4"
                    >
                      <div className="mb-1 flex items-center justify-between gap-3">
                        <p className="text-sm font-medium text-slate-800">
                          {(log.agent_name ?? "agent").replaceAll("_", " ")}
                        </p>
                        <span className="text-xs text-slate-400">
                          {log.created_at ? timeAgo(log.created_at) : "just now"}
                        </span>
                      </div>
                      <p className="text-sm text-slate-600">
                        {log.action_taken ?? "Alert generated"}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                <Bell className="h-4 w-4 text-blue-500" />
                Live Agent Feed
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <AgentActivityFeed />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
