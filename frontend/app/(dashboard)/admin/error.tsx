"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";

export default function AdminError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Keep error visible in dev console for quick debugging.
    console.error("Admin route error:", error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center p-6">
      <div className="w-full max-w-lg rounded-xl border border-red-200 bg-red-50 p-5">
        <h2 className="text-base font-semibold text-red-800">
          Admin dashboard failed to load
        </h2>
        <p className="mt-2 text-sm text-red-700">
          {error.message || "Unexpected error"}
        </p>
        <Button
          onClick={reset}
          className="mt-4 bg-red-600 hover:bg-red-700 text-white"
        >
          Retry
        </Button>
      </div>
    </div>
  );
}
