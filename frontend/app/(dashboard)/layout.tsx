// frontend/app/(dashboard)/layout.tsx// frontend/app/(dashboard)/layout.tsx
"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/lib/auth-store";
import { Sidebar } from "@/components/Sidebar";
import { Skeleton } from "@/components/ui/skeleton";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isLoggedIn, hydrated } = useAuthStore();
  const router = useRouter();

  // Force hydration pass when landing directly on dashboard routes.
  useEffect(() => {
    if (!hydrated) {
      void useAuthStore.persist.rehydrate();
    }
  }, [hydrated]);

  // Redirect to login if not authenticated
  useEffect(() => {
    if (hydrated && !isLoggedIn) {
      router.push("/login");
    }
  }, [hydrated, isLoggedIn, router]);

  if (!hydrated) {
    return (
      <div className="flex h-screen bg-slate-50 overflow-hidden">
        <div className="hidden border-r border-slate-100 bg-white md:flex md:w-56" />
        <div className="flex flex-1 flex-col gap-4 p-4 sm:p-6">
          <Skeleton className="h-16 w-full rounded-xl" />
          <Skeleton className="h-40 w-full rounded-xl" />
          <Skeleton className="h-64 w-full rounded-xl" />
        </div>
      </div>
    );
  }

  if (!isLoggedIn) return null;

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden">
      <div className="hidden md:flex">
        <Sidebar />
      </div>
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {children}
      </div>
    </div>
  );
}
