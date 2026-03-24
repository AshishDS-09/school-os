"use client";

import * as React from "react";

import { CheckIcon, ChevronRightIcon } from "lucide-react";

import { cn } from "@/lib/utils";

function DropdownMenu({ children, ...props }: React.ComponentProps<"div">) {
  return <div {...props}>{children}</div>;
}

function DropdownMenuPortal({ children }: { children: React.ReactNode }) {
  return <>{children}</>;
}

function DropdownMenuTrigger({ children, ...props }: React.ComponentProps<"button">) {
  return (
    <button type="button" {...props}>
      {children}
    </button>
  );
}

function DropdownMenuContent({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn("min-w-32 rounded-lg border border-slate-200 bg-white p-1 shadow-md", className)}
      {...props}
    />
  );
}

function DropdownMenuGroup({ children, ...props }: React.ComponentProps<"div">) {
  return <div {...props}>{children}</div>;
}

function DropdownMenuItem({
  className,
  inset,
  variant = "default",
  ...props
}: React.ComponentProps<"button"> & {
  inset?: boolean;
  variant?: "default" | "destructive";
}) {
  return (
    <button
      type="button"
      className={cn(
        "flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors hover:bg-slate-100",
        inset && "pl-7",
        variant === "destructive" && "text-red-600 hover:bg-red-50",
        className
      )}
      {...props}
    />
  );
}

function DropdownMenuCheckboxItem({
  className,
  children,
  checked,
  inset,
  ...props
}: React.ComponentProps<"button"> & {
  checked?: boolean;
  inset?: boolean;
}) {
  return (
    <DropdownMenuItem className={className} inset={inset} {...props}>
      <span className="ml-auto">{checked ? <CheckIcon className="h-4 w-4" /> : null}</span>
      {children}
    </DropdownMenuItem>
  );
}

function DropdownMenuRadioGroup({ children, ...props }: React.ComponentProps<"div">) {
  return <div {...props}>{children}</div>;
}

function DropdownMenuRadioItem({
  className,
  children,
  inset,
  ...props
}: React.ComponentProps<"button"> & { inset?: boolean }) {
  return (
    <DropdownMenuItem className={className} inset={inset} {...props}>
      <span className="ml-auto">
        <CheckIcon className="h-4 w-4" />
      </span>
      {children}
    </DropdownMenuItem>
  );
}

function DropdownMenuLabel({ className, inset, ...props }: React.ComponentProps<"div"> & { inset?: boolean }) {
  return (
    <div
      className={cn("px-2 py-1 text-xs font-medium text-slate-500", inset && "pl-7", className)}
      {...props}
    />
  );
}

function DropdownMenuSeparator({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("my-1 h-px bg-slate-200", className)} {...props} />;
}

function DropdownMenuShortcut({ className, ...props }: React.ComponentProps<"span">) {
  return <span className={cn("ml-auto text-xs text-slate-400", className)} {...props} />;
}

function DropdownMenuSub({ children, ...props }: React.ComponentProps<"div">) {
  return <div {...props}>{children}</div>;
}

function DropdownMenuSubTrigger({
  className,
  inset,
  children,
  ...props
}: React.ComponentProps<"button"> & { inset?: boolean }) {
  return (
    <DropdownMenuItem className={className} inset={inset} {...props}>
      {children}
      <ChevronRightIcon className="ml-auto h-4 w-4" />
    </DropdownMenuItem>
  );
}

function DropdownMenuSubContent({ className, ...props }: React.ComponentProps<"div">) {
  return <DropdownMenuContent className={className} {...props} />;
}

export {
  DropdownMenu,
  DropdownMenuPortal,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuGroup,
  DropdownMenuLabel,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
  DropdownMenuSeparator,
  DropdownMenuShortcut,
  DropdownMenuSub,
  DropdownMenuSubTrigger,
  DropdownMenuSubContent,
};
