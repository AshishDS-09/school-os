// frontend/app/(dashboard)/admission/page.tsx
"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Users, TrendingUp, Calendar, PhoneCall } from "lucide-react";
import { Topbar }     from "@/components/Topbar";
import { StatCard }   from "@/components/StatCard";
import { EmptyState } from "@/components/EmptyState";
import { Badge }      from "@/components/ui/badge";
import { Button }     from "@/components/ui/button";
import { useToast }   from "@/components/ui/use-toast";
import { leadsApi }   from "@/lib/api";
import { formatDate, cn } from "@/lib/utils";

type LeadStatus =
  | "new" | "contacted" | "visit_scheduled"
  | "visited" | "applied" | "admitted" | "rejected" | "lost";

interface Lead {
  id:                  number;
  parent_name:         string;
  parent_phone:        string;
  child_name:          string;
  applying_for_grade:  string;
  status:              LeadStatus;
  source?:             string;
  follow_up_count:     number;
  created_at:          string;
}

// Kanban columns — ordered pipeline stages
const COLUMNS: { key: LeadStatus; label: string; colour: string }[] = [
  { key: "new",              label: "New",             colour: "bg-blue-50 border-blue-200"    },
  { key: "contacted",        label: "Contacted",       colour: "bg-purple-50 border-purple-200"},
  { key: "visit_scheduled",  label: "Visit Scheduled", colour: "bg-amber-50 border-amber-200"  },
  { key: "visited",          label: "Visited",         colour: "bg-orange-50 border-orange-200"},
  { key: "admitted",         label: "Admitted",        colour: "bg-green-50 border-green-200"  },
];

// Next logical status in the pipeline
const NEXT_STATUS: Partial<Record<LeadStatus, LeadStatus>> = {
  new:             "contacted",
  contacted:       "visit_scheduled",
  visit_scheduled: "visited",
  visited:         "admitted",
};

export default function AdmissionPipeline() {
  const { toast }  = useToast();
  const qc         = useQueryClient();
  const [selected, setSelected] = useState<Lead | null>(null);

  const { data: leads = [], isLoading } = useQuery({
    queryKey: ["leads"],
    queryFn:  () => leadsApi.list().then((r) => r.data as Lead[]),
  });

  const advance = useMutation({
    mutationFn: ({ id, status }: { id: number; status: LeadStatus }) =>
      leadsApi.update(id, { status }),
    onSuccess: (_, vars) => {
      qc.invalidateQueries({ queryKey: ["leads"] });
      toast({
        title:       "Lead updated",
        description: `Status changed to ${vars.status.replace("_", " ")}`,
      });
      setSelected(null);
    },
  });

  // ── Derived stats ──────────────────────────────────────────────
  const admitted   = leads.filter((l) => l.status === "admitted").length;
  const total      = leads.length;
  const convRate   = total > 0 ? Math.round((admitted / total) * 100) : 0;
  const thisWeek   = leads.filter((l) => {
    const d = new Date(l.created_at);
    const now = new Date();
    return (now.getTime() - d.getTime()) < 7 * 24 * 60 * 60 * 1000;
  }).length;

  // Group leads into columns
  const grouped = COLUMNS.reduce<Record<string, Lead[]>>((acc, col) => {
    acc[col.key] = leads.filter((l) => l.status === col.key);
    return acc;
  }, {});

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <Topbar title="Admission Pipeline" subtitle="Lead tracking and conversion" />

      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <StatCard
            label="Total leads"
            value={total}
            icon={Users}
            iconBg="bg-blue-50"
            iconColor="text-blue-600"
          />
          <StatCard
            label="Admitted"
            value={admitted}
            icon={TrendingUp}
            iconBg="bg-green-50"
            iconColor="text-green-600"
            sub={`${convRate}% conversion rate`}
            trend="up"
          />
          <StatCard
            label="New this week"
            value={thisWeek}
            icon={Calendar}
            iconBg="bg-purple-50"
            iconColor="text-purple-600"
          />
          <StatCard
            label="Need follow-up"
            value={leads.filter((l) => l.follow_up_count === 0 && l.status !== "admitted").length}
            icon={PhoneCall}
            iconBg="bg-amber-50"
            iconColor="text-amber-600"
            sub="not yet contacted"
            trend="down"
          />
        </div>

        {/* Kanban board */}
        {isLoading ? (
          <div className="text-center py-12 text-sm text-slate-400">
            Loading leads...
          </div>
        ) : leads.length === 0 ? (
          <EmptyState
            icon={Users}
            title="No leads yet"
            body="When parents submit an admission enquiry, leads appear here automatically."
          />
        ) : (
          <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
            {COLUMNS.map((col) => {
              const colLeads = grouped[col.key] ?? [];
              return (
                <div key={col.key} className="flex flex-col gap-2">
                  {/* Column header */}
                  <div className={cn(
                    "flex items-center justify-between px-3 py-2",
                    "rounded-lg border text-xs font-medium", col.colour
                  )}>
                    <span className="capitalize">{col.label}</span>
                    <span className="bg-white/70 px-1.5 py-0.5 rounded-full">
                      {colLeads.length}
                    </span>
                  </div>

                  {/* Lead cards */}
                  {colLeads.length === 0 ? (
                    <div className="border border-dashed border-slate-200
                                    rounded-xl h-20 flex items-center
                                    justify-center">
                      <p className="text-xs text-slate-300">Empty</p>
                    </div>
                  ) : (
                    colLeads.map((lead) => (
                      <div
                        key={lead.id}
                        className="bg-white border border-slate-200 rounded-xl
                                   p-3 cursor-pointer hover:border-blue-300
                                   hover:shadow-sm transition-all"
                        onClick={() =>
                          setSelected(selected?.id === lead.id ? null : lead)
                        }
                      >
                        {/* Lead card header */}
                        <p className="text-xs font-semibold text-slate-800 mb-0.5">
                          {lead.child_name}
                        </p>
                        <p className="text-xs text-slate-500 mb-2">
                          Grade {lead.applying_for_grade}
                        </p>
                        <p className="text-xs text-slate-500 mb-2 truncate">
                          {lead.parent_name}
                        </p>

                        {lead.source && (
                          <Badge
                            variant="outline"
                            className="text-xs px-1.5 py-0 h-4 capitalize mb-2"
                          >
                            {lead.source}
                          </Badge>
                        )}

                        {/* Expanded detail */}
                        {selected?.id === lead.id && (
                          <div className="mt-2 pt-2 border-t border-slate-100
                                          space-y-2">
                            <p className="text-xs text-slate-600">
                              Phone: {lead.parent_phone}
                            </p>
                            <p className="text-xs text-slate-400">
                              Added: {formatDate(lead.created_at)}
                            </p>
                            {lead.follow_up_count > 0 && (
                              <p className="text-xs text-blue-500">
                                {lead.follow_up_count} AI follow-up
                                {lead.follow_up_count > 1 ? "s" : ""} sent
                              </p>
                            )}

                            {/* Advance button */}
                            {NEXT_STATUS[lead.status] && (
                              <Button
                                size="sm"
                                className="w-full h-7 text-xs bg-blue-600
                                           hover:bg-blue-700 mt-1"
                                disabled={advance.isPending}
                                onClick={(e) => {
                                  e.stopPropagation();
                                  advance.mutate({
                                    id:     lead.id,
                                    status: NEXT_STATUS[lead.status]!,
                                  });
                                }}
                              >
                                Move to {NEXT_STATUS[lead.status]!
                                  .replace("_", " ")}
                              </Button>
                            )}
                          </div>
                        )}
                      </div>
                    ))
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
