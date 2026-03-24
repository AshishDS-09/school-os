"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

type BadgeVariant = "default" | "secondary" | "destructive" | "outline" | "ghost" | "link";

const variantClasses: Record<BadgeVariant, string> = {
  default: "bg-slate-900 text-white",
  secondary: "bg-slate-100 text-slate-700",
  destructive: "bg-red-50 text-red-700 border border-red-200",
  outline: "border border-slate-200 text-slate-700 bg-white",
  ghost: "bg-transparent text-slate-700",
  link: "bg-transparent text-blue-600 underline-offset-4 hover:underline",
};

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

function Badge({ className, variant = "default", ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium",
        variantClasses[variant],
        className
      )}
      {...props}
    />
  );
}

export { Badge };
