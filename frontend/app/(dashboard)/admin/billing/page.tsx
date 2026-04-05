// frontend/app/(dashboard)/admin/billing/page.tsx
"use client";

import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  CheckCircle2, XCircle, Crown,
  Zap, Shield, ArrowUpRight,
} from "lucide-react";
import { Topbar }  from "@/components/Topbar";
import { Button }  from "@/components/ui/button";
import { Badge }   from "@/components/ui/badge";
import { api }     from "@/lib/api";
import { useAuthStore } from "@/lib/auth-store";
import { useToast }    from "@/components/ui/use-toast";
import { cn }          from "@/lib/utils";

const TIER_ICONS = {
  basic: Shield,
  smart: Zap,
  pro:   Crown,
};

const TIER_COLORS = {
  basic: "text-slate-600 bg-slate-50 border-slate-200",
  smart: "text-blue-700 bg-blue-50 border-blue-200",
  pro:   "text-purple-700 bg-purple-50 border-purple-200",
};

interface BillingStatus {
  current_tier:    string;
  price_per_month: number;
  label:           string;
  features:        Record<string, boolean | number>;
  razorpay_key:    string;
  billing_enabled: boolean;
  school_name:     string;
}

interface Plan {
  tier:        string;
  label:       string;
  amount:      number;
  description: string;
  features:    Record<string, boolean | number>;
}

declare global {
  interface Window {
    Razorpay: new (opts: Record<string, unknown>) => { open: () => void };
  }
}

export default function BillingPage() {
  const { toast }    = useToast();
  const { user }     = useAuthStore();
  const qc           = useQueryClient();
  const [upgrading, setUpgrading] = useState<string | null>(null);

  const { data: status, isLoading: loadingStatus } = useQuery<BillingStatus>({
    queryKey: ["billing", "status"],
    queryFn:  () => api.get("/api/billing/status").then((r) => r.data),
  });

  const { data: plansData } = useQuery<{ plans: Plan[] }>({
    queryKey: ["billing", "plans"],
    queryFn:  () => api.get("/api/billing/plans").then((r) => r.data),
  });

  const plans = plansData?.plans ?? [];
  const billingEnabled = Boolean(status?.billing_enabled && status?.razorpay_key);

  const handleUpgrade = async (tier: string) => {
    if (tier === status?.current_tier) return;
    if (!billingEnabled) {
      toast({
        title: "Free testing mode",
        description: "Billing is disabled for this deployment.",
      });
      return;
    }
    setUpgrading(tier);

    try {
      // Create order
      const { data: order } = await api.post("/api/billing/create-order", { tier });

      // Load Razorpay
      if (!document.querySelector('script[src*="razorpay"]')) {
        const script = document.createElement("script");
        script.src   = "https://checkout.razorpay.com/v1/checkout.js";
        document.body.appendChild(script);
        await new Promise<void>((res) => { script.onload = () => res(); });
      }

      const plan = plans.find((p) => p.tier === tier);

      const rzp = new window.Razorpay({
        key:         order.key_id,
        order_id:    order.order_id,
        amount:      order.amount,
        currency:    "INR",
        name:        "School OS",
        description: `${plan?.label ?? tier} Plan`,
        prefill:     { email: user?.email ?? "" },
        theme:       { color: "#2563EB" },

        handler: async (response: {
          razorpay_order_id:   string;
          razorpay_payment_id: string;
          razorpay_signature:  string;
        }) => {
          const { data: result } = await api.post("/api/billing/verify-payment", {
            order_id:   response.razorpay_order_id,
            payment_id: response.razorpay_payment_id,
            signature:  response.razorpay_signature,
            tier,
          });

          if (result.success) {
            qc.invalidateQueries({ queryKey: ["billing"] });
            toast({
              title:       "Plan upgraded!",
              description: result.message,
            });
          }
          setUpgrading(null);
        },
      });

      rzp.open();
    } catch {
      toast({
        title:   "Payment failed",
        variant: "destructive",
      });
      setUpgrading(null);
    }
  };

  const TierIcon = TIER_ICONS[status?.current_tier as keyof typeof TIER_ICONS]
    ?? Shield;

  // Feature display names
  const FEATURE_LABELS: Record<string, string> = {
    academic_agent:      "Academic Risk Agent",
    attendance_agent:    "Attendance Risk Agent",
    fee_agent:           "Fee Collection Agent",
    teacher_copilot:     "Teacher Co-Pilot (AI lesson plans)",
    admission_agent:     "Admission Lead Agent",
    behavioral_agent:    "Behavioral Monitor Agent",
    learning_agent:      "Personalized Learning Agent",
    teacher_performance: "Teacher Performance Reports",
    admin_workflow:      "Admin Morning Briefing",
    parent_comm:         "Regional Language Support",
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      <Topbar title="Billing & Subscription"
              subtitle="Manage your School OS plan" />

      <div className="flex-1 overflow-auto p-6 space-y-6">

        {/* Current plan card */}
        {!loadingStatus && status && (
          <div className={cn(
            "border rounded-2xl p-6",
            TIER_COLORS[status.current_tier as keyof typeof TIER_COLORS]
              ?? "border-slate-200 bg-white"
          )}>
            <div className="flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-white/60 flex
                                items-center justify-center border border-white/40">
                  <TierIcon className="w-5 h-5" />
                </div>
                <div>
                  <p className="text-xs font-medium opacity-70">Current plan</p>
                  <p className="text-lg font-bold">
                    {status.label} Plan
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-2xl font-bold">
                  ₹{status.price_per_month.toLocaleString("en-IN")}
                </p>
                <p className="text-xs opacity-70">per month</p>
              </div>
            </div>

            <div className="mt-4 pt-4 border-t border-white/30">
              <p className="text-xs font-medium opacity-70 mb-2">
                School: {status.school_name}
              </p>
              <div className="flex gap-2 flex-wrap">
                <Badge variant="outline"
                  className="text-xs bg-white/40 border-white/30">
                  Up to {(status.features.max_students as number).toLocaleString()} students
                </Badge>
                <Badge variant="outline"
                  className="text-xs bg-white/40 border-white/30">
                  {Object.entries(status.features)
                    .filter(([k, v]) => k.endsWith("_agent") && v === true)
                    .length} AI agents active
                </Badge>
              </div>
            </div>
          </div>
        )}

        {!loadingStatus && status && !billingEnabled && (
          <div className="rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 text-sm text-amber-900">
            Billing is disabled for this deployment. Your team can test the platform without Razorpay for now.
          </div>
        )}

        {/* Plan comparison */}
        <div>
          <p className="text-sm font-semibold text-slate-800 mb-4">
            All plans
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {plans.map((plan) => {
              const isCurrent = plan.tier === status?.current_tier;
              const Icon      = TIER_ICONS[plan.tier as keyof typeof TIER_ICONS]
                ?? Shield;

              return (
                <div
                  key={plan.tier}
                  className={cn(
                    "bg-white border rounded-xl p-5 flex flex-col",
                    isCurrent
                      ? "border-blue-400 ring-1 ring-blue-200"
                      : "border-slate-200"
                  )}
                >
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <Icon className="w-4 h-4 text-slate-600" />
                      <span className="text-sm font-semibold text-slate-800">
                        {plan.label}
                      </span>
                    </div>
                    {isCurrent && (
                      <Badge className="text-xs bg-blue-600 text-white border-0">
                        Current
                      </Badge>
                    )}
                  </div>

                  <p className="text-xl font-bold text-slate-800 mb-1">
                    ₹{plan.amount.toLocaleString("en-IN")}
                    <span className="text-sm font-normal text-slate-400">
                      /month
                    </span>
                  </p>

                  <p className="text-xs text-slate-500 mb-4">
                    {plan.description}
                  </p>

                  {/* AI Features */}
                  <div className="space-y-1.5 flex-1 mb-4">
                    {Object.entries(FEATURE_LABELS).map(([key, label]) => {
                      const included = plan.features[key] === true;
                      return (
                        <div key={key}
                          className="flex items-center gap-2">
                          {included
                            ? <CheckCircle2 className="w-3.5 h-3.5 text-green-500 shrink-0" />
                            : <XCircle      className="w-3.5 h-3.5 text-slate-200 shrink-0" />
                          }
                          <span className={cn(
                            "text-xs",
                            included ? "text-slate-700" : "text-slate-300"
                          )}>
                            {label}
                          </span>
                        </div>
                      );
                    })}
                  </div>

                  {isCurrent ? (
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full h-8 text-xs"
                      disabled
                    >
                      Current plan
                    </Button>
                  ) : (
                    <Button
                      size="sm"
                      className="w-full h-8 text-xs bg-blue-600
                                 hover:bg-blue-700 text-white"
                      onClick={() => handleUpgrade(plan.tier)}
                      disabled={!billingEnabled || upgrading === plan.tier}
                    >
                      {upgrading === plan.tier ? "Processing..." : !billingEnabled ? (
                        "Billing disabled"
                      ) : (
                        <>
                          Upgrade to {plan.label}
                          <ArrowUpRight className="w-3.5 h-3.5 ml-1" />
                        </>
                      )}
                    </Button>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}
