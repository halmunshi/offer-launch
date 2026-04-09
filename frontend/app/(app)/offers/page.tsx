import Link from "next/link";

export default function OffersPage() {
  return (
    <section className="animate-fade-up space-y-4">
      <header className="flex items-center justify-between gap-3">
        <div className="space-y-2">
          <h1 className="text-[28px] font-bold tracking-[-0.02em] text-primary">Offers</h1>
          <p className="text-sm text-secondary">Offer management will be added in the next phase.</p>
        </div>
        <Link
          href="/offers/new"
          className="inline-flex h-11 items-center rounded-button bg-orange px-5 text-sm font-semibold text-white transition-colors hover:bg-[#d63500]"
        >
          New offer
        </Link>
      </header>
    </section>
  );
}
