"use client";

import { useAuth } from "@clerk/nextjs";
import { AlertTriangle, ArrowLeft, FolderOpen } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { Badge } from "@/components/ui/badge";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";

type OfferApi = {
  id: string;
  name: string;
  industry: string;
  intake_data: {
    brand_name: string;
    offer_name: string;
    offer_one_liner: string;
    price_point: string;
    whats_included: string;
    transformation: string;
    ideal_client: string;
    pain_point: string;
  };
  updated_at: string;
  created_at: string;
};

type FunnelApi = {
  id: string;
  offer_id: string;
  name: string;
  funnel_type: string;
  style: string;
  status: string;
  created_at: string;
};

type OfferDraft = {
  name: string;
  industry: string;
  intake_data: OfferApi["intake_data"];
};

const industryOptions = [
  { id: "business_entrepreneurship", label: "Business & Entrepreneurship" },
  { id: "marketing_advertising", label: "Marketing & Advertising" },
  { id: "real_estate", label: "Real Estate" },
  { id: "finance_investing", label: "Finance & Investing" },
  { id: "health_fitness", label: "Health & Fitness" },
  { id: "beauty_aesthetics", label: "Beauty & Aesthetics" },
  { id: "relationships_dating", label: "Relationships & Dating" },
  { id: "personal_development", label: "Personal Development" },
  { id: "education_coaching", label: "Education & Coaching" },
  { id: "legal_professional_services", label: "Legal & Professional Services" },
  { id: "ecommerce_retail", label: "E-commerce & Retail" },
  { id: "technology_saas", label: "Technology & SaaS" },
  { id: "local_services", label: "Local Services" },
  { id: "other", label: "Other" },
];

const pricePointOptions = ["Under $100", "$101 - $1,000", "$1,001 - $5,000", "$5,000+"];

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "-";
  }

  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
  }).format(date);
}

function formatTime(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "--:--:--";
  }

  return new Intl.DateTimeFormat("en-US", {
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  }).format(date);
}

function formatFunnelType(value: string): string {
  const normalized = value.replaceAll("_", " ");
  return normalized.charAt(0).toUpperCase() + normalized.slice(1);
}

function resolveIndustryOption(value: string): { selected: string; custom: string } {
  const normalized = value.trim().toLowerCase();

  const byId = industryOptions.find((option) => option.id === normalized);
  if (byId) {
    return { selected: byId.id, custom: "" };
  }

  const byLabel = industryOptions.find((option) => option.label.trim().toLowerCase() === normalized);
  if (byLabel) {
    return { selected: byLabel.id, custom: "" };
  }

  return { selected: "other", custom: value };
}

function createDraftFromOffer(offer: OfferApi): OfferDraft {
  return {
    name: offer.name || "",
    industry: offer.industry || "",
    intake_data: {
      brand_name: offer.intake_data.brand_name || "",
      offer_name: offer.intake_data.offer_name || "",
      offer_one_liner: offer.intake_data.offer_one_liner || "",
      price_point: offer.intake_data.price_point || "",
      whats_included: offer.intake_data.whats_included || "",
      transformation: offer.intake_data.transformation || "",
      ideal_client: offer.intake_data.ideal_client || "",
      pain_point: offer.intake_data.pain_point || "",
    },
  };
}

export default function OfferDetailsPage() {
  const params = useParams<{ offerId: string }>();
  const router = useRouter();
  const { getToken } = useAuth();

  const offerId = String(params.offerId || "");

  const [offer, setOffer] = useState<OfferApi | null>(null);
  const [funnels, setFunnels] = useState<FunnelApi[]>([]);
  const [draft, setDraft] = useState<OfferDraft | null>(null);

  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [industrySelection, setIndustrySelection] = useState<string>("other");
  const [customIndustry, setCustomIndustry] = useState("");
  const [isLeaveDialogOpen, setIsLeaveDialogOpen] = useState(false);
  const [isDeleteWarningOpen, setIsDeleteWarningOpen] = useState(false);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      if (!offerId) {
        return;
      }

      setIsLoading(true);
      setError(null);

      try {
        const token = await getToken();
        const [offerResponse, funnelsResponse] = await Promise.all([
          api.get<OfferApi>(`/offers/${offerId}`, token),
          api.get<FunnelApi[]>("/funnels", token),
        ]);

        if (cancelled) {
          return;
        }

        const linkedFunnels = Array.isArray(funnelsResponse)
          ? funnelsResponse.filter((funnel) => String(funnel.offer_id) === offerId)
          : [];

        const nextDraft = createDraftFromOffer(offerResponse);

        const resolvedIndustry = resolveIndustryOption(nextDraft.industry);

        setOffer(offerResponse);
        setFunnels(linkedFunnels);
        setDraft(nextDraft);
        setIndustrySelection(resolvedIndustry.selected);
        setCustomIndustry(resolvedIndustry.custom);
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Unable to load offer details.");
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void load();

    return () => {
      cancelled = true;
    };
  }, [getToken, offerId]);

  const isDirty = useMemo(() => {
    if (!offer || !draft) {
      return false;
    }

    const initial = createDraftFromOffer(offer);

    return JSON.stringify(initial) !== JSON.stringify(draft);
  }, [draft, offer]);

  const isDeleteConfirmationValid = useMemo(() => {
    return deleteConfirmation.trim() === "CONFIRM";
  }, [deleteConfirmation]);

  function updateDraft(patch: Partial<OfferDraft>) {
    setDraft((current) => (current ? { ...current, ...patch } : current));
  }

  function updateIntakeField<K extends keyof OfferApi["intake_data"]>(key: K, value: string) {
    setDraft((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        intake_data: {
          ...current.intake_data,
          [key]: value,
        },
      };
    });
  }

  function updateOfferName(value: string) {
    setDraft((current) => {
      if (!current) {
        return current;
      }

      return {
        ...current,
        name: value,
        intake_data: {
          ...current.intake_data,
          offer_name: value,
        },
      };
    });
  }

  async function saveChanges() {
    if (!draft || !offerId) {
      return;
    }

    const selectedIndustryLabel =
      industrySelection === "other"
        ? customIndustry.trim()
        : (industryOptions.find((option) => option.id === industrySelection)?.label ?? industrySelection);

    const preparedIndustry = selectedIndustryLabel;
    const payload: OfferDraft = {
      name: draft.name.trim(),
      industry: preparedIndustry,
      intake_data: {
        ...draft.intake_data,
        offer_name: draft.name.trim(),
      },
    };

    setIsSaving(true);
    setError(null);

    try {
      const token = await getToken();
      const updated = await api.patch<OfferApi, OfferDraft>(`/offers/${offerId}`, payload, token);

      const refreshedDraft = createDraftFromOffer(updated);

      const resolvedIndustry = resolveIndustryOption(refreshedDraft.industry);

      setOffer(updated);
      setDraft(refreshedDraft);
      setIndustrySelection(resolvedIndustry.selected);
      setCustomIndustry(resolvedIndustry.custom);
      toast.success("Offer details saved successfully.");
    } catch (saveError) {
      const message = saveError instanceof Error ? saveError.message : "Unable to save offer changes.";
      setError(message);
      if (message.includes("400") || message.toLowerCase().includes("validation") || message.toLowerCase().includes("invalid")) {
        toast.error("Could not save changes. Please review your inputs and try again.");
      } else {
        toast.error("Something went wrong while saving. Please try again.");
      }
    } finally {
      setIsSaving(false);
    }
  }

  function cancelEdits() {
    if (!offer) {
      return;
    }

    const nextDraft = createDraftFromOffer(offer);

    const resolvedIndustry = resolveIndustryOption(nextDraft.industry);

    setDraft(nextDraft);
    setIndustrySelection(resolvedIndustry.selected);
    setCustomIndustry(resolvedIndustry.custom);
    setError(null);
  }

  function handleBackClick() {
    if (isDirty) {
      setIsLeaveDialogOpen(true);
      return;
    }

    router.push("/offers");
  }

  async function deleteOffer() {
    if (!offerId) {
      return;
    }

    setIsDeleting(true);

    try {
      const token = await getToken();
      await api.del<void>(`/offers/${offerId}`, token);
      setIsDeleteConfirmOpen(false);
      setIsDeleteWarningOpen(false);
      setDeleteConfirmation("");
      toast.success("Offer deleted permanently.");
      router.push("/offers");
    } catch {
      toast.error("Could not delete this offer. Please try again.");
    } finally {
      setIsDeleting(false);
    }
  }

  if (isLoading || !draft || !offer) {
    return (
      <section className="space-y-5 px-3 md:px-10 xl:px-60">
        <Skeleton className="h-[360px] w-full rounded-card" />
        <Skeleton className="h-[220px] w-full rounded-card" />
      </section>
    );
  }

  return (
    <section className="space-y-5 px-3 md:px-10 xl:px-60">
      <header className="flex items-center justify-between gap-3">
        <button
          type="button"
          onClick={handleBackClick}
          className="inline-flex h-9 items-center gap-2 rounded-button border border-border bg-transparent px-3 text-sm font-medium text-secondary transition-colors hover:text-primary"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to offers
        </button>
      </header>

      <div className="rounded-card border border-border bg-transparent p-5">
        <div className="mb-4 flex items-center justify-between gap-3">
          <div>
            <h1 className="text-[24px] font-semibold tracking-[-0.02em] text-primary">Offer Details</h1>
            <p className="text-sm text-secondary">Last edited {formatDate(offer.updated_at)}</p>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-x-4 gap-y-3 md:grid-cols-2">
          <label className="space-y-1">
            <span className="text-xs font-semibold uppercase tracking-[0.05em] text-[#3f3a34]">Offer Name</span>
            <Input value={draft.name} onChange={(event) => updateOfferName(event.target.value)} className="h-10" />
          </label>

          <label className="space-y-1">
            <span className="text-xs font-semibold uppercase tracking-[0.05em] text-[#3f3a34]">Created at</span>
            <p className="h-10 pt-2.5 text-[15px] font-medium text-primary">
              {formatDate(offer.created_at)} {formatTime(offer.created_at)}
            </p>
          </label>

          <label className="space-y-1">
            <span className="text-xs font-semibold uppercase tracking-[0.05em] text-[#3f3a34]">One-liner</span>
            <Input
              value={draft.intake_data.offer_one_liner}
              onChange={(event) => updateIntakeField("offer_one_liner", event.target.value)}
              className="h-10"
            />
          </label>

          <label className="space-y-1">
            <span className="text-xs font-semibold uppercase tracking-[0.05em] text-[#3f3a34]">Price point</span>
            <Select value={draft.intake_data.price_point || ""} onValueChange={(value) => updateIntakeField("price_point", value)}>
              <SelectTrigger className="h-10">
                <SelectValue placeholder="Select price point" />
              </SelectTrigger>
              <SelectContent>
                {pricePointOptions.map((option) => (
                  <SelectItem
                    key={option}
                    value={option}
                    className="focus:bg-[#eaf4ff] focus:text-[#2f6ea8] data-[state=checked]:bg-[#eaf4ff] data-[state=checked]:text-[#2f6ea8]"
                  >
                    {option}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </label>

          <label className="space-y-1">
            <span className="text-xs font-semibold uppercase tracking-[0.05em] text-[#3f3a34]">Brand Name</span>
            <Input
              value={draft.intake_data.brand_name}
              onChange={(event) => updateIntakeField("brand_name", event.target.value)}
              className="h-10"
            />
          </label>

          <div className="space-y-1">
            <span className="text-xs font-semibold uppercase tracking-[0.05em] text-[#3f3a34]">Industry</span>
            <div className="flex items-start gap-2">
              <Select
                value={industrySelection}
                onValueChange={(value) => {
                  setIndustrySelection(value);
                  if (value === "other") {
                    updateDraft({ industry: customIndustry });
                    return;
                  }
                  const label = industryOptions.find((option) => option.id === value)?.label ?? value;
                  updateDraft({ industry: label });
                }}
              >
                <SelectTrigger className="h-10 w-[50%] min-w-[180px]">
                  <SelectValue placeholder="Select industry" />
                </SelectTrigger>
                <SelectContent>
                  {industryOptions.map((option) => (
                    <SelectItem
                      key={option.id}
                      value={option.id}
                      className="focus:bg-[#eaf4ff] focus:text-[#2f6ea8] data-[state=checked]:bg-[#eaf4ff] data-[state=checked]:text-[#2f6ea8]"
                    >
                      {option.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
              {industrySelection === "other" ? (
                <Input
                  value={customIndustry}
                  onChange={(event) => {
                    const nextValue = event.target.value;
                    setCustomIndustry(nextValue);
                    updateDraft({ industry: nextValue });
                  }}
                  placeholder="Type your industry"
                  className="h-10 w-44"
                />
              ) : null}
            </div>
          </div>

          <label className="space-y-1 md:col-span-2">
            <span className="text-xs font-semibold uppercase tracking-[0.05em] text-[#3f3a34]">What&apos;s Included</span>
            <Textarea
              value={draft.intake_data.whats_included}
              onChange={(event) => updateIntakeField("whats_included", event.target.value)}
              className="min-h-20"
            />
          </label>

          <label className="space-y-1 md:col-span-2">
            <span className="text-xs font-semibold uppercase tracking-[0.05em] text-[#3f3a34]">Pain Point</span>
            <Textarea
              value={draft.intake_data.pain_point}
              onChange={(event) => updateIntakeField("pain_point", event.target.value)}
              className="min-h-20"
            />
          </label>

          <label className="space-y-1 md:col-span-2">
            <span className="text-xs font-semibold uppercase tracking-[0.05em] text-[#3f3a34]">Transformation</span>
            <Textarea
              value={draft.intake_data.transformation}
              onChange={(event) => updateIntakeField("transformation", event.target.value)}
              className="min-h-20"
            />
          </label>
        </div>

        {error ? <p className="mt-4 text-sm text-status-error-text">{error}</p> : null}

        <div className="mt-6 min-h-16 border-t border-border pt-4">
          {isDirty ? (
            <div className="flex items-center justify-end gap-2">
              <button
                type="button"
                onClick={cancelEdits}
                className="inline-flex h-10 items-center rounded-button border border-border bg-transparent px-4 text-sm font-semibold text-secondary hover:text-primary"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSaving}
                onClick={() => void saveChanges()}
                className="inline-flex h-10 items-center rounded-button bg-blue-600 px-4 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSaving ? "Saving..." : "Save"}
              </button>
            </div>
          ) : null}
        </div>
      </div>

      <div className="rounded-card border border-border bg-transparent p-5">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-lg font-semibold text-primary">Funnels</h2>
          <Badge variant="outline" className="text-xs text-muted">
            {funnels.length} funnels
          </Badge>
        </div>

        {funnels.length === 0 ? (
          <div className="flex flex-col items-center rounded-[14px] border border-dashed border-[#d6d2cc] bg-[#f8f6f3] px-5 py-8 text-center">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#ede9e2] text-[#7a756e]">
              <FolderOpen className="h-5 w-5" />
            </div>
            <p className="mt-3 text-[20px] font-semibold tracking-[-0.02em] text-primary">No funnels yet</p>
            <button
              type="button"
              onClick={() => router.push(`/funnels/new?offerId=${offerId}`)}
              className="mt-5 inline-flex h-10 items-center rounded-button bg-orange px-4 text-sm font-semibold text-white transition-colors hover:bg-[#d63500]"
            >
              Create funnel
            </button>
          </div>
        ) : (
          <div className="overflow-hidden rounded-[14px] bg-transparent">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="h-14 px-4 text-sm font-semibold text-[#6f6a63]">Funnel</TableHead>
                  <TableHead className="h-14 text-sm font-semibold text-[#6f6a63]">Type</TableHead>
                  <TableHead className="h-14 text-sm font-semibold text-[#6f6a63]">Style</TableHead>
                  <TableHead className="h-14 text-sm font-semibold text-[#6f6a63]">Status</TableHead>
                  <TableHead className="h-14 text-right text-sm font-semibold text-[#6f6a63]">Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {funnels.map((funnel) => (
                  <TableRow key={funnel.id} className="h-[64px] border-[#ebe8e3] hover:bg-[#f7f5f2]">
                    <TableCell className="px-4 py-4 font-medium text-primary">{funnel.name}</TableCell>
                    <TableCell className="py-4 text-[#4f4a44]">{formatFunnelType(funnel.funnel_type)}</TableCell>
                    <TableCell className="py-4 text-[#4f4a44]">{funnel.style.replaceAll("_", " ")}</TableCell>
                    <TableCell className="py-4 text-[#4f4a44]">{funnel.status}</TableCell>
                    <TableCell className="py-4 text-right text-[#7a756e]">{formatDate(funnel.created_at)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>

      <div className="flex items-center justify-between gap-4 rounded-card border border-border bg-transparent p-5">
        <div className="space-y-1">
          <h2 className="text-[16px] font-semibold text-primary">Delete offer</h2>
          <p className="text-[13px] leading-tight text-secondary">Permanently delete this offer and its funnels.</p>
        </div>
        <button
          type="button"
          onClick={() => setIsDeleteWarningOpen(true)}
          disabled={isDeleting}
          className="inline-flex h-10 items-center rounded-[10px] bg-[#dc2626] px-4 text-sm font-semibold text-white shadow-[0_1px_2px_rgba(16,24,40,0.35),inset_0_1px_0_rgba(255,255,255,0.18)] transition-colors hover:bg-[#c81f1f] disabled:cursor-not-allowed disabled:opacity-60"
        >
          Delete
        </button>
      </div>

      <Dialog open={isLeaveDialogOpen} onOpenChange={setIsLeaveDialogOpen}>
        <DialogContent className="max-w-[460px]">
          <DialogHeader>
            <DialogTitle>Discard unsaved changes?</DialogTitle>
            <DialogDescription>
              You have unsaved changes. If you leave now, your edits will be lost.
            </DialogDescription>
          </DialogHeader>
          <div className="mt-5 flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={() => setIsLeaveDialogOpen(false)}
              className="inline-flex h-10 items-center rounded-button bg-transparent px-4 text-sm font-semibold text-secondary hover:text-primary"
            >
              Stay
            </button>
            <button
              type="button"
              onClick={() => {
                setIsLeaveDialogOpen(false);
                router.push("/offers");
              }}
              className="inline-flex h-10 items-center rounded-button bg-black px-4 text-sm font-semibold text-white hover:bg-[#d63500]"
            >
              Leave without saving
            </button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog
        open={isDeleteWarningOpen}
        onOpenChange={(open) => {
          if (isDeleting) {
            return;
          }

          setIsDeleteWarningOpen(open);
        }}
      >
        <DialogContent className="flex min-h-[300px] max-w-[420px] flex-col gap-2">
          <DialogHeader className="mb-1">
            <DialogTitle className="text-[26px] font-bold tracking-[-0.02em]">Delete {offer.name}?</DialogTitle>
            <DialogDescription asChild className="space-y-1 text-[15px] leading-6">
              <div>
                <p>
                  This action cannot be undone. <span className="text-[#dc2626]">This will permanently delete your project.</span>{" "}
                  Including:
                </p>
              </div>
            </DialogDescription>
          </DialogHeader>

          <ul className="mb-7 ml-1 list-disc space-y-1 pl-5 text-[15px] text-secondary">
            <li>
              {funnels.length} funnel{funnels.length === 1 ? "" : "s"}
            </li>
            <li>Any published funnels made with OfferLaunch</li>
            <li>All preview links</li>
          </ul>

          <div className="mt-auto flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={() => setIsDeleteWarningOpen(false)}
              className="inline-flex h-10 items-center rounded-[9px] bg-[#faf9f7] px-4 text-sm font-medium text-primary transition-colors hover:bg-[#f0ede8]"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={() => {
                setIsDeleteWarningOpen(false);
                setDeleteConfirmation("");
                setIsDeleteConfirmOpen(true);
              }}
              className="inline-flex h-10 items-center rounded-[9px] bg-[#dc2626] px-4 text-sm font-semibold text-white transition-colors hover:bg-[#c81f1f]"
            >
              Continue
            </button>
          </div>
        </DialogContent>
      </Dialog>

      <Dialog
        open={isDeleteConfirmOpen}
        onOpenChange={(open) => {
          if (isDeleting) {
            return;
          }

          setIsDeleteConfirmOpen(open);
          if (!open) {
            setDeleteConfirmation("");
          }
        }}
      >
        <DialogContent className="flex min-h-[300px] max-w-[420px] flex-col gap-0">
          <DialogHeader className="mb-2">
            <DialogTitle className="text-[26px] font-bold tracking-[-0.02em]">Final confirmation</DialogTitle>
            <DialogDescription asChild className="space-y-1 text-[15px] leading-6">
              <div>
                <p>Are you sure you want to delete {offer.name}?</p>
                <p>Type CONFIRM below to proceed.</p>
              </div>
            </DialogDescription>
          </DialogHeader>
          <div className="mt-1 space-y-2">
            <Input
              value={deleteConfirmation}
              onChange={(event) => setDeleteConfirmation(event.target.value)}
              placeholder="Type CONFIRM"
              className="h-10"
            />
          </div>
          <div className="mt-2 flex items-center gap-1 text-[#dc2626]">
            <AlertTriangle className="h-4 w-4" />
            <p className="text-[15px]">This action is irreversible.</p>
          </div>
          <div className="mt-2 flex items-center justify-end gap-2 pt-6">
            <button
              type="button"
              disabled={isDeleting}
              onClick={() => {
                setIsDeleteConfirmOpen(false);
                setDeleteConfirmation("");
                setIsDeleteWarningOpen(true);
              }}
              className="inline-flex h-10 items-center rounded-[9px] bg-[#faf9f7] px-4 text-sm font-medium text-primary transition-colors hover:bg-[#f0ede8] disabled:cursor-not-allowed disabled:opacity-60"
            >
              Back
            </button>
            <button
              type="button"
              disabled={!isDeleteConfirmationValid || isDeleting}
              onClick={() => void deleteOffer()}
              className="inline-flex h-10 items-center rounded-[9px] bg-[#dc2626] px-4 text-sm font-semibold text-white transition-colors hover:bg-[#b42318] disabled:bg-[#f1a4a4] disabled:text-white disabled:cursor-not-allowed"
            >
              {isDeleting ? "Deleting..." : "Delete offer"}
            </button>
          </div>
        </DialogContent>
      </Dialog>
    </section>
  );
}
