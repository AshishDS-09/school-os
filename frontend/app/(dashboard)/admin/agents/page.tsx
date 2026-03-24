// frontend/app/(dashboard)/admin/agents/page.tsx
"use client";

import { useQuery }          from "@tanstack/react-query";
import { Topbar }            from "@/components/Topbar";
import { AgentActivityFeed } from "@/components/AgentActivityFeed";
import { RiskBadge }         from "@/components/RiskBadge";
import { agentLogsApi }      from "@/lib/api";
import { formatDate }        from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function AgentsPage() {
  const { data: logs = [] } = useQuery({
    queryKey: ["agent-logs", "all"],
    queryFn:  () => agentLogsApi.list({ limit: 100 }).then((r) => r.data),
    refetchInterval: 15000,
  });

  const totalCost  = logs.reduce(
    (s: number, l: { cost_usd: number }) => s + l.cost_usd, 0
  );
  const errorCount = logs.filter(
    (l: { outcome: string }) => l.outcome === "error"
  ).length;

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <Topbar title="AI Agents" subtitle="Live activity and cost monitoring" />
      <div className="flex-1 overflow-auto p-6 space-y-6">

        {/* Cost overview */}
        <div className="grid grid-cols-3 gap-4">
          {[
            { label: "Total agent runs",   value: logs.length  },
            { label: "Errors",             value: errorCount   },
            { label: "Total OpenAI cost",  value: `$${totalCost.toFixed(4)}` },
          ].map(({ label, value }) => (
            <div key={label}
              className="bg-white border border-slate-200 rounded-xl p-4">
              <p className="text-xs text-slate-500 mb-1">{label}</p>
              <p className="text-xl font-semibold text-slate-800">{value}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card className="border-slate-200">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold flex gap-2 items-center">
                <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"/>
                Live feed
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <AgentActivityFeed />
            </CardContent>
          </Card>

          <Card className="border-slate-200">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold">Recent runs</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="divide-y divide-slate-50 max-h-72 overflow-auto">
                {logs.slice(0, 20).map((l: {
                  id: number; agent_name: string;
                  outcome: string; action_taken?: string;
                  cost_usd: number; created_at: string;
                }) => (
                  <div key={l.id}
                    className="flex items-center justify-between px-4 py-2.5">
                    <div>
                      <p className="text-xs font-medium text-slate-700 capitalize">
                        {l.agent_name.replace("_agent", " agent")}
                      </p>
                      <p className="text-xs text-slate-400">
                        {formatDate(l.created_at)}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {l.action_taken?.includes("HIGH") && (
                        <RiskBadge level="HIGH" />
                      )}
                      <span className={`text-xs font-medium ${
                        l.outcome === "success" ? "text-green-600" :
                        l.outcome === "error"   ? "text-red-600"   :
                        "text-slate-400"
                      }`}>
                        {l.outcome}
                      </span>
                      <span className="text-xs text-slate-300">
                        ${l.cost_usd.toFixed(4)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}