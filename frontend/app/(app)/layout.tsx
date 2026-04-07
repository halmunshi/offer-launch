"use client";

import { SignOutButton, UserButton, useUser } from "@clerk/nextjs";
import { useAuth } from "@clerk/nextjs";
import {
  BarChart3,
  ChevronDown,
  Loader2,
  LayoutDashboard,
  Megaphone,
  Settings,
  Sparkles,
  Funnel
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { api } from "@/lib/api";

const ONBOARDING_CACHE_PREFIX = "offerlaunch:onboarding:";

type UserMeResponse = {
  id: string;
  full_name: string | null;
};

function NavItem({
  href,
  icon: Icon,
  label,
  active,
}: {
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  label: string;
  active: boolean;
}) {
  return (
    <Link
      href={href}
      className={`flex items-center gap-3 rounded-button px-3 py-2 text-sm font-medium transition-colors ${
        active
          ? "bg-selected text-orange ring-1 ring-orange/25"
          : "text-secondary hover:bg-surface hover:text-primary"
      }`}
    >
      <Icon className="h-4 w-4" />
      <span>{label}</span>
    </Link>
  );
}

export default function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const pathname = usePathname();
  const router = useRouter();
  const { getToken, userId, isLoaded } = useAuth();
  const { user } = useUser();
  const plan = typeof user?.publicMetadata?.plan === "string" ? user.publicMetadata.plan : "Free";
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isCheckingOnboarding, setIsCheckingOnboarding] = useState(true);
  const userMenuRef = useRef<HTMLDivElement | null>(null);
  const isOnboardingRoute = pathname === "/onboarding";

  useEffect(() => {
    function onDocumentMouseDown(event: MouseEvent) {
      if (!userMenuRef.current) {
        return;
      }

      if (!userMenuRef.current.contains(event.target as Node)) {
        setIsUserMenuOpen(false);
      }
    }

    document.addEventListener("mousedown", onDocumentMouseDown);
    return () => {
      document.removeEventListener("mousedown", onDocumentMouseDown);
    };
  }, []);

  useEffect(() => {
    let isCancelled = false;

    async function checkOnboarding() {
      if (!isLoaded) {
        return;
      }

      if (!userId) {
        if (!isCancelled) {
          setIsCheckingOnboarding(false);
        }
        return;
      }

      const storageKey = `${ONBOARDING_CACHE_PREFIX}${userId}`;
      const cached = sessionStorage.getItem(storageKey);

      if (cached === "complete") {
        if (!isCancelled) {
          setIsCheckingOnboarding(false);
          if (isOnboardingRoute) {
            router.replace("/dashboard");
          }
        }
        return;
      }

      if (cached === "incomplete") {
        if (!isCancelled) {
          setIsCheckingOnboarding(false);
          if (!isOnboardingRoute) {
            router.replace("/onboarding");
          }
        }
        return;
      }

      try {
        const token = await getToken();
        const me = await api.get<UserMeResponse>("/users/me", token);
        const hasName = typeof me.full_name === "string" && me.full_name.trim().length > 0;

        sessionStorage.setItem(storageKey, hasName ? "complete" : "incomplete");

        if (!isCancelled) {
          setIsCheckingOnboarding(false);
          if (hasName && isOnboardingRoute) {
            router.replace("/dashboard");
          }
          if (!hasName && !isOnboardingRoute) {
            router.replace("/onboarding");
          }
        }
      } catch {
        if (userId) {
          sessionStorage.setItem(storageKey, "incomplete");
        }
        if (!isCancelled) {
          setIsCheckingOnboarding(false);
          if (!isOnboardingRoute) {
            router.replace("/onboarding");
          }
        }
      }
    }

    void checkOnboarding();

    return () => {
      isCancelled = true;
    };
  }, [getToken, isLoaded, isOnboardingRoute, pathname, router, userId]);

  if (!isLoaded || isCheckingOnboarding) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-page text-secondary">
        <Loader2 className="h-5 w-5 animate-spin" />
      </div>
    );
  }

  if (isOnboardingRoute) {
    return <>{children}</>;
  }

  return (
    <div className="flex min-h-screen bg-page text-primary">
      <aside className="sticky top-0 flex h-screen w-[240px] shrink-0 flex-col border-r-[1.5px] border-border bg-card px-5 py-6">
        <Link href="/dashboard" className="mb-8 text-[18px] font-extrabold tracking-[-0.02em]">
          <span className="text-primary">Offer</span>
          <span className="text-[#f26522]">Launch</span>
        </Link>

        <nav className="space-y-1">
          <NavItem
            href="/dashboard"
            icon={LayoutDashboard}
            label="Dashboard"
            active={pathname === "/dashboard"}
          />
          <NavItem href="/offers" icon={Sparkles} label="Offers" active={pathname === "/offers"} />
          <NavItem href="/funnels" icon={Funnel} label="Funnels" active={pathname === "/funnels"} />
        </nav>

        <div className="my-6 border-t border-border" />

        <p className="mb-2 px-3 text-xs font-semibold uppercase tracking-[0.06em] text-muted">Coming soon</p>
        <div className="space-y-1">
          <div className="flex items-center gap-3 rounded-button px-3 py-2 text-sm text-muted">
            <Megaphone className="h-4 w-4" />
            <span>Campaigns</span>
          </div>
          <div className="flex items-center gap-3 rounded-button px-3 py-2 text-sm text-muted">
            <BarChart3 className="h-4 w-4" />
            <span>Analytics</span>
          </div>
        </div>

        <div className="mt-auto space-y-3">
          <NavItem href="/settings" icon={Settings} label="Settings" active={pathname === "/settings"} />

          <div ref={userMenuRef} className="relative">
            <button
              type="button"
              onClick={() => setIsUserMenuOpen((prev) => !prev)}
              className="flex w-full items-center justify-between rounded-card border border-border bg-surface px-3 py-2.5 text-left"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-semibold text-primary">
                  {user?.fullName ?? user?.firstName ?? "OfferLaunch User"}
                </p>
                <span className="inline-flex items-center rounded-pill bg-status-draft-bg px-2 py-0.5 text-[11px] font-semibold text-status-draft-text">
                  {String(plan)}
                </span>
              </div>
              <div className="flex items-center gap-1">
                <UserButton />
                <ChevronDown className="h-4 w-4 text-muted" />
              </div>
            </button>

            {isUserMenuOpen ? (
              <div className="absolute bottom-[calc(100%+8px)] left-0 right-0 z-20 rounded-input border border-border bg-card p-1 shadow-sm">
                <SignOutButton redirectUrl="/sign-in">
                  <button
                    type="button"
                    className="block w-full rounded-button px-3 py-2 text-left text-sm font-medium text-status-error-text transition-colors hover:bg-status-error-bg"
                    onClick={() => setIsUserMenuOpen(false)}
                  >
                    Sign out
                  </button>
                </SignOutButton>
              </div>
            ) : null}
          </div>
        </div>
      </aside>

      <main className="h-screen flex-1 overflow-y-auto bg-page">
        <div className="mx-auto w-full max-w-[960px] px-8 py-8 md:px-10">{children}</div>
      </main>
    </div>
  );
}
