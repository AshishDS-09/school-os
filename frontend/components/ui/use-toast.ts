"use client";

import { toast as sonnerToast } from "sonner";

type ToastVariant = "default" | "destructive";

interface ToastOptions {
  title?: unknown;
  description?: unknown;
  variant?: ToastVariant;
}

function normalizeToastValue(value: unknown): string | undefined {
  if (value == null) {
    return undefined;
  }

  if (typeof value === "string") {
    return value;
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }

  if (Array.isArray(value)) {
    const normalizedItems = value
      .map((item) => normalizeToastValue(item))
      .filter((item): item is string => Boolean(item));

    return normalizedItems.length > 0
      ? normalizedItems.join(", ")
      : undefined;
  }

  if (typeof value === "object") {
    const record = value as Record<string, unknown>;
    const preferredMessage =
      normalizeToastValue(record.msg) ??
      normalizeToastValue(record.message) ??
      normalizeToastValue(record.detail) ??
      normalizeToastValue(record.error);

    return preferredMessage ?? JSON.stringify(value);
  }

  return String(value);
}

function toast({ title, description, variant = "default" }: ToastOptions) {
  const normalizedTitle = normalizeToastValue(title);
  const normalizedDescription = normalizeToastValue(description);
  const message = normalizedTitle ?? normalizedDescription ?? "Notification";
  const descriptionText =
    normalizedTitle && normalizedDescription ? normalizedDescription : undefined;

  if (variant === "destructive") {
    sonnerToast.error(message, {
      description: descriptionText,
    });
    return;
  }

  sonnerToast(message, {
    description: descriptionText,
  });
}

function useToast() {
  return { toast };
}

export { toast, useToast, normalizeToastValue };
