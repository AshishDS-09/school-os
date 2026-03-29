"use client";

import * as React from "react";
import { Check, ChevronDown } from "lucide-react";

import { cn } from "@/lib/utils";

type SelectItemRecord = {
  value: string;
  label: React.ReactNode;
};

type SelectContextValue = {
  value?: string;
  open: boolean;
  setOpen: (open: boolean) => void;
  onValueChange?: (value: string) => void;
  registerItem: (item: SelectItemRecord) => void;
  items: Map<string, React.ReactNode>;
};

const SelectContext = React.createContext<SelectContextValue | null>(null);

function useSelectContext() {
  const context = React.useContext(SelectContext);

  if (!context) {
    throw new Error("Select components must be used inside <Select>.");
  }

  return context;
}

interface SelectProps {
  children: React.ReactNode;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  value?: string;
}

function Select({ children, defaultValue, onValueChange, value }: SelectProps) {
  const [internalValue, setInternalValue] = React.useState(defaultValue);
  const [open, setOpen] = React.useState(false);
  const [items, setItems] = React.useState<Map<string, React.ReactNode>>(new Map());
  const rootRef = React.useRef<HTMLDivElement>(null);

  const currentValue = value ?? internalValue;

  React.useEffect(() => {
    function handlePointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === "Escape") {
        setOpen(false);
      }
    }

    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleEscape);

    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleEscape);
    };
  }, []);

  const registerItem = React.useCallback((item: SelectItemRecord) => {
    setItems((prev) => {
      const next = new Map(prev);
      next.set(item.value, item.label);
      return next;
    });
  }, []);

  const handleValueChange = React.useCallback((nextValue: string) => {
    if (value === undefined) {
      setInternalValue(nextValue);
    }

    onValueChange?.(nextValue);
    setOpen(false);
  }, [onValueChange, value]);

  return (
    <SelectContext.Provider
      value={{
        value: currentValue,
        open,
        setOpen,
        onValueChange: handleValueChange,
        registerItem,
        items,
      }}
    >
      <div ref={rootRef} className="relative w-full">
        {children}
      </div>
    </SelectContext.Provider>
  );
}

function SelectTrigger({ className, children, ...props }: React.ButtonHTMLAttributes<HTMLButtonElement>) {
  const { open, setOpen } = useSelectContext();

  return (
    <button
      type="button"
      aria-expanded={open}
      className={cn(
        "flex h-10 w-full items-center justify-between rounded-lg border border-input bg-transparent px-3 py-2 text-sm outline-none transition-colors",
        "focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50",
        className
      )}
      onClick={() => setOpen(!open)}
      {...props}
    >
      <span className="min-w-0 flex-1 text-left">{children}</span>
      <ChevronDown className="ml-2 h-4 w-4 shrink-0 text-slate-500" />
    </button>
  );
}

function SelectValue({
  className,
  placeholder = "Select an option",
}: {
  className?: string;
  placeholder?: string;
}) {
  const { value, items } = useSelectContext();
  const label = value ? items.get(value) : null;

  return (
    <span className={cn("block truncate", !label && "text-slate-400", className)}>
      {label ?? placeholder}
    </span>
  );
}

function SelectContent({ className, children }: React.ComponentProps<"div">) {
  const { open } = useSelectContext();

  if (!open) {
    return null;
  }

  return (
    <div
      className={cn(
        "absolute z-50 mt-2 max-h-64 w-full overflow-auto rounded-lg border border-slate-200 bg-white p-1 shadow-lg",
        className
      )}
    >
      {children}
    </div>
  );
}

interface SelectItemProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  value: string;
}

function SelectItem({ className, children, value, ...props }: SelectItemProps) {
  const { value: selectedValue, onValueChange, registerItem } = useSelectContext();
  const isSelected = selectedValue === value;

  React.useEffect(() => {
    registerItem({ value, label: children });
  }, [children, registerItem, value]);

  return (
    <button
      type="button"
      className={cn(
        "flex w-full items-center justify-between rounded-md px-3 py-2 text-sm text-slate-700 transition-colors hover:bg-slate-100",
        isSelected && "bg-slate-100 font-medium text-slate-900",
        className
      )}
      onClick={() => onValueChange?.(value)}
      {...props}
    >
      <span className="truncate">{children}</span>
      {isSelected ? <Check className="ml-2 h-4 w-4 shrink-0 text-blue-600" /> : null}
    </button>
  );
}

export { Select, SelectContent, SelectItem, SelectTrigger, SelectValue };
