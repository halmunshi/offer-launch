"use client";

import { motion } from "framer-motion";
import { FileText, MonitorPlay, Rocket } from "lucide-react";
import Link from "next/link";

const container = {
  hidden: { opacity: 0 },
  show: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const item = {
  hidden: { opacity: 0, y: 20 },
  show: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.6,
      ease: [0.22, 1, 0.36, 1] as [number, number, number, number],
    },
  },
};

export default function MarketingHomePage() {
  return (
    <main className="min-h-screen bg-page text-primary">
      <div className="relative isolate overflow-hidden">
        <div
          className="pointer-events-none absolute inset-x-0 bottom-0 h-[60vh]"
          style={{
            backgroundImage:
              "url('/images/hero-mesh.png'), radial-gradient(ellipse 45% 70% at 25% 90%, rgba(242,101,34,0.55) 0%, rgba(245,185,80,0.3) 40%, transparent 70%), radial-gradient(ellipse 35% 60% at 50% 95%, rgba(167,139,250,0.45) 0%, rgba(124,58,237,0.2) 40%, transparent 70%), radial-gradient(ellipse 45% 70% at 75% 90%, rgba(124,58,237,0.5) 0%, rgba(91,33,182,0.3) 40%, transparent 70%)",
            backgroundPosition: "center bottom, center, center, center",
            backgroundRepeat: "no-repeat, no-repeat, no-repeat, no-repeat",
            backgroundSize: "cover, cover, cover, cover",
            maskImage: "linear-gradient(to top, black 70%, transparent 100%)",
          }}
        />

        <header className="relative z-10 mx-auto flex w-full max-w-[1120px] items-center justify-between px-6 py-6 md:px-10">
          <Link href="/" className="text-[18px] font-extrabold tracking-[-0.02em]">
            <span className="text-primary">Offer</span>
            <span className="text-[#f26522]">Launch</span>
          </Link>
          <Link href="/sign-in" className="text-sm font-semibold text-secondary hover:text-primary">
            Sign In
          </Link>
        </header>

        <motion.section
          variants={container}
          initial="hidden"
          animate="show"
          className="relative z-10 mx-auto flex w-full max-w-[1120px] flex-col gap-10 px-6 pb-24 pt-10 md:px-10 md:pt-16"
        >
          <div className="max-w-3xl space-y-6">
            <motion.h1 variants={item} className="text-4xl font-extrabold tracking-[-0.03em] md:text-6xl">
              Build your next high-converting funnel with AI.
            </motion.h1>
            <motion.p variants={item} className="max-w-2xl text-base text-secondary md:text-lg">
              OfferLaunch turns your offer details into production-ready funnel pages with persuasive copy,
              live preview updates, and one-click workflow generation.
            </motion.p>
            <motion.div variants={item} className="flex items-center gap-4">
              <Link
                href="/sign-up"
                className="inline-flex h-11 items-center rounded-button bg-orange px-5 text-sm font-semibold text-white transition hover:bg-[#d63500]"
              >
                Get Started Free
              </Link>
              <Link href="/sign-in" className="text-sm font-semibold text-secondary hover:text-primary">
                Sign In
              </Link>
            </motion.div>
          </div>

          <motion.div variants={container} className="grid gap-4 md:grid-cols-3">
            <motion.article variants={item} className="rounded-card border border-border bg-card p-5">
              <FileText className="mb-3 h-5 w-5 text-orange" />
              <h2 className="text-base font-bold">AI-Powered Copy</h2>
              <p className="mt-2 text-sm text-secondary">Generate message-market-fit copy tailored to your offer in minutes.</p>
            </motion.article>
            <motion.article variants={item} className="rounded-card border border-border bg-card p-5">
              <MonitorPlay className="mb-3 h-5 w-5 text-orange" />
              <h2 className="text-base font-bold">Live Preview Builder</h2>
              <p className="mt-2 text-sm text-secondary">Watch your funnel update live as pages and components are generated.</p>
            </motion.article>
            <motion.article variants={item} className="rounded-card border border-border bg-card p-5">
              <Rocket className="mb-3 h-5 w-5 text-orange" />
              <h2 className="text-base font-bold">One-Click Publish</h2>
              <p className="mt-2 text-sm text-secondary">Export complete project files and launch with your existing deployment flow.</p>
            </motion.article>
          </motion.div>
        </motion.section>
      </div>

      <footer className="border-t border-border py-6 text-center text-sm text-secondary">© 2026 OfferLaunch</footer>
    </main>
  );
}
