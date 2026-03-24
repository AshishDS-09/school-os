"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

interface TabsContextValue {
  value: string;
  setValue: (value: string) => void;
}

const TabsContext = React.createContext<TabsContextValue | null>(null);

function useTabsContext() {
  const context = React.useContext(TabsContext);

  if (!context) {
    throw new Error("Tabs components must be used inside <Tabs>.");
  }

  return context;
}

interface TabsProps extends React.ComponentProps<"div"> {
  value: string;
  onValueChange: (value: string) => void;
}

function Tabs({ className, value, onValueChange, ...props }: TabsProps) {
  return (
    <TabsContext.Provider value={{ value, setValue: onValueChange }}>
      <div className={cn("flex flex-col gap-4", className)} {...props} />
    </TabsContext.Provider>
  );
}

function TabsList({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "inline-flex w-fit items-center gap-1 rounded-lg bg-slate-100 p-1",
        className
      )}
      {...props}
    />
  );
}

interface TabsTriggerProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
}

function TabsTrigger({ className, value, ...props }: TabsTriggerProps) {
  const { value: activeValue, setValue } = useTabsContext();
  const isActive = activeValue === value;

  return (
    <button
      type="button"
      aria-pressed={isActive}
      className={cn(
        "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
        isActive
          ? "bg-white text-slate-900 shadow-sm"
          : "text-slate-500 hover:text-slate-800",
        className
      )}
      onClick={() => setValue(value)}
      {...props}
    />
  );
}

interface TabsContentProps extends React.ComponentProps<"div"> {
  value: string;
}

function TabsContent({ className, value, ...props }: TabsContentProps) {
  const { value: activeValue } = useTabsContext();

  if (activeValue !== value) {
    return null;
  }

  return <div className={cn("text-sm", className)} {...props} />;
}

export { Tabs, TabsList, TabsTrigger, TabsContent };
