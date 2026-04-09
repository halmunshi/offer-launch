"use client";

import { useState } from "react";

import { NewFunnelModal } from "@/components/dashboard/NewFunnelModal";

export default function FunnelsPage() {
  const [isModalOpen, setIsModalOpen] = useState(false);

  return (
    <>
      <section className="animate-fade-up space-y-4">
        <header className="flex items-center justify-between gap-3">
          <div className="space-y-2">
            <h1 className="text-[28px] font-bold tracking-[-0.02em] text-primary">Funnels</h1>
            <p className="text-sm text-secondary">Funnel list and actions will be built in upcoming phases.</p>
          </div>
          <button
            type="button"
            onClick={() => setIsModalOpen(true)}
            className="inline-flex h-11 items-center rounded-button bg-orange px-5 text-sm font-semibold text-white transition-colors hover:bg-[#d63500]"
          >
            New funnel
          </button>
        </header>
      </section>

      <NewFunnelModal open={isModalOpen} onOpenChange={setIsModalOpen} />
    </>
  );
}
