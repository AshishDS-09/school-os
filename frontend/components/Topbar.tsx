// frontend/components/Topbar.tsx
"use client";

import { Bell } from "lucide-react";
import { useAuthStore } from "@/lib/auth-store";
import { Badge } from "@/components/ui/badge";

interface TopbarProps {
  title:    string;
  subtitle?: string;
}

export function Topbar({ title, subtitle }: TopbarProps) {
  const { user } = useAuthStore();

  return (
    <header className="bg-white border-b border-slate-100 px-4 py-3
                       sm:px-6 shrink-0">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="min-w-0">
        <h1 className="text-base font-semibold text-slate-800">{title}</h1>
        {subtitle && (
          <p className="text-xs text-slate-400 truncate">{subtitle}</p>
        )}
        </div>
        <div className="flex items-center gap-3 self-start sm:self-auto">
          <Badge variant="outline" className="text-xs capitalize">
            {user?.role}
          </Badge>
          <button className="relative p-1.5 rounded-lg hover:bg-slate-50">
            <Bell className="w-4 h-4 text-slate-500" />
          </button>
        </div>
      </div>
    </header>
  );
}
