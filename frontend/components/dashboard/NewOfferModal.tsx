"use client";

import { ArrowRight, ExternalLink, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export function NewOfferModal({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const router = useRouter();

  function startFromScratch() {
    onOpenChange(false);
    router.push("/offers/new");
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Create a new offer</DialogTitle>
          <DialogDescription>Choose how you want to start your offer intake flow.</DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <button
            type="button"
            onClick={startFromScratch}
            className="group flex w-full items-center justify-between rounded-card border-[1.5px] border-border bg-surface px-4 py-4 text-left transition-all hover:border-orange hover:bg-selected"
          >
            <div className="flex items-start gap-3">
              <span className="mt-0.5 inline-flex h-8 w-8 items-center justify-center rounded-full bg-card text-orange">
                <Sparkles className="h-4 w-4" />
              </span>
              <div>
                <p className="text-sm font-semibold text-primary">Start from scratch</p>
                <p className="text-xs text-secondary">Build a new offer with the 6-step guided wizard.</p>
              </div>
            </div>
            <ArrowRight className="h-4 w-4 text-secondary transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
          </button>

          <div className="flex w-full items-center justify-between rounded-card border-[1.5px] border-border bg-card px-4 py-4 opacity-70">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 inline-flex h-8 w-8 items-center justify-center rounded-full bg-surface text-muted">
                <ExternalLink className="h-4 w-4" />
              </span>
              <div>
                <p className="text-sm font-semibold text-primary">Import from URL</p>
                <p className="text-xs text-secondary">Coming soon</p>
              </div>
            </div>
            <span className="rounded-pill border border-border bg-surface px-2 py-0.5 text-[11px] font-semibold text-muted">
              Coming soon
            </span>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
