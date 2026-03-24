// frontend/lib/local-agent-log.ts
"use client";

export interface LocalAgentLog {
  id: number;
  school_id: number;
  agent_name: string;
  trigger: string;
  action_taken: string;
  outcome: "success" | "error" | "skipped";
  duration_ms: number | null;
  cost_usd: number;
  created_at: string;
}

const STORAGE_KEY = "school-os-local-agent-logs";
const EVENT_KEY = "school-os-agent-log-event";
let localLogCounter = 0;

function safeParseLogs(raw: string | null): LocalAgentLog[] {
  if (!raw) return [];
  try {
    const parsed = JSON.parse(raw);
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function getLocalAgentLogs(schoolId: number): LocalAgentLog[] {
  if (typeof window === "undefined") return [];
  const sorted = safeParseLogs(localStorage.getItem(STORAGE_KEY))
    .filter((log) => log.school_id === schoolId)
    .sort((a, b) => +new Date(b.created_at) - +new Date(a.created_at));

  const seen = new Set<number>();
  const deduped = sorted.filter((log) => {
    if (seen.has(log.id)) return false;
    seen.add(log.id);
    return true;
  });

  return deduped;
}

export function emitLocalAgentLog(
  schoolId: number,
  data: Omit<LocalAgentLog, "id" | "school_id" | "created_at">
) {
  if (typeof window === "undefined") return;

  localLogCounter = (localLogCounter + 1) % 1000000;
  const uniqueId = Number(`${Date.now()}${String(localLogCounter).padStart(3, "0")}`);

  const nextLog: LocalAgentLog = {
    id: uniqueId,
    school_id: schoolId,
    created_at: new Date().toISOString(),
    ...data,
  };

  const current = safeParseLogs(localStorage.getItem(STORAGE_KEY));
  const updated = [nextLog, ...current].slice(0, 100);
  localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
  localStorage.setItem(EVENT_KEY, JSON.stringify(nextLog));
}

export const localAgentLogEventKey = EVENT_KEY;
