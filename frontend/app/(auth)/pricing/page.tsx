// frontend/app/(auth)/pricing/page.tsx
"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { CheckCircle2, GraduationCap } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn }    from "@/lib/utils";
import { useAuthStore } from "@/lib/auth-store";

interface Plan {
  tier:     string;
  label:    string;
  amount:   number;
  popular?: boolean;
  description: string;
  highlights: string[];
  agentCount: number;
}

const PLANS: Plan[] = [
  {
    tier:        "basic",
    label:       "Basic",
    amount:      999,
    description: "Everything you need to manage your school digitally",
    agentCount:  0,
    highlights: [
      "Up to 200 students",
      "Attendance management",
      "Fee collection tracking",
      "Exam marks & reports",
      "Parent portal",
      "SMS & WhatsApp notifications",
    ],
  },
  {
    tier:        "smart",
    label:       "Smart",
    amount:      1999,
    popular:     true,
    description: "AI that works in the background so your staff doesn't have to",
    agentCount:  4,
    highlights: [
      "Everything in Basic",
      "Up to 500 students",
      "Academic Risk Agent",
      "Attendance Risk Agent",
      "Fee Collection Agent",
      "Parent Communication Agent",
      "Real-time admin alerts",
      "Agent activity dashboard",
    ],
  },
  {
    tier:        "pro",
    label:       "Pro",
    amount:      3499,
    description: "The full AI operating system for ambitious schools",
    agentCount:  10,
    highlights: [
      "Everything in Smart",
      "Up to 5000 students",
      "Teacher Co-Pilot (lesson plans + MCQs)",
      "Personalized Learning Plans",
      "Teacher Performance Reports",
      "Behavioral Monitor Agent",
      "Admission Pipeline Agent",
      "Admin Morning Briefing",
      "Regional language support",
      "Priority support",
    ],
  },
];

declare global {
  interface Window {
    Razorpay: new (options: Record<string, unknown>) => {
      open: () => void;
    };
  }
}

export default function PricingPage() {
  const router        = useRouter();
  const { isLoggedIn, user } = useAuthStore();
  const [loading, setLoading] = useState<string | null>(null);

  const handleSelect = async (plan: Plan) => {
    if (!isLoggedIn) {
      router.push(`/register?tier=${plan.tier}`);
      return;
    }

    setLoading(plan.tier);

    try {
      // Step 1: Create order
      const { default: axios } = await import("axios");
      const { api } = await import("@/lib/api");

      const { data: order } = await api.post("/api/billing/create-order", {
        tier: plan.tier,
      });

      // Step 2: Load Razorpay script
      const script = document.createElement("script");
      script.src   = "https://checkout.razorpay.com/v1/checkout.js";
      document.body.appendChild(script);

      await new Promise<void>((res) => { script.onload = () => res(); });

      // Step 3: Open Razorpay modal
      const rzp = new window.Razorpay({
        key:         order.key_id,
        order_id:    order.order_id,
        amount:      order.amount,
        currency:    "INR",
        name:        "School OS",
        description: `${plan.label} Plan — Monthly`,
        prefill: {
          email: user?.email ?? "",
        },
        theme: { color: "#2563EB" },

        handler: async (response: {
          razorpay_order_id:   string;
          razorpay_payment_id: string;
          razorpay_signature:  string;
        }) => {
          // Step 4: Verify payment
          const { data: result } = await api.post("/api/billing/verify-payment", {
            order_id:   response.razorpay_order_id,
            payment_id: response.razorpay_payment_id,
            signature:  response.razorpay_signature,
            tier:       plan.tier,
          });

          if (result.success) {
            router.push("/admin?upgraded=true");
          }
        },
      });

      rzp.open();
    } catch (err) {
      console.error("Payment failed:", err);
    } finally {
      setLoading(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 px-6 py-4
                      flex items-center gap-3">
        <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center
                        justify-center">
          <GraduationCap className="w-4 h-4 text-white" />
        </div>
        <span className="font-semibold text-slate-800">School OS</span>
      </div>

      <div className="max-w-5xl mx-auto px-6 py-16">
        {/* Heading */}
        <div className="text-center mb-12">
          <p className="text-xs font-semibold text-blue-600 uppercase
                        tracking-widest mb-3">
            Pricing
          </p>
          <h1 className="text-3xl font-bold text-slate-900 mb-4">
            Simple, transparent pricing
          </h1>
          <p className="text-slate-500 max-w-xl mx-auto">
            Start free for 14 days. No credit card required.
            Upgrade anytime as your school grows.
          </p>
        </div>

        {/* Plan cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {PLANS.map((plan) => (
            <div
              key={plan.tier}
              className={cn(
                "bg-white rounded-2xl border overflow-hidden flex flex-col",
                plan.popular
                  ? "border-blue-400 shadow-lg shadow-blue-100 scale-[1.02]"
                  : "border-slate-200"
              )}
            >
              {plan.popular && (
                <div className="bg-blue-600 text-white text-xs font-semibold
                                text-center py-1.5 tracking-wide">
                  MOST POPULAR
                </div>
              )}

              <div className="p-6 flex-1">
                {/* Plan name + price */}
                <div className="mb-4">
                  <p className="text-sm font-semibold text-slate-500 mb-1">
                    {plan.label}
                  </p>
                  <div className="flex items-baseline gap-1">
                    <span className="text-3xl font-bold text-slate-900">
                      ₹{plan.amount.toLocaleString("en-IN")}
                    </span>
                    <span className="text-sm text-slate-400">/month</span>
                  </div>
                  <p className="text-xs text-slate-500 mt-2">
                    {plan.description}
                  </p>
                </div>

                {/* AI agent count badge */}
                {plan.agentCount > 0 && (
                  <div className={cn(
                    "inline-flex items-center gap-1.5 px-3 py-1 rounded-full",
                    "text-xs font-medium mb-4",
                    plan.agentCount === 10
                      ? "bg-purple-50 text-purple-700"
                      : "bg-blue-50 text-blue-700"
                  )}>
                    <span className="w-1.5 h-1.5 rounded-full bg-current" />
                    {plan.agentCount} AI Agents included
                  </div>
                )}

                {/* Feature list */}
                <ul className="space-y-2.5">
                  {plan.highlights.map((feature) => (
                    <li key={feature}
                      className="flex items-start gap-2">
                      <CheckCircle2 className="w-4 h-4 text-green-500
                                               shrink-0 mt-0.5" />
                      <span className="text-sm text-slate-700">{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* CTA button */}
              <div className="p-6 pt-0">
                <Button
                  className={cn(
                    "w-full h-10 text-sm font-medium",
                    plan.popular
                      ? "bg-blue-600 hover:bg-blue-700 text-white"
                      : "bg-slate-900 hover:bg-slate-800 text-white"
                  )}
                  onClick={() => handleSelect(plan)}
                  disabled={loading === plan.tier}
                >
                  {loading === plan.tier
                    ? "Processing..."
                    : isLoggedIn
                    ? `Upgrade to ${plan.label}`
                    : `Start with ${plan.label}`
                  }
                </Button>
                <p className="text-xs text-slate-400 text-center mt-2">
                  14-day free trial · Cancel anytime
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* FAQ */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 gap-6">
          {[
            {
              q: "Can I switch plans?",
              a: "Yes, you can upgrade or downgrade anytime. Changes take effect immediately.",
            },
            {
              q: "What happens if I exceed student limits?",
              a: "We'll notify you and suggest upgrading. We never cut off access without warning.",
            },
            {
              q: "Is my school's data safe?",
              a: "Yes. Each school's data is completely isolated using Row Level Security. No school can ever see another school's data.",
            },
            {
              q: "Do you offer annual billing?",
              a: "Yes — annual billing gives you 2 months free. Contact us after signing up.",
            },
          ].map(({ q, a }) => (
            <div key={q} className="bg-white border border-slate-200
                                    rounded-xl p-5">
              <p className="text-sm font-semibold text-slate-800 mb-2">{q}</p>
              <p className="text-sm text-slate-500">{a}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}