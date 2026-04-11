"use client";

import { useAuth, useUser } from "@clerk/nextjs";
import { ChevronsUpDownIcon, ExternalLink, LayoutGrid, List, MoreVertical, Pencil, Plus, RefreshCw, Search, Settings, Trash2 } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";

import { NewFunnelModal } from "@/components/dashboard/NewFunnelModal";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import {
  Combobox,
  ComboboxContent,
  ComboboxEmpty,
  ComboboxGroup,
  ComboboxItem,
  ComboboxList,
  ComboboxSeparator,
  ComboboxTrigger,
} from "@/components/ui/combobox";
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { api } from "@/lib/api";

type FunnelApi = {
  id: string;
  offer_id: string;
  name: string;
  funnel_type: "lead_generation" | "call_funnel" | "direct_sales";
  style: string;
  status: "draft" | "generating" | "ready" | "published" | "error";
  published_url: string | null;
  created_at: string;
  updated_at: string;
};

type OfferLiteApi = {
  id: string;
  name: string;
};

type FunnelProjectApi = {
  files: Record<string, unknown>;
};

type FunnelPreview = {
  path: string;
  snippet: string;
};

type FunnelActionTarget = {
  id: string;
  name: string;
};

type SortBy = "last_edited" | "last_viewed" | "created" | "name";
type ViewMode = "grid" | "list";

const VIEW_MODE_STORAGE_KEY = "funnels-view-mode";
const FUNNEL_NAME_MAX_LENGTH = 255;

const sortOptions: Array<{ value: SortBy; label: string }> = [
  { value: "last_edited", label: "Last edited" },
  { value: "last_viewed", label: "Last viewed" },
  { value: "created", label: "Created" },
  { value: "name", label: "Name" },
];

const statusOptions: Array<{ value: string; label: string }> = [
  { value: "any_status", label: "Any status" },
  { value: "draft", label: "Draft" },
  { value: "published", label: "Published" },
  { value: "error", label: "Error" },
];

const typeOptions: Array<{ value: string; label: string }> = [
  { value: "any_type", label: "Any type" },
  { value: "lead_generation", label: "Lead generation" },
  { value: "call_funnel", label: "Call funnel" },
  { value: "direct_sales", label: "Direct sales" },
];

const creatorOptions = [{ value: "all_creators", label: "All creators" }];

const comboboxItemClass = "data-selected:bg-[#eaf4ff] data-selected:text-[#2f6ea8]";

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

function formatEditedAgo(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "Edited -";
  }

  const diffMs = Math.max(0, Date.now() - date.getTime());
  const minuteMs = 60 * 1000;
  const hourMs = 60 * minuteMs;
  const dayMs = 24 * hourMs;
  const weekMs = 7 * dayMs;
  const monthMs = 30 * dayMs;

  function withUnit(amount: number, singular: string, plural: string): string {
    return `Edited ${amount} ${amount === 1 ? singular : plural} ago`;
  }

  if (diffMs < hourMs) {
    const minutes = Math.max(1, Math.floor(diffMs / minuteMs));
    return withUnit(minutes, "min", "mins");
  }

  if (diffMs < dayMs) {
    const hours = Math.floor(diffMs / hourMs);
    return withUnit(hours, "hr", "hrs");
  }

  if (diffMs < weekMs) {
    const days = Math.floor(diffMs / dayMs);
    return withUnit(days, "day", "days");
  }

  if (diffMs < monthMs) {
    const weeks = Math.floor(diffMs / weekMs);
    return withUnit(weeks, "week", "weeks");
  }

  const months = Math.floor(diffMs / monthMs);
  return withUnit(months, "month", "months");
}

function formatFunnelType(value: FunnelApi["funnel_type"]): string {
  if (value === "lead_generation") {
    return "Lead generation";
  }
  if (value === "call_funnel") {
    return "Call funnel";
  }
  return "Direct sales";
}

function normalizeStatus(value: FunnelApi["status"]): "draft" | "published" | "error" {
  if (value === "published") {
    return "published";
  }
  if (value === "error") {
    return "error";
  }
  return "draft";
}

function formatStatus(value: "draft" | "published" | "error"): string {
  return value.charAt(0).toUpperCase() + value.slice(1);
}

function getStatusTone(status: "draft" | "published" | "error"): string {
  if (status === "published") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }
  if (status === "error") {
    return "border-rose-200 bg-rose-50 text-rose-700";
  }
  return "border-border bg-muted/40 text-secondary";
}

function bySort(a: FunnelApi, b: FunnelApi, sortBy: SortBy): number {
  if (sortBy === "name") {
    return a.name.localeCompare(b.name);
  }

  if (sortBy === "created") {
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  }

  if (sortBy === "last_viewed") {
    return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
  }

  return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
}

function readFileCode(files: Record<string, unknown>, path: string): string | null {
  const file = files[path];

  if (typeof file === "string") {
    return file;
  }

  if (file && typeof file === "object" && "code" in file) {
    const code = (file as { code?: unknown }).code;
    if (typeof code === "string") {
      return code;
    }
  }

  return null;
}

function resolveImportPathCandidates(importPath: string): string[] {
  let normalized = importPath.trim();

  if (normalized.startsWith("@/")) {
    normalized = `/src/${normalized.slice(2)}`;
  } else if (normalized.startsWith("./")) {
    normalized = `/src/${normalized.slice(2)}`;
  } else if (normalized.startsWith("../")) {
    normalized = `/${normalized.slice(3)}`;
  }

  if (!normalized.startsWith("/")) {
    normalized = `/${normalized}`;
  }

  if (/\.[a-z]+$/i.test(normalized)) {
    return [normalized];
  }

  return [
    `${normalized}.tsx`,
    `${normalized}.ts`,
    `${normalized}.jsx`,
    `${normalized}.js`,
    `${normalized}/index.tsx`,
    `${normalized}/index.ts`,
    `${normalized}/index.jsx`,
    `${normalized}/index.js`,
  ];
}

function extractCodeSnippet(code: string): string {
  const nonEmpty = code
    .split(/\r?\n/)
    .map((line) => line.replaceAll("\t", "  ").trimEnd())
    .filter((line) => line.trim().length > 0)
    .slice(0, 8);

  return nonEmpty.map((line, index) => `${String(index + 1).padStart(2, "0")}  ${line}`).join("\n");
}

function buildFunnelPreview(files: Record<string, unknown>): FunnelPreview | null {
  const appCode = readFileCode(files, "/src/App.tsx");

  if (appCode) {
    const imports = new Map<string, string>();
    const importRegex = /^import\s+([A-Za-z0-9_]+)\s+from\s+["']([^"']+)["']/gm;
    let importMatch = importRegex.exec(appCode);
    while (importMatch) {
      imports.set(importMatch[1], importMatch[2]);
      importMatch = importRegex.exec(appCode);
    }

    const defaultRouteMatch = appCode.match(/<Route[^>]*path=["']\/["'][^>]*element=\{\s*<([A-Za-z0-9_]+)/);
    const defaultComponent = defaultRouteMatch?.[1];

    if (defaultComponent) {
      const importPath = imports.get(defaultComponent);
      if (importPath) {
        const candidates = resolveImportPathCandidates(importPath);
        for (const candidate of candidates) {
          const candidateCode = readFileCode(files, candidate);
          if (candidateCode) {
            return {
              path: candidate,
              snippet: extractCodeSnippet(candidateCode),
            };
          }
        }
      }
    }

    return {
      path: "/src/App.tsx",
      snippet: extractCodeSnippet(appCode),
    };
  }

  const fallbackPaths = [
    "/src/pages/PreSell.tsx",
    "/src/pages/VSL.tsx",
    "/src/pages/CallBooking.tsx",
    "/src/pages/Checkout.tsx",
  ];

  for (const path of fallbackPaths) {
    const code = readFileCode(files, path);
    if (code) {
      return {
        path,
        snippet: extractCodeSnippet(code),
      };
    }
  }

  return null;
}

export default function FunnelsPage() {
  const router = useRouter();
  const { getToken } = useAuth();
  const { user } = useUser();

  const [isModalOpen, setIsModalOpen] = useState(false);

  const [funnels, setFunnels] = useState<FunnelApi[]>([]);
  const [offerNameById, setOfferNameById] = useState<Record<string, string>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [previewByFunnelId, setPreviewByFunnelId] = useState<Record<string, FunnelPreview | null>>({});
  const [previewLoadingByFunnelId, setPreviewLoadingByFunnelId] = useState<Record<string, boolean>>({});

  const [query, setQuery] = useState("");
  const [sortBy, setSortBy] = useState<SortBy>("last_edited");
  const [statusFilter, setStatusFilter] = useState("any_status");
  const [typeFilter, setTypeFilter] = useState("any_type");
  const [offerFilter, setOfferFilter] = useState("any_offer");
  const [creatorFilter] = useState("all_creators");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");

  const [activeFunnel, setActiveFunnel] = useState<FunnelActionTarget | null>(null);
  const [isRenameOpen, setIsRenameOpen] = useState(false);
  const [renameValue, setRenameValue] = useState("");
  const [isRenaming, setIsRenaming] = useState(false);

  const [isDeleteWarningOpen, setIsDeleteWarningOpen] = useState(false);
  const [isDeleteConfirmOpen, setIsDeleteConfirmOpen] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState("");
  const [isDeleting, setIsDeleting] = useState(false);

  const trimmedRenameValue = renameValue.trim();
  const isRenameUnchanged = activeFunnel ? trimmedRenameValue === activeFunnel.name.trim() : true;
  const renameValidationMessage =
    trimmedRenameValue.length === 0
      ? "Name is required."
      : trimmedRenameValue.length > FUNNEL_NAME_MAX_LENGTH
        ? `Name must be ${FUNNEL_NAME_MAX_LENGTH} characters or less.`
        : null;
  const canSaveRename = !isRenaming && !renameValidationMessage && !isRenameUnchanged;

  useEffect(() => {
    const stored = typeof window !== "undefined" ? window.localStorage.getItem(VIEW_MODE_STORAGE_KEY) : null;
    if (stored === "grid" || stored === "list") {
      setViewMode(stored);
    }
  }, []);

  useEffect(() => {
    if (typeof window !== "undefined") {
      window.localStorage.setItem(VIEW_MODE_STORAGE_KEY, viewMode);
    }
  }, [viewMode]);

  useEffect(() => {
    let cancelled = false;

    async function loadFunnels() {
      setIsLoading(true);
      setError(null);

      try {
        const token = await getToken();
        const [funnelResponse, offersResponse] = await Promise.all([
          api.get<FunnelApi[]>("/funnels", token),
          api.get<OfferLiteApi[]>("/offers", token),
        ]);

        if (cancelled) {
          return;
        }

        const safeFunnels = Array.isArray(funnelResponse) ? funnelResponse : [];
        const safeOffers = Array.isArray(offersResponse) ? offersResponse : [];

        const nextOfferNames: Record<string, string> = {};
        for (const offer of safeOffers) {
          nextOfferNames[String(offer.id)] = offer.name || "Untitled offer";
        }

        setFunnels(safeFunnels);
        setOfferNameById(nextOfferNames);
      } catch (loadError) {
        if (cancelled) {
          return;
        }

        setError(loadError instanceof Error ? loadError.message : "Unable to load funnels.");
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadFunnels();

    return () => {
      cancelled = true;
    };
  }, [getToken]);

  const offerFilterOptions = useMemo(() => {
    const uniqueOffers = Array.from(
      new Map(
        funnels
          .map((funnel) => {
            const offerId = String(funnel.offer_id);
            return [offerId, offerNameById[offerId] || "Unknown offer"] as const;
          })
          .filter(([offerId]) => Boolean(offerId)),
      ).entries(),
    ).map(([value, label]) => ({ value, label }));

    uniqueOffers.sort((a, b) => a.label.localeCompare(b.label));

    return [{ value: "any_offer", label: "Any offer" }, ...uniqueOffers];
  }, [funnels, offerNameById]);

  const filteredFunnels = useMemo(() => {
    const normalized = query.trim().toLowerCase();

    const results = funnels.filter((funnel) => {
      const uiStatus = normalizeStatus(funnel.status);

      if (statusFilter !== "any_status" && uiStatus !== statusFilter) {
        return false;
      }

      if (typeFilter !== "any_type" && funnel.funnel_type !== typeFilter) {
        return false;
      }

      if (offerFilter !== "any_offer" && String(funnel.offer_id) !== offerFilter) {
        return false;
      }

      if (!normalized) {
        return true;
      }

      const haystack = [
        funnel.name,
        funnel.style,
        formatFunnelType(funnel.funnel_type),
        offerNameById[String(funnel.offer_id)] || "",
      ]
        .join(" ")
        .toLowerCase();

      return haystack.includes(normalized);
    });

    return [...results].sort((a, b) => bySort(a, b, sortBy));
  }, [funnels, statusFilter, typeFilter, offerFilter, query, offerNameById, sortBy]);

  const previewTargets = useMemo(() => {
    return filteredFunnels.slice(0, 24).map((funnel) => funnel.id);
  }, [filteredFunnels]);

  async function loadSinglePreview(funnelId: string, token: string | null): Promise<FunnelPreview | null> {
    const project = await api.get<FunnelProjectApi>(`/funnel-projects/${funnelId}`, token);
    return buildFunnelPreview(project.files || {});
  }

  useEffect(() => {
    const pendingIds = previewTargets.filter(
      (funnelId) => previewByFunnelId[funnelId] === undefined && !previewLoadingByFunnelId[funnelId],
    );

    if (pendingIds.length === 0) {
      return;
    }

    let cancelled = false;

    setPreviewLoadingByFunnelId((current) => {
      const next = { ...current };
      for (const funnelId of pendingIds) {
        next[funnelId] = true;
      }
      return next;
    });

    async function loadPreviews() {
      try {
        const token = await getToken();

        await Promise.all(
          pendingIds.map(async (funnelId) => {
            try {
              const preview = await loadSinglePreview(funnelId, token);

              if (!cancelled) {
                setPreviewByFunnelId((current) => ({
                  ...current,
                  [funnelId]: preview,
                }));
              }
            } catch {
              if (!cancelled) {
                setPreviewByFunnelId((current) => ({
                  ...current,
                  [funnelId]: null,
                }));
              }
            } finally {
              if (!cancelled) {
                setPreviewLoadingByFunnelId((current) => ({
                  ...current,
                  [funnelId]: false,
                }));
              }
            }
          }),
        );
      } catch {
        if (!cancelled) {
          setPreviewLoadingByFunnelId((current) => {
            const next = { ...current };
            for (const funnelId of pendingIds) {
              next[funnelId] = false;
            }
            return next;
          });
        }
      }
    }

    void loadPreviews();

    return () => {
      cancelled = true;
    };
  }, [getToken, previewByFunnelId, previewLoadingByFunnelId, previewTargets]);

  async function retryPreview(funnelId: string) {
    setPreviewLoadingByFunnelId((current) => ({ ...current, [funnelId]: true }));

    try {
      const token = await getToken();
      const preview = await loadSinglePreview(funnelId, token);
      setPreviewByFunnelId((current) => ({ ...current, [funnelId]: preview }));
    } catch {
      toast.error("Could not refresh preview right now.");
    } finally {
      setPreviewLoadingByFunnelId((current) => ({ ...current, [funnelId]: false }));
    }
  }

  const hasSearchQuery = query.trim().length > 0;
  const isDefaultSort = sortBy === "last_edited";
  const isFiltered =
    hasSearchQuery ||
    !isDefaultSort ||
    statusFilter !== "any_status" ||
    typeFilter !== "any_type" ||
    offerFilter !== "any_offer";
  const showNoFunnelsState =
    funnels.length === 0 &&
    !hasSearchQuery &&
    isDefaultSort &&
    statusFilter === "any_status" &&
    typeFilter === "any_type" &&
    offerFilter === "any_offer";

  const resultLabel = isLoading ? "Loading..." : `${filteredFunnels.length} funnel${filteredFunnels.length === 1 ? "" : "s"}`;

  const isDeleteConfirmationValid = deleteConfirmation.trim() === "CONFIRM";

  function openFunnelInNewTab(funnelId: string) {
    window.open(`/builder/${funnelId}`, "_blank", "noopener,noreferrer");
  }

  function startRenameFunnel(funnel: FunnelApi) {
    setActiveFunnel({ id: funnel.id, name: funnel.name });
    setRenameValue(funnel.name);
    setIsRenameOpen(true);
  }

  function startDeleteFunnel(funnel: FunnelApi) {
    setActiveFunnel({ id: funnel.id, name: funnel.name });
    setDeleteConfirmation("");
    setIsDeleteWarningOpen(true);
  }

  async function renameFunnel() {
    if (!activeFunnel) {
      return;
    }

    const nextName = trimmedRenameValue;
    if (!nextName) {
      toast.error("Funnel name cannot be empty.");
      return;
    }

    setIsRenaming(true);

    try {
      const token = await getToken();
      const updated = await api.patch<FunnelApi, { name: string }>(`/funnels/${activeFunnel.id}`, { name: nextName }, token);

      setFunnels((current) =>
        current.map((funnel) =>
          funnel.id === activeFunnel.id
            ? {
                ...funnel,
                name: updated.name,
                updated_at: updated.updated_at,
              }
            : funnel,
        ),
      );

      setIsRenameOpen(false);
      setActiveFunnel(null);
      setRenameValue("");
      toast.success("Funnel renamed.");
    } catch (error) {
      const message = error instanceof Error ? error.message.toLowerCase() : "";
      if (message.includes("not found")) {
        toast.error("This funnel no longer exists.");
      } else {
        toast.error("Could not rename this funnel. Please try again.");
      }
    } finally {
      setIsRenaming(false);
    }
  }

  async function deleteFunnel() {
    if (!activeFunnel) {
      return;
    }

    setIsDeleting(true);

    try {
      const token = await getToken();
      await api.del<void>(`/funnels/${activeFunnel.id}`, token);

      setFunnels((current) => current.filter((funnel) => funnel.id !== activeFunnel.id));
      setPreviewByFunnelId((current) => {
        const next = { ...current };
        delete next[activeFunnel.id];
        return next;
      });
      setPreviewLoadingByFunnelId((current) => {
        const next = { ...current };
        delete next[activeFunnel.id];
        return next;
      });

      setIsDeleteConfirmOpen(false);
      setIsDeleteWarningOpen(false);
      setDeleteConfirmation("");
      setActiveFunnel(null);
      toast.success("Funnel deleted permanently.");
    } catch (error) {
      const message = error instanceof Error ? error.message.toLowerCase() : "";
      if (message.includes("not found")) {
        toast.error("This funnel no longer exists.");
      } else {
        toast.error("Could not delete this funnel. Please try again.");
      }
    } finally {
      setIsDeleting(false);
    }
  }

  return (
    <>
      <section className="animate-fade-up w-full space-y-5">
        <div className="flex flex-col items-start justify-between gap-2 sm:flex-row sm:items-center sm:gap-3">
          <h1 className="text-[34px] leading-[0.95] font-bold tracking-[-0.03em] text-primary sm:text-[40px]">Funnels</h1>
          <Badge
            variant="outline"
            className={`h-7 rounded-pill px-3 text-xs font-medium ${
              isFiltered
                ? "border-[#c8dcf5] bg-[#eaf4ff] text-[#3d6e9e]"
                : "border-[#dbd8d2] bg-[#f7f5f2] text-[#94908a]"
            }`}
          >
            <span className="tabular-nums">{resultLabel}</span>
          </Badge>
        </div>

        <div className="w-full">
          <div className="grid grid-cols-1 gap-2.5 sm:grid-cols-2 xl:grid-cols-[minmax(0,1fr)_auto_auto_auto_auto_auto_auto]">
            <div className="relative sm:col-span-2 xl:col-span-1">
              <div className="pointer-events-none absolute inset-y-0 left-3 flex items-center">
                <Search className="h-4 w-4 text-[#a39f98]" />
              </div>
              <Input
                aria-label="Search funnels"
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="Search funnels..."
                className="h-9 rounded-[12px] border border-[#d8d4ce] bg-transparent pl-9 text-sm placeholder:text-[#a39f98]"
              />
            </div>

            <Combobox data={offerFilterOptions} type="offer" value={offerFilter} onValueChange={setOfferFilter}>
              <ComboboxTrigger
                aria-label="Filter by offer"
                className="h-9 min-w-[174px] rounded-[12px] border border-[#d8d4ce] bg-transparent text-sm font-normal text-[#3d3a36] hover:border-[#bcb7b0] hover:bg-transparent aria-expanded:bg-transparent"
              >
                <span className="flex w-full items-center justify-between gap-2">
                  {offerFilterOptions.find((option) => option.value === offerFilter)?.label ?? "Any offer"}
                  <ChevronsUpDownIcon className="size-4 shrink-0 text-muted-foreground" />
                </span>
              </ComboboxTrigger>
              <ComboboxContent popoverOptions={{ align: "start", style: { width: "min(280px, calc(100vw - 24px))" } }}>
                <ComboboxList>
                  <ComboboxEmpty />
                  <p className="px-2 py-1 text-xs font-semibold uppercase tracking-[0.06em] text-[#8f8a83]">Offer</p>
                  <ComboboxSeparator className="my-1 bg-[#ece9e4]" />
                  <ComboboxGroup>
                    {offerFilterOptions.map((option) => (
                      <ComboboxItem
                        key={option.value}
                        value={option.value}
                        data-checked={offerFilter === option.value}
                        className={comboboxItemClass}
                      >
                        {option.label}
                      </ComboboxItem>
                    ))}
                  </ComboboxGroup>
                </ComboboxList>
              </ComboboxContent>
            </Combobox>

            <Combobox data={statusOptions} type="status" value={statusFilter} onValueChange={setStatusFilter}>
              <ComboboxTrigger
                aria-label="Filter by status"
                className="h-9 min-w-[164px] rounded-[12px] border border-[#d8d4ce] bg-transparent text-sm font-normal text-[#3d3a36] hover:border-[#bcb7b0] hover:bg-transparent aria-expanded:bg-transparent"
              >
                <span className="flex w-full items-center justify-between gap-2">
                  {statusOptions.find((option) => option.value === statusFilter)?.label ?? "Any status"}
                  <ChevronsUpDownIcon className="size-4 shrink-0 text-muted-foreground" />
                </span>
              </ComboboxTrigger>
              <ComboboxContent>
                <ComboboxList>
                  <ComboboxEmpty />
                  <p className="px-2 py-1 text-xs font-semibold uppercase tracking-[0.06em] text-[#8f8a83]">Status</p>
                  <ComboboxSeparator className="my-1 bg-[#ece9e4]" />
                  <ComboboxGroup>
                    {statusOptions.map((option) => (
                      <ComboboxItem
                        key={option.value}
                        value={option.value}
                        data-checked={statusFilter === option.value}
                        className={comboboxItemClass}
                      >
                        {option.label}
                      </ComboboxItem>
                    ))}
                  </ComboboxGroup>
                </ComboboxList>
              </ComboboxContent>
            </Combobox>

            <Combobox data={typeOptions} type="type" value={typeFilter} onValueChange={setTypeFilter}>
              <ComboboxTrigger
                aria-label="Filter by funnel type"
                className="h-9 min-w-[164px] rounded-[12px] border border-[#d8d4ce] bg-transparent text-sm font-normal text-[#3d3a36] hover:border-[#bcb7b0] hover:bg-transparent aria-expanded:bg-transparent"
              >
                <span className="flex w-full items-center justify-between gap-2">
                  {typeOptions.find((option) => option.value === typeFilter)?.label ?? "Any type"}
                  <ChevronsUpDownIcon className="size-4 shrink-0 text-muted-foreground" />
                </span>
              </ComboboxTrigger>
              <ComboboxContent>
                <ComboboxList>
                  <ComboboxEmpty />
                  <p className="px-2 py-1 text-xs font-semibold uppercase tracking-[0.06em] text-[#8f8a83]">Funnel Type</p>
                  <ComboboxSeparator className="my-1 bg-[#ece9e4]" />
                  <ComboboxGroup>
                    {typeOptions.map((option) => (
                      <ComboboxItem
                        key={option.value}
                        value={option.value}
                        data-checked={typeFilter === option.value}
                        className={comboboxItemClass}
                      >
                        {option.label}
                      </ComboboxItem>
                    ))}
                  </ComboboxGroup>
                </ComboboxList>
              </ComboboxContent>
            </Combobox>

            <Combobox data={sortOptions} type="sort" value={sortBy} onValueChange={(value) => setSortBy(value as SortBy)}>
              <ComboboxTrigger
                aria-label="Sort funnels"
                className="h-9 min-w-[154px] rounded-[12px] border border-[#d8d4ce] bg-transparent text-sm font-normal text-[#3d3a36] hover:border-[#bcb7b0] hover:bg-transparent aria-expanded:bg-transparent"
              >
                <span className="flex w-full items-center justify-between gap-2">
                  {sortOptions.find((option) => option.value === sortBy)?.label ?? "Sort by"}
                  <ChevronsUpDownIcon className="size-4 shrink-0 text-muted-foreground" />
                </span>
              </ComboboxTrigger>
              <ComboboxContent>
                <ComboboxList>
                  <ComboboxEmpty />
                  <p className="px-2 py-1 text-xs font-semibold uppercase tracking-[0.06em] text-[#8f8a83]">Sort By</p>
                  <ComboboxSeparator className="my-1 bg-[#ece9e4]" />
                  <ComboboxGroup>
                    {sortOptions.map((option) => (
                      <ComboboxItem
                        key={option.value}
                        value={option.value}
                        data-checked={sortBy === option.value}
                        className={comboboxItemClass}
                      >
                        {option.label}
                      </ComboboxItem>
                    ))}
                  </ComboboxGroup>
                </ComboboxList>
              </ComboboxContent>
            </Combobox>

            <Combobox data={creatorOptions} type="creator" value={creatorFilter} onValueChange={() => {}}>
              <ComboboxTrigger
                aria-label="Filter by creator"
                className="h-9 min-w-[174px] rounded-[12px] border border-[#d8d4ce] bg-transparent text-sm font-normal text-[#807b74] opacity-100 hover:border-[#bcb7b0] hover:bg-transparent aria-expanded:bg-transparent"
              >
                <span className="flex w-full items-center justify-between gap-2">
                  {creatorOptions.find((option) => option.value === creatorFilter)?.label ?? "All creators"}
                  <ChevronsUpDownIcon className="size-4 shrink-0 text-muted-foreground" />
                </span>
              </ComboboxTrigger>
              <ComboboxContent popoverOptions={{ align: "start", style: { width: "min(240px, calc(100vw - 24px))" } }}>
                <ComboboxList>
                  <p className="px-2 py-1 text-xs font-semibold uppercase tracking-[0.06em] text-[#8f8a83]">Creators</p>
                  <ComboboxSeparator className="my-1 bg-[#ece9e4]" />
                  <ComboboxGroup>
                    <ComboboxItem value="all_creators" disabled data-checked className={comboboxItemClass}>
                      All creators
                    </ComboboxItem>
                    <ComboboxItem value="current_user" disabled className={comboboxItemClass}>
                      {user?.fullName ?? user?.firstName ?? "Current user"} (You)
                    </ComboboxItem>
                  </ComboboxGroup>
                  <p className="px-2 py-2 text-[11px] text-[#9b968f]">Creator filter coming soon</p>
                </ComboboxList>
              </ComboboxContent>
            </Combobox>

            <div className="flex items-center justify-start sm:justify-end">
              <ToggleGroup
                type="single"
                aria-label="Funnels view mode"
                value={viewMode}
                onValueChange={(value) => {
                  if (value === "grid" || value === "list") {
                    setViewMode(value);
                  }
                }}
                className="h-9 rounded-[12px] border border-[#d8d4ce] bg-transparent p-1"
              >
                <ToggleGroupItem
                  value="grid"
                  aria-label="Grid view"
                  className="h-full w-8 rounded-[8px] text-[#87827b] data-[state=on]:bg-[#f1eeea] data-[state=on]:text-[#3d3a36]"
                >
                  <LayoutGrid className="h-4 w-4" />
                </ToggleGroupItem>
                <ToggleGroupItem
                  value="list"
                  aria-label="List view"
                  className="h-full w-8 rounded-[8px] text-[#87827b] data-[state=on]:bg-[#f1eeea] data-[state=on]:text-[#3d3a36]"
                >
                  <List className="h-4 w-4" />
                </ToggleGroupItem>
              </ToggleGroup>
            </div>
          </div>
        </div>

        {error ? (
          <div className="rounded-[14px] border border-[#f2d7cc] bg-[#fff8f4] px-4 py-3 text-sm text-status-error-text">
            {error}
          </div>
        ) : null}

        <div className="w-full">
          {isLoading ? (
            viewMode === "grid" ? (
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
                {Array.from({ length: 12 }).map((_, index) => (
                  <Card key={index} className="overflow-hidden rounded-[14px] border border-[#d9d6d1] bg-[#f4f2ef] py-0 shadow-none ring-0">
                    <div className="h-[148px] border-b border-[#e2dfda] bg-[#ece8e2] p-3">
                      <Skeleton className="h-full w-full rounded-[10px]" />
                    </div>
                    <div className="space-y-2 px-4 py-3">
                      <Skeleton className="h-5 w-[72%] rounded-[8px]" />
                      <Skeleton className="h-4 w-[58%] rounded-[7px]" />
                      <Skeleton className="h-4 w-[46%] rounded-[7px]" />
                    </div>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="space-y-2">
                {Array.from({ length: 10 }).map((_, index) => (
                  <Skeleton key={index} className="h-[66px] w-full rounded-[10px]" />
                ))}
              </div>
            )
          ) : filteredFunnels.length === 0 ? (
            showNoFunnelsState ? (
              <div className="px-6 py-14 text-center">
                <p className="text-base font-semibold tracking-[-0.01em] text-primary">No funnels yet</p>
                <p className="mt-1 text-sm text-[#6f6a63]">Create your first funnel to start building pages.</p>
                <div className="mt-4 flex items-center justify-center">
                  <button
                    type="button"
                    onClick={() => setIsModalOpen(true)}
                    className="inline-flex h-10 items-center rounded-[10px] border border-[#d8d4ce] bg-[#fff] px-4 text-sm font-semibold text-primary transition-colors hover:bg-[#f7f5f2]"
                  >
                    Create new funnel
                  </button>
                </div>
              </div>
            ) : (
              <div className="px-6 py-14 text-center">
                <p className="text-base font-semibold tracking-[-0.01em] text-primary">No matching funnels</p>
                <p className="mt-1 text-sm text-[#6f6a63]">Try another search term or clear current filters.</p>
                <div className="mt-4 flex items-center justify-center">
                  <button
                    type="button"
                    onClick={() => {
                      setQuery("");
                      setSortBy("last_edited");
                      setStatusFilter("any_status");
                      setTypeFilter("any_type");
                      setOfferFilter("any_offer");
                    }}
                    className="inline-flex h-10 items-center rounded-[10px] border border-[#f2b9a1] bg-[#fff7f3] px-4 text-sm font-medium text-[#a24a24] transition-colors hover:bg-[#ffefe8]"
                  >
                    Clear filters
                  </button>
                </div>
              </div>
            )
          ) : viewMode === "grid" ? (
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
              <button
                type="button"
                onClick={() => setIsModalOpen(true)}
                className="group block rounded-[10px] border-2 border-dashed border-[#c7c3bd] bg-transparent text-left transition-colors hover:border-[#afa9a2] hover:bg-[#fff4ef]"
              >
                <Card className="h-full min-h-[220px] justify-center rounded-[10px] bg-transparent py-0 shadow-none ring-0">
                  <Plus className="mx-auto h-8 w-8 text-[#d46a3a] transition-colors group-hover:text-[#c45523]" />
                  <p className="text-center text-[18px] font-semibold tracking-[-0.02em] text-primary">Create new funnel</p>
                </Card>
              </button>

              {filteredFunnels.map((funnel) => {
                const offerLabel = offerNameById[String(funnel.offer_id)] || "Unknown offer";
                const preview = previewByFunnelId[funnel.id];
                const isPreviewLoading = previewLoadingByFunnelId[funnel.id] === true;
                const displayStatus = normalizeStatus(funnel.status);

                return (
                  <Card
                    key={funnel.id}
                    role="button"
                    tabIndex={0}
                    aria-label={`Open funnel ${funnel.name}`}
                    onClick={() => router.push(`/builder/${funnel.id}`)}
                    onKeyDown={(event) => {
                      if (event.target !== event.currentTarget) {
                        return;
                      }

                      if (event.key === "Enter" || event.key === " ") {
                        event.preventDefault();
                        router.push(`/builder/${funnel.id}`);
                      }
                    }}
                    className="group overflow-hidden rounded-[14px] border border-[#d9d6d1] bg-[#f5f4f2] py-0 shadow-none ring-0 transition-colors hover:border-[#cfcac3]"
                  >
                      <div className="relative h-[158px] border-b border-[#e2dfda] bg-[#f4f2ef]">
                        <div className="absolute inset-x-2 top-2 z-10 flex items-center justify-between gap-2">
                          <Badge
                            variant="outline"
                            className="h-6 rounded-pill border-[#d8d4ce] bg-[#f7f5f2] px-2.5 text-[11px] font-semibold text-[#5f5a54]"
                          >
                            {formatFunnelType(funnel.funnel_type)}
                          </Badge>
                          <Badge variant="outline" className={`h-6 rounded-pill px-2.5 text-[11px] font-semibold ${getStatusTone(displayStatus)}`}>
                            {formatStatus(displayStatus)}
                          </Badge>
                        </div>

                        <div className="h-full p-3 pt-10">
                          {isPreviewLoading ? (
                            <div className="space-y-2">
                              <Skeleton className="h-3 w-[88%] rounded-[6px]" />
                              <Skeleton className="h-3 w-full rounded-[6px]" />
                              <Skeleton className="h-3 w-[90%] rounded-[6px]" />
                              <Skeleton className="h-3 w-[82%] rounded-[6px]" />
                            </div>
                          ) : preview ? (
                            <pre className="max-h-[92px] overflow-hidden text-[10px] leading-relaxed text-[#5e5953]">
                              <code>{preview.snippet}</code>
                            </pre>
                          ) : (
                            <div className="space-y-2">
                              <p className="text-[12px] text-[#8a847d]">Preview not generated yet.</p>
                              <button
                                type="button"
                                onClick={(event) => {
                                  event.preventDefault();
                                  event.stopPropagation();
                                  void retryPreview(funnel.id);
                                }}
                                className="inline-flex items-center gap-1 rounded-[7px] border border-[#d8d4ce] bg-[#faf9f7] px-2 py-1 text-[11px] font-medium text-[#625e58] transition-colors hover:bg-[#f0ede8]"
                              >
                                <RefreshCw className="h-3 w-3" />
                                Retry preview
                              </button>
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="space-y-1.5 px-4 pb-3 pt-0">
                        <p className="line-clamp-1 text-[16px] leading-tight font-semibold tracking-[-0.015em] text-primary">
                          {funnel.name}
                        </p>
                        <p className="line-clamp-1 text-[14px] text-[#7a756e]">{offerLabel}</p>
                        <div className="flex items-center justify-between gap-1.5">
                          <p className="text-[12px] tabular-nums text-[#7a756e]">{formatEditedAgo(funnel.updated_at)}</p>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <button
                                type="button"
                                aria-label="Funnel actions"
                                onClick={(event) => event.stopPropagation()}
                                onPointerDown={(event) => event.stopPropagation()}
                                className="inline-flex h-8 w-8 items-center justify-center rounded-[8px] text-[#7a756e] transition-colors hover:bg-[#f3f1ed] hover:text-primary"
                              >
                                <MoreVertical className="h-4 w-4" />
                              </button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-48" onClick={(event) => event.stopPropagation()}>
                              <DropdownMenuItem
                                onSelect={(event) => {
                                  event.preventDefault();
                                  openFunnelInNewTab(funnel.id);
                                }}
                              >
                                <ExternalLink className="h-4 w-4" />
                                Open in a new tab
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onSelect={(event) => {
                                  event.preventDefault();
                                  startRenameFunnel(funnel);
                                }}
                              >
                                <Pencil className="h-4 w-4" />
                                Rename
                              </DropdownMenuItem>
                              <DropdownMenuItem disabled>
                                <Settings className="h-4 w-4" />
                                Settings
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                variant="destructive"
                                onSelect={(event) => {
                                  event.preventDefault();
                                  startDeleteFunnel(funnel);
                                }}
                              >
                                <Trash2 className="h-4 w-4" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                        </div>
                  </Card>
                );
              })}
            </div>
          ) : (
            <div className="overflow-hidden rounded-[14px] bg-transparent">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="h-16 px-4 text-sm font-semibold text-secondary">Funnel</TableHead>
                    <TableHead className="h-16 text-sm font-semibold text-secondary">Offer</TableHead>
                    <TableHead className="h-16 text-sm font-semibold text-secondary">Type</TableHead>
                    <TableHead className="h-16 text-sm font-semibold text-secondary">Status</TableHead>
                    <TableHead className="h-16 px-4 text-right text-sm font-semibold text-secondary">Updated</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow className="h-[66px] border-[#ebe8e3] hover:bg-[#f7f5f2]">
                    <TableCell colSpan={5} className="px-4 py-4">
                      <button
                        type="button"
                        onClick={() => setIsModalOpen(true)}
                        className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:underline"
                      >
                        <Plus className="h-4 w-4 text-[#8f8a83]" />
                        Create new funnel
                      </button>
                    </TableCell>
                  </TableRow>

                  {filteredFunnels.map((funnel) => (
                    <TableRow key={funnel.id} className="h-[66px] border-[#ebe8e3] hover:bg-[#f7f5f2]">
                      <TableCell className="px-4 py-4">
                        <Link href={`/builder/${funnel.id}`} className="block">
                          <p className="line-clamp-1 font-semibold text-primary">{funnel.name}</p>
                        </Link>
                      </TableCell>
                      <TableCell className="py-4 text-[#4f4a44]">{offerNameById[String(funnel.offer_id)] || "Unknown offer"}</TableCell>
                      <TableCell className="py-4 text-[#4f4a44]">{formatFunnelType(funnel.funnel_type)}</TableCell>
                      <TableCell className="py-4">
                        <Badge variant="outline" className={`h-7 rounded-pill px-3 text-xs font-semibold ${getStatusTone(normalizeStatus(funnel.status))}`}>
                          {formatStatus(normalizeStatus(funnel.status))}
                        </Badge>
                      </TableCell>
                      <TableCell className="px-4 py-4">
                        <div className="flex items-center justify-end gap-1.5">
                          <span className="tabular-nums text-[#4f4a44]">{formatDate(funnel.updated_at)}</span>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <button
                                type="button"
                                aria-label="Funnel actions"
                                className="inline-flex h-8 w-8 items-center justify-center rounded-[8px] text-[#7a756e] transition-colors hover:bg-[#f3f1ed] hover:text-primary"
                              >
                                <MoreVertical className="h-4 w-4" />
                              </button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end" className="w-48">
                              <DropdownMenuItem
                                onSelect={(event) => {
                                  event.preventDefault();
                                  openFunnelInNewTab(funnel.id);
                                }}
                              >
                                <ExternalLink className="h-4 w-4" />
                                Open in a new tab
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onSelect={(event) => {
                                  event.preventDefault();
                                  startRenameFunnel(funnel);
                                }}
                              >
                                <Pencil className="h-4 w-4" />
                                Rename
                              </DropdownMenuItem>
                              <DropdownMenuItem disabled>
                                <Settings className="h-4 w-4" />
                                Settings
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                variant="destructive"
                                onSelect={(event) => {
                                  event.preventDefault();
                                  startDeleteFunnel(funnel);
                                }}
                              >
                                <Trash2 className="h-4 w-4" />
                                Delete
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </div>
      </section>

      <Dialog
        open={isRenameOpen}
        onOpenChange={(open) => {
          if (isRenaming) {
            return;
          }

          setIsRenameOpen(open);
          if (!open) {
            setRenameValue("");
          }
        }}
      >
        <DialogContent className="max-w-[440px]">
          <DialogHeader>
            <DialogTitle>Rename Funnel</DialogTitle>
            <DialogDescription>Enter a new name for this funnel.</DialogDescription>
          </DialogHeader>

          <div className="mt-2">
            <Input
              value={renameValue}
              onChange={(event) => setRenameValue(event.target.value)}
              placeholder="Funnel name"
              maxLength={FUNNEL_NAME_MAX_LENGTH}
            />
            <div className="mt-2 flex items-center justify-between text-[12px]">
              <p className={renameValidationMessage ? "text-status-error-text" : "text-secondary"}>
                {renameValidationMessage ?? (isRenameUnchanged ? "No changes yet." : "Ready to save.")}
              </p>
              <p className="tabular-nums text-[#8f8a83]">{renameValue.length}/{FUNNEL_NAME_MAX_LENGTH}</p>
            </div>
          </div>

          <div className="mt-5 flex items-center justify-end gap-2">
            <button
              type="button"
              disabled={isRenaming}
              onClick={() => {
                setIsRenameOpen(false);
                setRenameValue("");
              }}
              className="inline-flex h-10 items-center rounded-[9px] border border-border bg-transparent px-4 text-sm font-semibold text-secondary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              Cancel
            </button>
            <button
              type="button"
              disabled={!canSaveRename}
              onClick={() => void renameFunnel()}
              className="inline-flex h-10 items-center rounded-[9px] bg-orange px-4 text-sm font-semibold text-white transition-colors hover:bg-[#d63500] disabled:cursor-not-allowed disabled:opacity-60"
            >
              {isRenaming ? "Saving..." : "Save"}
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
            <DialogTitle className="text-[26px] font-bold tracking-[-0.02em]">Delete {activeFunnel?.name}?</DialogTitle>
            <DialogDescription asChild className="space-y-1 text-[15px] leading-6">
              <div>
                <p>
                  This action cannot be undone. <span className="text-destructive">This will permanently delete your funnel.</span>{" "}
                  Including:
                </p>
              </div>
            </DialogDescription>
          </DialogHeader>

          <ul className="mb-7 ml-1 list-disc space-y-1 pl-5 text-[15px] text-secondary">
            <li>All generated page code</li>
            <li>All preview links</li>
            <li>Builder project files</li>
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
              className="inline-flex h-10 items-center rounded-[9px] bg-destructive px-4 text-sm font-semibold text-white transition-colors hover:bg-destructive/90"
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
                <p>Are you sure you want to delete {activeFunnel?.name}?</p>
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

          <div className="mt-2 flex items-center gap-1 text-destructive">
            <Trash2 className="h-4 w-4" />
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
              onClick={() => void deleteFunnel()}
              className="inline-flex h-10 items-center rounded-[9px] bg-destructive px-4 text-sm font-semibold text-white transition-colors hover:bg-destructive/90 disabled:cursor-not-allowed disabled:bg-destructive/40 disabled:text-white"
            >
              {isDeleting ? "Deleting..." : "Delete funnel"}
            </button>
          </div>
        </DialogContent>
      </Dialog>

      <NewFunnelModal open={isModalOpen} onOpenChange={setIsModalOpen} />
    </>
  );
}
