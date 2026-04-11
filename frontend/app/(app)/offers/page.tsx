"use client";

import { useAuth, useUser } from "@clerk/nextjs";
import { ChevronsUpDownIcon, LayoutGrid, List, Plus, Search } from "lucide-react";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

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
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { api } from "@/lib/api";

type OfferApi = {
  id: string;
  name: string;
  industry: string;
  status: string;
  intake_data: {
    offer_name?: string;
    offer_one_liner?: string;
    price_point?: string;
  };
  created_at: string;
  updated_at: string;
};

type FunnelApi = {
  id: string;
  offer_id: string;
};

type SortBy = "last_edited" | "last_viewed" | "created" | "name";
type ViewMode = "grid" | "list";

const VIEW_MODE_STORAGE_KEY = "offers-view-mode";

const sortOptions: Array<{ value: SortBy; label: string }> = [
  { value: "last_edited", label: "Last edited" },
  { value: "last_viewed", label: "Last viewed" },
  { value: "created", label: "Created" },
  { value: "name", label: "Name" },
];

const creatorOptions = [{ value: "all_creators", label: "All creators" }];

const comboboxItemClass = "data-selected:bg-[#eaf4ff] data-selected:text-[#2f6ea8]";
const activeFilterTriggerClass =
  "border-white bg-[#9a4a1f] text-white hover:border-white hover:bg-[#9a4a1f] hover:text-white aria-expanded:border-white aria-expanded:bg-[#9a4a1f] aria-expanded:text-white";

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

function bySort(a: OfferApi, b: OfferApi, sortBy: SortBy): number {
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

export default function OffersPage() {
  const { getToken } = useAuth();
  const { user } = useUser();

  const [offers, setOffers] = useState<OfferApi[]>([]);
  const [funnelCountByOffer, setFunnelCountByOffer] = useState<Record<string, number>>({});
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [query, setQuery] = useState("");
  const [sortBy, setSortBy] = useState<SortBy>("last_edited");
  const [creatorFilter] = useState("all_creators");
  const [viewMode, setViewMode] = useState<ViewMode>("grid");

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

    async function loadOffers() {
      setIsLoading(true);
      setError(null);

      try {
        const token = await getToken();
        const [offersResponse, funnelsResponse] = await Promise.all([
          api.get<OfferApi[]>("/offers", token),
          api.get<FunnelApi[]>("/funnels", token),
        ]);

        if (cancelled) {
          return;
        }

        const safeOffers = Array.isArray(offersResponse) ? offersResponse : [];
        const safeFunnels = Array.isArray(funnelsResponse) ? funnelsResponse : [];

        const counts: Record<string, number> = {};
        for (const funnel of safeFunnels) {
          const offerId = String(funnel.offer_id || "");
          if (!offerId) {
            continue;
          }
          counts[offerId] = (counts[offerId] ?? 0) + 1;
        }

        setOffers(safeOffers);
        setFunnelCountByOffer(counts);
      } catch (loadError) {
        if (cancelled) {
          return;
        }
        setError(loadError instanceof Error ? loadError.message : "Unable to load offers.");
      } finally {
        if (!cancelled) {
          setIsLoading(false);
        }
      }
    }

    void loadOffers();

    return () => {
      cancelled = true;
    };
  }, [getToken]);

  const filteredOffers = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    const searched = normalized
      ? offers.filter((offer) => {
          return offer.name.toLowerCase().includes(normalized);
        })
      : offers;

    return [...searched].sort((a, b) => bySort(a, b, sortBy));
  }, [offers, query, sortBy]);

  const hasSearchQuery = query.trim().length > 0;
  const isDefaultSort = sortBy === "last_edited";
  const isFiltered = hasSearchQuery || !isDefaultSort;
  const showNoOffersState = offers.length === 0 && !hasSearchQuery && isDefaultSort;

  return (
    <section className="animate-fade-up w-full space-y-6">
      <div className="flex flex-col items-start justify-between gap-2 sm:flex-row sm:items-center sm:gap-3">
        <h1 className="text-[40px] leading-none font-bold tracking-[-0.03em] text-primary">Offers</h1>
        <Badge
          variant="outline"
          className={`h-7 rounded-pill px-3 text-xs font-medium ${
            isFiltered
              ? "border-[#c8dcf5] bg-[#eaf4ff] text-[#3d6e9e]"
              : "border-[#dbd8d2] bg-[#f7f5f2] text-[#94908a]"
          }`}
        >
          {isLoading ? "Loading..." : `${filteredOffers.length} offer${filteredOffers.length === 1 ? "" : "s"}`}
        </Badge>
      </div>

      <div className="w-full">
        <div className="grid grid-cols-1 items-center gap-2.5 sm:grid-cols-2 sm:gap-3 xl:grid-cols-[minmax(0,1fr)_auto_auto_auto]">
          <div className="relative sm:col-span-2 xl:col-span-1">
            <div className="pointer-events-none absolute inset-y-0 left-3 flex items-center">
              <Search className="h-4 w-4 text-[#a39f98]" />
            </div>
            <Input
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search offers..."
              className="h-9 rounded-[12px] border border-[#d8d4ce] bg-transparent pl-9 text-sm placeholder:text-[#a39f98]"
            />
          </div>

          <Combobox data={sortOptions} type="sort" value={sortBy} onValueChange={(value) => setSortBy(value as SortBy)}>
            <ComboboxTrigger
              aria-label="Sort offers"
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
                    <ComboboxItem key={option.value} value={option.value} data-checked={sortBy === option.value} className={comboboxItemClass}>
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
              className={`h-9 min-w-[174px] rounded-[12px] border text-sm font-normal opacity-100 ${
                creatorFilter !== "all_creators"
                  ? activeFilterTriggerClass
                  : "border-[#d8d4ce] bg-transparent text-[#807b74] hover:border-[#bcb7b0] hover:bg-transparent aria-expanded:bg-transparent"
              }`}
            >
              <span className="flex w-full items-center justify-between gap-2">
                {creatorOptions.find((option) => option.value === creatorFilter)?.label ?? "All creators"}
                <ChevronsUpDownIcon
                  className={`size-4 shrink-0 ${creatorFilter !== "all_creators" ? "text-white" : "text-muted-foreground"}`}
                />
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
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4 xl:gap-3.5">
              {Array.from({ length: 12 }).map((_, index) => (
                <Card key={index} className="min-h-[220px] rounded-[14px] border border-[#d9d6d1] bg-[#f4f2ef] py-0 shadow-none ring-0">
                  <div className="flex h-full min-h-[220px] flex-col px-4 py-4">
                    <div className="flex items-start justify-between gap-3">
                      <Skeleton className="h-6 w-[62%] rounded-[8px]" />
                    </div>
                    <div className="mt-2 space-y-2">
                      <Skeleton className="h-4 w-[88%] rounded-[7px]" />
                      <Skeleton className="h-4 w-[72%] rounded-[7px]" />
                    </div>
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
        ) : filteredOffers.length === 0 ? (
          showNoOffersState ? (
            <div className="px-6 py-14 text-center">
              <p className="text-sm font-semibold text-primary">No offers yet</p>
              <p className="mt-1 text-sm text-[#6f6a63]">Create your first offer to get started.</p>
              <div className="mt-4 flex items-center justify-center">
                <Link
                  href="/offers/new"
                  className="inline-flex h-10 items-center rounded-[10px] border border-[#d8d4ce] bg-[#fff] px-4 text-sm font-semibold text-primary transition-colors hover:bg-[#f7f5f2]"
                >
                  Create new offer
                </Link>
              </div>
            </div>
          ) : (
            <div className="px-6 py-14 text-center">
              <button
                type="button"
                onClick={() => {
                  setQuery("");
                  setSortBy("last_edited");
                }}
                className="inline-flex h-10 items-center rounded-[10px] border border-[#f2b9a1] bg-[#fff7f3] px-4 text-sm font-medium text-[#a24a24] transition-colors hover:bg-[#ffefe8]"
              >
                Clear filters
              </button>
            </div>
          )
        ) : viewMode === "grid" ? (
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-4 xl:gap-3.5">
            <Link
              href="/offers/new"
              className="group block rounded-[10px] border-2 border-dashed border-[#c7c3bd] bg-transparent transition-colors hover:border-[#afa9a2] hover:bg-[#fff4ef]"
            >
              <Card className="h-full min-h-[220px] justify-center rounded-[10px] bg-transparent py-0 shadow-none ring-0">
                <Plus className="mx-auto h-8 w-8 text-[#d46a3a] transition-colors group-hover:text-[#c45523]" />
                <p className="text-center text-[18px] font-semibold tracking-[-0.02em] text-primary">Create new offer</p>
              </Card>
            </Link>

            {filteredOffers.map((offer) => (
              <Link key={offer.id} href={`/offers/${offer.id}`} className="group block">
                <Card className="min-h-[220px] rounded-[14px] border border-[#d9d6d1] bg-[#fff] py-0 shadow-none ring-0 transition-colors hover:border-[#cfcac3]">
                  <div className="flex h-full min-h-[220px] flex-col px-4 py-4">
                    <div className="flex items-start justify-between gap-3">
                      <p className="line-clamp-1 text-[18px] leading-tight font-semibold tracking-[-0.015em] text-primary">
                        {offer.name}
                      </p>
                      <Badge
                        variant="outline"
                        className={`h-7 shrink-0 rounded-pill px-3 text-xs font-semibold ${
                          (funnelCountByOffer[offer.id] ?? 0) > 0
                            ? "border-[#c8dcf5] bg-[#eaf4ff] text-[#3d6e9e]"
                            : "border-[#ddd9d3] bg-[#f8f7f5] text-[#7e7972]"
                        }`}
                      >
                        {funnelCountByOffer[offer.id] ?? 0} funnels
                      </Badge>
                    </div>
                    <p className="mt-1.5 line-clamp-2 text-[15px] leading-relaxed text-[#625e58]">
                      {offer.intake_data?.offer_one_liner || "-"}
                    </p>
                    <div className="mt-auto flex items-center justify-between pt-3 text-[13px] text-[#a19c95]">
                      <span>{offer.industry}</span>
                      <span>Edited {formatDate(offer.updated_at)}</span>
                    </div>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        ) : (
          <div className="overflow-hidden rounded-[14px] bg-transparent">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead className="h-16 px-4 text-sm font-semibold text-[#6f6a63]">Offer</TableHead>
                  <TableHead className="h-16 pl-10 text-sm font-semibold text-[#6f6a63]">Created</TableHead>
                  <TableHead className="h-16 px-4 text-right text-sm font-semibold text-[#6f6a63]">Industry</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow className="h-[66px] border-[#ebe8e3] hover:bg-[#f7f5f2]">
                  <TableCell className="px-4 py-4">
                    <Link href="/offers/new" className="inline-flex items-center gap-2 text-sm font-semibold text-primary hover:underline">
                      <Plus className="h-4 w-4 text-[#8f8a83]" />
                      Create new offer
                    </Link>
                  </TableCell>
                  <TableCell colSpan={2} className="py-4 text-right text-xs text-[#9b968f]">
                    Start from scratch
                  </TableCell>
                </TableRow>

                {filteredOffers.map((offer) => (
                  <TableRow key={offer.id} className="h-[66px] border-[#ebe8e3] hover:bg-[#f7f5f2]">
                    <TableCell className="px-4 py-4">
                      <Link href={`/offers/${offer.id}`} className="block">
                        <p className="font-semibold text-primary">{offer.name}</p>
                        <p className="line-clamp-1 text-xs text-[#7a756e]">Edited {formatDate(offer.updated_at)}</p>
                      </Link>
                    </TableCell>
                    <TableCell className="py-4 pl-10 text-[#4f4a44]">{formatDate(offer.created_at)}</TableCell>
                    <TableCell className="px-4 py-4 text-right text-[#4f4a44]">{offer.industry || "General"}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </section>
  );
}
