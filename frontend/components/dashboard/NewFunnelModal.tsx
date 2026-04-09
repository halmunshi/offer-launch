"use client";

import { useAuth } from "@clerk/nextjs";
import { ArrowRight, ExternalLink, Loader2, Sparkles, WandSparkles } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { api } from "@/lib/api";

type OfferOption = {
  id: string;
  name: string;
  createdAt: string;
};

export function NewFunnelModal({
  open,
  onOpenChange,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}) {
  const router = useRouter();
  const { getToken } = useAuth();
  const [isLoadingOffers, setIsLoadingOffers] = useState(false);
  const [offersError, setOffersError] = useState<string | null>(null);
  const [offers, setOffers] = useState<OfferOption[]>([]);
  const [selectedOfferId, setSelectedOfferId] = useState<string>("");

  const hasOffers = offers.length > 0;
  const hasSingleOffer = offers.length === 1;
  const resolvedOfferId = selectedOfferId;

  const canStart = useMemo(() => {
    if (!hasOffers) {
      return false;
    }
    return resolvedOfferId.length > 0;
  }, [hasOffers, resolvedOfferId]);

  useEffect(() => {
    if (!open) {
      return;
    }

    let cancelled = false;

    async function loadOffers() {
      setIsLoadingOffers(true);
      setOffersError(null);

      try {
        const token = await getToken();
        const response = await api.get<Array<{ id: string; name: string; created_at: string }>>("/offers", token);

        if (cancelled) {
          return;
        }

        const mapped = response.map((offer) => ({
          id: String(offer.id),
          name: offer.name || "Untitled Offer",
          createdAt: offer.created_at,
        }));
        setOffers(mapped);

        if (mapped.length === 1) {
          setSelectedOfferId(mapped[0].id);
        } else {
          setSelectedOfferId("");
        }
      } catch (error) {
        if (cancelled) {
          return;
        }
        setOffers([]);
        setOffersError(error instanceof Error ? error.message : "Unable to load offers.");
      } finally {
        if (!cancelled) {
          setIsLoadingOffers(false);
        }
      }
    }

    void loadOffers();

    return () => {
      cancelled = true;
    };
  }, [getToken, open]);

  function startFromScratch() {
    if (!canStart || !resolvedOfferId) {
      return;
    }

    onOpenChange(false);
    router.push(`/funnels/new?offerId=${resolvedOfferId}`);
  }

  function formatCreatedAt(value: string) {
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return "";
    }

    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    }).format(date);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="overflow-hidden p-0">
        <div className="border-b border-border bg-gradient-to-br from-[#fff8f2] via-[#fffdf9] to-[#f2f8ff] px-6 py-5">
          <DialogHeader className="mb-0 space-y-2">
            <div className="inline-flex w-fit items-center gap-1.5 rounded-pill border border-[#ffd7c6] bg-[#fff2ea] px-2.5 py-1 text-[11px] font-semibold uppercase tracking-[0.06em] text-[#cc4a00]">
              <WandSparkles className="h-3.5 w-3.5" />
              Funnel Setup
            </div>
            <DialogTitle className="text-[22px] tracking-[-0.03em]">Create a new funnel</DialogTitle>
            <DialogDescription className="max-w-[48ch] text-[13px] leading-relaxed text-secondary">
              Pick the offer this funnel belongs to, then choose how you want to start your funnel setup flow.
            </DialogDescription>
          </DialogHeader>
        </div>

        <div className="space-y-3 px-6 py-5">
          <div className="rounded-card border-[1.5px] border-border bg-gradient-to-br from-[#ffffff] to-[#faf9f7] p-3.5 shadow-[0_6px_20px_rgba(26,26,26,0.04)]">
            <p className="mb-2 text-xs font-semibold uppercase tracking-[0.05em] text-muted">Choose Offer</p>
            <Select value={selectedOfferId} onValueChange={setSelectedOfferId} disabled={isLoadingOffers || !hasOffers}>
              <SelectTrigger className="h-11 w-full rounded-input border-[1.5px] border-border bg-card px-3 text-sm text-primary shadow-xs">
                {isLoadingOffers ? (
                  <span className="inline-flex items-center gap-2 text-muted">
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    Loading offers...
                  </span>
                ) : (
                  <SelectValue
                    placeholder={hasOffers ? "Select which offer this funnel belongs to" : "No offers available"}
                  />
                )}
              </SelectTrigger>
              <SelectContent>
                {offers.map((offer) => (
                  <SelectItem key={offer.id} value={offer.id}>
                    <span className="grid w-full grid-cols-[minmax(0,1fr)_auto] items-center gap-3">
                      <span className="truncate">{offer.name}</span>
                      <span className="shrink-0 text-right text-xs italic text-muted">{formatCreatedAt(offer.createdAt)}</span>
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {hasSingleOffer && !isLoadingOffers ? (
              <p className="mt-2 text-xs text-muted">Only one offer found, preselected for you.</p>
            ) : null}
          </div>

          <button
            type="button"
            onClick={startFromScratch}
            disabled={!canStart}
            className={`group relative flex w-full items-center justify-between overflow-hidden rounded-card border-[1.5px] px-4 py-4 text-left transition-all ${
              canStart
                ? "border-[#f2c6b2] bg-gradient-to-r from-[#fff4ec] via-[#fff9f5] to-[#fff] hover:-translate-y-px hover:border-orange"
                : "cursor-not-allowed border-border bg-card opacity-75"
            }`}
          >
            {canStart ? (
              <span className="absolute -right-12 -top-12 h-28 w-28 rounded-full bg-orange/10 blur-xl" />
            ) : null}
            <div className="flex items-start gap-3">
              <span className="mt-0.5 inline-flex h-8 w-8 items-center justify-center rounded-full border border-[#ffd7c6] bg-[#fff2ea] text-orange">
                <Sparkles className="h-4 w-4" />
              </span>
              <div>
                <p className="text-sm font-semibold text-primary">Start from scratch</p>
                <p className="text-xs text-secondary">Build a new funnel with the 4-step guided wizard.</p>
              </div>
            </div>
            <ArrowRight className="relative z-10 h-4 w-4 text-secondary transition-transform group-hover:translate-x-0.5 group-hover:text-primary" />
          </button>

          {!isLoadingOffers && !hasOffers ? (
            <div className="rounded-card border-[1.5px] border-[#f0d8cc] bg-[#fff8f4] px-4 py-3 text-left">
              <p className="text-sm text-secondary">
                You need an offer before creating a funnel. Create one first in the offer intake wizard.
              </p>
              <Link href="/offers/new" className="mt-2 inline-flex text-sm font-semibold text-orange hover:underline">
                Create an offer
              </Link>
            </div>
          ) : null}

          {offersError ? (
            <p className="rounded-input border border-[#f0d8cc] bg-[#fff7f4] px-3 py-2 text-sm text-status-error-text">
              {offersError}
            </p>
          ) : null}

          <div className="flex w-full items-center justify-between rounded-card border-[1.5px] border-border bg-card px-4 py-4 opacity-80">
            <div className="flex items-start gap-3">
              <span className="mt-0.5 inline-flex h-8 w-8 items-center justify-center rounded-full border border-border bg-surface text-muted">
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
