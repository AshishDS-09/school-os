// frontend/components/AgentActivityFeed.tsx
"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { agentLogsApi } from "@/lib/api";
import { timeAgo, cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth-store";
import { supabase } from "@/lib/supabase";
import { Badge } from "@/components/ui/badge";
import { getLocalAgentLogs, localAgentLogEventKey } from "@/lib/local-agent-log";
import { useToast } from "@/components/ui/use-toast";

interface AgentLog {
  id:           number;
  agent_name:   string;
  trigger:      string;
  entity_type:  string | null;
  entity_id:    number | null;
  action_taken: string | null;
  outcome:      "success" | "error" | "skipped";
  duration_ms:  number | null;
  cost_usd:     number;
  created_at:   string;
}

function safeTimeAgo(dateStr: string | null | undefined): string {
  if (!dateStr) return "just now";
  try {
    return timeAgo(dateStr);
  } catch {
    return "just now";
  }
}

function normalizeAgentLog(raw: unknown): AgentLog | null {
  if (!raw || typeof raw !== "object") return null;
  const r = raw as Record<string, unknown>;
  if (typeof r.id !== "number") return null;

  return {
    id: r.id,
    agent_name: typeof r.agent_name === "string" ? r.agent_name : "agent",
    trigger: typeof r.trigger === "string" ? r.trigger : "event",
    entity_type: typeof r.entity_type === "string" ? r.entity_type : null,
    entity_id: typeof r.entity_id === "number" ? r.entity_id : null,
    action_taken: typeof r.action_taken === "string" ? r.action_taken : null,
    outcome:
      r.outcome === "error" || r.outcome === "skipped" || r.outcome === "success"
        ? r.outcome
        : "success",
    duration_ms: typeof r.duration_ms === "number" ? r.duration_ms : null,
    cost_usd: typeof r.cost_usd === "number" ? r.cost_usd : 0,
    created_at: typeof r.created_at === "string" ? r.created_at : new Date().toISOString(),
  };
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

// Human-readable agent name mapping
const agentLabels: Record<string, string> = {
  academic_agent:    "Academic Agent",
  attendance_agent:  "Attendance Agent",
  fee_agent:         "Fee Agent",
  behavioral_agent:  "Behavioral Agent",
  admission_agent:   "Admission Agent",
  teacher_agent:     "Teacher Co-Pilot",
  learning_agent:    "Learning Agent",
};

// Extract risk level from action_taken text
function extractRisk(action: string | null): string | null {
  if (!action) return null;
  if (action.includes("HIGH"))   return "HIGH";
  if (action.includes("MEDIUM")) return "MEDIUM";
  if (action.includes("LOW"))    return "LOW";
  return null;
}

function dedupeLogs(logs: AgentLog[]): AgentLog[] {
  const seen = new Set<number>();
  const result: AgentLog[] = [];

  for (const log of logs) {
    if (seen.has(log.id)) continue;
    seen.add(log.id);
    result.push(log);
  }

  return result;
}

export function AgentActivityFeed() {
  const { toast } = useToast();
  const { user }  = useAuthStore();
  const schoolId  = user?.school_id;
  const seenAlertIds = useRef<Set<number>>(new Set());

  // Initial load from API
  const { data: initialLogs } = useQuery({
    queryKey: ["agent-logs", "feed"],
    queryFn:  () =>
      agentLogsApi
        .list({ limit: 20 })
        .then((r) => toList<AgentLog>(r.data).map(normalizeAgentLog).filter(Boolean) as AgentLog[]),
    enabled:  !!schoolId,
  });

  const [liveLogs, setLiveLogs] = useState<AgentLog[]>([]);
  const localLogs = useMemo(() => {
    if (!schoolId) return [];
    return getLocalAgentLogs(schoolId).map(normalizeAgentLog).filter(Boolean) as AgentLog[];
  }, [schoolId]);

  useEffect(() => {
    if (!schoolId) return;
    const onStorage = (event: StorageEvent) => {
      if (event.key !== localAgentLogEventKey || !event.newValue) return;
      try {
        const parsed = JSON.parse(event.newValue) as { school_id?: number };
        if (parsed.school_id !== schoolId) return;
        const normalized = normalizeAgentLog(parsed);
        if (!normalized) return;
        setLiveLogs((prev) => [normalized, ...prev.filter((x) => x.id !== normalized.id)].slice(0, 50));
      } catch {
        // Ignore malformed cross-tab events.
      }
    };

    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [schoolId]);

  const logs = dedupeLogs([
    ...liveLogs,
    ...localLogs,
    ...(initialLogs ?? []),
  ]).slice(0, 50);

  useEffect(() => {
    if (!schoolId || !supabase) return;
    const realtime = supabase;

    const channel = realtime
      .channel(`agent-logs-${schoolId}`)
      .on(
        "postgres_changes",
        {
          event:  "INSERT",
          schema: "public",
          table:  "agent_logs",
          filter: `school_id=eq.${schoolId}`,
        },
        (payload) => {
          const normalized = normalizeAgentLog(payload.new);
          if (!normalized) return;
          setLiveLogs((prev) => [normalized, ...prev.filter((x) => x.id !== normalized.id)].slice(0, 50));
        }
      )
      .subscribe();

    return () => { realtime.removeChannel(channel); };
  }, [schoolId]);

  useEffect(() => {
    for (const log of logs) {
      if (seenAlertIds.current.has(log.id)) continue;
      seenAlertIds.current.add(log.id);

      const text = String(log.action_taken ?? "");
      if (text.includes("HIGH")) {
        toast({
          title: "High-risk alert",
          description: text.length > 100 ? `${text.slice(0, 100)}...` : text,
        });
      }
    }
  }, [logs, toast]);

  if (logs.length === 0) {
    return (
      <div className="py-8 text-center">
        <p className="text-sm text-slate-400">
          No agent activity yet. Enter marks or mark attendance to trigger agents.
        </p>
      </div>
    );
  }

  return (
    <div className="divide-y divide-slate-50 max-h-72 overflow-auto">
      {logs.map((log) => {
        const risk     = extractRisk(log.action_taken);
        const label    = agentLabels[log.agent_name] ?? log.agent_name;
        const isError  = log.outcome === "error";
        const isSkip   = log.outcome === "skipped";

        return (
          <div
            key={`${log.id}-${log.created_at}`}
            className="flex items-start gap-3 px-4 py-3 hover:bg-slate-50
                       transition-colors"
          >
            {/* Status dot */}
            <div
              className={cn(
                "w-2 h-2 rounded-full mt-1.5 shrink-0",
                isError ? "bg-red-400" :
                isSkip  ? "bg-slate-300" : "bg-green-400"
              )}
            />

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-medium text-slate-700">
                  {label}
                </span>

                {/* Risk badge */}
                {risk && (
                  <Badge
                    variant="outline"
                    className={cn(
                      "text-xs px-1.5 py-0 h-4",
                      risk === "HIGH"   && "border-red-200 text-red-600 bg-red-50",
                      risk === "MEDIUM" && "border-amber-200 text-amber-600 bg-amber-50",
                      risk === "LOW"    && "border-green-200 text-green-600 bg-green-50",
                    )}
                  >
                    {risk}
                  </Badge>
                )}

                {/* Trigger badge */}
                <Badge
                  variant="outline"
                  className="text-xs px-1.5 py-0 h-4 text-slate-400"
                >
                  {log.trigger}
                </Badge>
              </div>

              {/* Action summary */}
              {log.action_taken && (
                <p className="text-xs text-slate-500 mt-0.5 truncate">
                  {log.action_taken.length > 80
                    ? log.action_taken.slice(0, 80) + "..."
                    : log.action_taken}
                </p>
              )}

              {/* Meta row */}
              <div className="flex items-center gap-3 mt-1">
                <span className="text-xs text-slate-400">
                  {safeTimeAgo(log.created_at)}
                </span>
                {log.duration_ms !== null && (
                  <span className="text-xs text-slate-300">
                    {log.duration_ms}ms
                  </span>
                )}
                {log.cost_usd > 0 && (
                  <span className="text-xs text-slate-300">
                    ${log.cost_usd.toFixed(4)}
                  </span>
                )}
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
