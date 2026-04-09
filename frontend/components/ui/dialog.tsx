"use client";

import { X } from "lucide-react";
import { createContext, type ReactNode, useContext, useEffect, useMemo } from "react";
import { createPortal } from "react-dom";

import { cn } from "@/lib/utils";

type DialogContextValue = {
  open: boolean;
  onOpenChange: (open: boolean) => void;
};

const DialogContext = createContext<DialogContextValue | null>(null);

function useDialogContext() {
  const context = useContext(DialogContext);
  if (!context) {
    throw new Error("Dialog components must be used within <Dialog>");
  }
  return context;
}

export function Dialog({
  open,
  onOpenChange,
  children,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: ReactNode;
}) {
  const value = useMemo(() => ({ open, onOpenChange }), [open, onOpenChange]);
  return <DialogContext.Provider value={value}>{children}</DialogContext.Provider>;
}

export function DialogContent({
  className,
  children,
}: {
  className?: string;
  children: ReactNode;
}) {
  const { open, onOpenChange } = useDialogContext();

  useEffect(() => {
    if (!open) {
      return;
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onOpenChange(false);
      }
    }

    document.body.style.overflow = "hidden";
    window.addEventListener("keydown", onKeyDown);

    return () => {
      document.body.style.overflow = "";
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [onOpenChange, open]);

  if (!open || typeof document === "undefined") {
    return null;
  }

  return createPortal(
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <button
        type="button"
        aria-label="Close dialog"
        className="absolute inset-0 bg-black/20"
        onClick={() => onOpenChange(false)}
      />
      <div
        role="dialog"
        aria-modal="true"
        className={cn(
          "relative z-10 w-full max-w-[560px] rounded-card border-[1.5px] border-border bg-card p-6 shadow-[0_12px_40px_rgba(26,26,26,0.1)]",
          className,
        )}
      >
        <button
          type="button"
          aria-label="Close"
          onClick={() => onOpenChange(false)}
          className="absolute right-4 top-4 inline-flex h-8 w-8 items-center justify-center rounded-full border border-border bg-card text-secondary transition-colors hover:text-primary"
        >
          <X className="h-4 w-4" />
        </button>
        {children}
      </div>
    </div>,
    document.body,
  );
}

export function DialogHeader({ className, children }: { className?: string; children: ReactNode }) {
  return <div className={cn("mb-4 space-y-1.5", className)}>{children}</div>;
}

export function DialogTitle({ className, children }: { className?: string; children: ReactNode }) {
  return <h2 className={cn("text-xl font-bold tracking-[-0.02em] text-primary", className)}>{children}</h2>;
}

export function DialogDescription({ className, children }: { className?: string; children: ReactNode }) {
  return <p className={cn("text-sm text-secondary", className)}>{children}</p>;
}
