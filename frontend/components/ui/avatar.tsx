"use client";

import * as React from "react";
import Image from "next/image";

import { cn } from "@/lib/utils";

type AvatarSize = "default" | "sm" | "lg";

const avatarSizeClasses: Record<AvatarSize, string> = {
  default: "h-8 w-8",
  sm: "h-6 w-6",
  lg: "h-10 w-10",
};

interface AvatarContextValue {
  imageError: boolean;
  setImageError: (value: boolean) => void;
}

const AvatarContext = React.createContext<AvatarContextValue | null>(null);

function useAvatarContext() {
  return React.useContext(AvatarContext);
}

function Avatar({
  className,
  size = "default",
  ...props
}: React.ComponentProps<"span"> & { size?: AvatarSize }) {
  const [imageError, setImageError] = React.useState(false);

  return (
    <AvatarContext.Provider value={{ imageError, setImageError }}>
      <span
        className={cn(
          "relative inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-slate-100 text-slate-600",
          avatarSizeClasses[size],
          className
        )}
        {...props}
      />
    </AvatarContext.Provider>
  );
}

interface AvatarImageProps extends Omit<React.ComponentProps<typeof Image>, "fill" | "sizes" | "alt"> {
  alt?: string;
}

function AvatarImage({
  className,
  onError,
  alt = "",
  ...props
}: AvatarImageProps) {
  const context = useAvatarContext();

  if (!context || context.imageError) {
    return null;
  }

  return (
    <Image
      alt={alt}
      className={cn("h-full w-full object-cover", className)}
      fill
      onError={(event) => {
        context.setImageError(true);
        onError?.(event);
      }}
      sizes="40px"
      {...props}
    />
  );
}

function AvatarFallback({ className, ...props }: React.ComponentProps<"span">) {
  const context = useAvatarContext();

  if (context && !context.imageError) {
    return null;
  }

  return (
    <span
      className={cn("flex h-full w-full items-center justify-center text-sm font-medium", className)}
      {...props}
    />
  );
}

function AvatarBadge({ className, ...props }: React.ComponentProps<"span">) {
  return (
    <span
      className={cn(
        "absolute bottom-0 right-0 inline-flex h-2.5 w-2.5 rounded-full border-2 border-white bg-blue-600",
        className
      )}
      {...props}
    />
  );
}

function AvatarGroup({ className, ...props }: React.ComponentProps<"div">) {
  return <div className={cn("flex -space-x-2", className)} {...props} />;
}

function AvatarGroupCount({ className, ...props }: React.ComponentProps<"div">) {
  return (
    <div
      className={cn(
        "flex h-8 w-8 items-center justify-center rounded-full bg-slate-100 text-xs font-medium text-slate-600 ring-2 ring-white",
        className
      )}
      {...props}
    />
  );
}

export {
  Avatar,
  AvatarImage,
  AvatarFallback,
  AvatarGroup,
  AvatarGroupCount,
  AvatarBadge,
};
