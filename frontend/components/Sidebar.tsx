// frontend/components/Sidebar.tsx
"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/auth-store";
import {
  LayoutDashboard, Users,
  BookOpen, CreditCard, Bell, LogOut,
  GraduationCap, Activity, UserCheck,
  Sparkles,
} from "lucide-react";

// Different nav items per role
const navItems = {
  admin: [
    { href: "/admin/billing", label: "Billing", icon: CreditCard },
    { href: "/admin",         label: "Overview",       icon: LayoutDashboard },
    { href: "/admin/classes", label: "Classes",        icon: BookOpen },
    { href: "/admin/teachers", label: "Teachers",      icon: UserCheck },
    { href: "/admin/parents", label: "Parents",        icon: Users },
    { href: "/admin/students",label: "Students",       icon: Users },
    { href: "/admin/admission", label: "Admission",    icon: Users },
    { href: "/admin/agents",  label: "AI Agents",      icon: Activity },
    { href: "/finance",       label: "Fees",           icon: CreditCard },
    { href: "/admin/alerts",  label: "Alerts",         icon: Bell },
  ],
  teacher: [
    { href: "/teacher/copilot", label: "AI Co-Pilot", icon: Sparkles },
    { href: "/teacher",           label: "My Class",    icon: LayoutDashboard },
    { href: "/teacher/attendance",label: "Attendance",  icon: UserCheck },
    { href: "/teacher/marks",     label: "Marks",       icon: BookOpen },
    { href: "/teacher/students",  label: "Students",    icon: Users },
  ],
  parent: [
    { href: "/parent",       label: "Dashboard",  icon: LayoutDashboard },
    { href: "/parent/attendance", label: "Attendance", icon: UserCheck },
    { href: "/parent/marks", label: "Marks",      icon: BookOpen },
    { href: "/parent/fees",  label: "Fees",       icon: CreditCard },
  ],
  student: [
    { href: "/student",       label: "Dashboard", icon: LayoutDashboard },
    { href: "/student/marks", label: "My Marks",  icon: BookOpen },
  ],
};

export function Sidebar() {
  const pathname  = usePathname();
  const { user, logout } = useAuthStore();
  const role      = user?.role ?? "student";
  const items     = navItems[role] ?? [];

  return (
    <aside className="w-56 min-h-screen bg-white border-r border-slate-100
                      flex flex-col shrink-0">
      {/* Logo */}
      <div className="px-5 py-4 border-b border-slate-100">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center
                          justify-center">
            <GraduationCap className="w-4 h-4 text-white" />
          </div>
          <div>
            <p className="text-sm font-semibold text-slate-800">School OS</p>
            <p className="text-xs text-slate-400 capitalize">{role}</p>
          </div>
        </div>
      </div>

      {/* Nav links */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {items.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm",
                "transition-colors duration-150",
                active
                  ? "bg-blue-50 text-blue-700 font-medium"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* User + logout */}
      <div className="px-3 py-3 border-t border-slate-100">
        <div className="flex items-center gap-3 px-3 py-2 mb-1">
          <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center
                          justify-center text-xs font-semibold text-blue-700">
            {user?.full_name?.charAt(0) ?? "?"}
          </div>
          <p className="text-xs text-slate-600 truncate flex-1">
            {user?.full_name}
          </p>
        </div>
        <button
          onClick={logout}
          className="w-full flex items-center gap-3 px-3 py-2 text-sm
                     text-slate-500 hover:text-red-600 hover:bg-red-50
                     rounded-lg transition-colors"
        >
          <LogOut className="w-4 h-4" />
          Logout
        </button>
      </div>
    </aside>
  );
}
