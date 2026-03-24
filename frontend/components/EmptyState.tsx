// frontend/components/EmptyState.tsx

import { LucideIcon } from "lucide-react";

interface EmptyStateProps {
  icon:    LucideIcon;
  title:   string;
  body?:   string;
}

export function EmptyState({ icon: Icon, title, body }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="w-12 h-12 rounded-full bg-slate-100 flex items-center
                      justify-center mb-3">
        <Icon className="w-5 h-5 text-slate-400" />
      </div>
      <p className="text-sm font-medium text-slate-600 mb-1">{title}</p>
      {body && <p className="text-xs text-slate-400 max-w-xs">{body}</p>}
    </div>
  );
}