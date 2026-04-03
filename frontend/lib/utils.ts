// frontend/lib/utils.ts
// Small helper utilities

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow, isValid } from "date-fns";

// shadcn utility — merges Tailwind classes
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Format date to "15 Nov 2024"
export function formatDate(dateStr: string | Date | null | undefined): string {
  if (!dateStr) return "—";
  const parsed = new Date(dateStr);
  if (!isValid(parsed)) return "—";
  return format(parsed, "dd MMM yyyy");
}

// Format to "2 hours ago"
export function timeAgo(dateStr: string | Date | null | undefined): string {
  if (!dateStr) return "—";
  const parsed = new Date(dateStr);
  if (!isValid(parsed)) return "—";
  return formatDistanceToNow(parsed, { addSuffix: true });
}

// Risk level badge colour
export function riskColour(level: string) {
  return {
    HIGH:   "bg-red-100 text-red-700 border-red-200",
    MEDIUM: "bg-amber-100 text-amber-700 border-amber-200",
    LOW:    "bg-green-100 text-green-700 border-green-200",
  }[level] ?? "bg-gray-100 text-gray-600";
}

// Format Indian rupees
export function formatRupees(amount: number): string {
  return new Intl.NumberFormat("en-IN", {
    style:    "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(amount);
}
