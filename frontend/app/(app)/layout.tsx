"use client";

import { SignOutButton, useUser } from "@clerk/nextjs";
import { useAuth } from "@clerk/nextjs";
import {
  BarChart3,
  ChevronsUpDown,
  Loader2,
  House,
  Megaphone,
  Settings,
  Funnel,
  LayoutGrid
} from "lucide-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useRef, useState } from "react";

import { api } from "@/lib/api";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarInset,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarProvider,
  SidebarRail,
  SidebarSeparator,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";

type UserPlan = "free" | "standard" | "pro" | "agency";

type UserMeResponse = {
  id: string;
  full_name: string | null;
  plan: UserPlan;
};

function formatPlanLabel(plan: UserPlan | null): string {
  if (!plan) {
    return "Free";
  }

  return plan.charAt(0).toUpperCase() + plan.slice(1);
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
  const [userPlan, setUserPlan] = useState<UserPlan | null>(null);
  const planLabel = formatPlanLabel(userPlan);
  const userInitial = (user?.firstName ?? user?.fullName ?? "O").charAt(0).toUpperCase();
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false);
  const [isCheckingOnboarding, setIsCheckingOnboarding] = useState(true);
  const userMenuRef = useRef<HTMLDivElement | null>(null);
  const isOnboardingRoute = pathname === "/onboarding";
  const isOfferOnboardingRoute = pathname === "/offers/new";
  const isFunnelOnboardingRoute = pathname === "/funnels/new";
  const isFullCanvasOnboardingRoute = isOfferOnboardingRoute || isFunnelOnboardingRoute;

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

      try {
        const token = await getToken();
        const me = await api.get<UserMeResponse>("/users/me", token);
        const hasName = typeof me.full_name === "string" && me.full_name.trim().length > 0;

        if (!isCancelled) {
          setUserPlan(me.plan);
          setIsCheckingOnboarding(false);
          if (hasName && isOnboardingRoute) {
            router.replace("/home");
          }
          if (!hasName && !isOnboardingRoute) {
            router.replace("/onboarding");
          }
        }
      } catch {
        if (!isCancelled) {
          setUserPlan(null);
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
    <TooltipProvider>
      <SidebarProvider className="min-h-screen bg-page text-primary">
        <Sidebar collapsible="icon">
          <SidebarHeader>
            <div className="flex items-center gap-2 group-data-[collapsible=icon]:justify-center">
              <SidebarMenu className="min-w-0 group-data-[collapsible=icon]:hidden">
                <SidebarMenuItem>
                  <SidebarMenuButton asChild size="lg">
                    <Link href="/home" className="font-extrabold tracking-[-0.02em]">
                      <span className="text-[15px] text-primary">Offer</span>
                      <span className="text-[15px] text-[#f26522]">Launch</span>
                    </Link>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              </SidebarMenu>

              <SidebarTrigger className="ml-auto group-data-[collapsible=icon]:hidden" />
              <SidebarTrigger className="hidden group-data-[collapsible=icon]:inline-flex" />
            </div>
          </SidebarHeader>

          <SidebarContent>
            <SidebarGroup>
              <SidebarGroupLabel>Platform</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton asChild tooltip="Home" isActive={pathname === "/home" || pathname === "/dashboard"}>
                      <Link href="/home">
                        <House />
                        <span>Home</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>

                  <SidebarMenuItem>
                    <SidebarMenuButton asChild tooltip="Offers" isActive={pathname.startsWith("/offers")}>
                      <Link href="/offers">
                        <LayoutGrid />
                        <span>Offers</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>

                  <SidebarMenuItem>
                    <SidebarMenuButton asChild tooltip="Funnels" isActive={pathname === "/funnels"}>
                      <Link href="/funnels">
                        <Funnel />
                        <span>Funnels</span>
                      </Link>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>

            <SidebarSeparator />

            <SidebarGroup>
              <SidebarGroupLabel>Coming soon</SidebarGroupLabel>
              <SidebarGroupContent>
                <SidebarMenu>
                  <SidebarMenuItem>
                    <SidebarMenuButton disabled>
                      <Megaphone />
                      <span>Campaigns</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>

                  <SidebarMenuItem>
                    <SidebarMenuButton disabled>
                      <BarChart3 />
                      <span>Analytics</span>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                </SidebarMenu>
              </SidebarGroupContent>
            </SidebarGroup>
          </SidebarContent>

          <SidebarFooter>
            <SidebarMenu>
              <SidebarMenuItem>
                <SidebarMenuButton asChild isActive={pathname === "/settings"}>
                  <Link href="/settings">
                    <Settings />
                    <span>Settings</span>
                  </Link>
                </SidebarMenuButton>
              </SidebarMenuItem>

              <SidebarMenuItem className="relative">
                <div ref={userMenuRef} className="relative">
                  <SidebarMenuButton
                    size="lg"
                    onClick={() => setIsUserMenuOpen((prev) => !prev)}
                    className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
                  >
                    <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                      <span className="text-xs font-semibold">{userInitial}</span>
                    </div>
                    <div className="grid flex-1 text-left text-sm leading-tight group-data-[collapsible=icon]:hidden">
                      <span className="truncate font-medium">
                        {user?.fullName ?? user?.firstName ?? "OfferLaunch User"}
                      </span>
                      <span className="truncate text-xs text-muted">{planLabel}</span>
                    </div>
                    <ChevronsUpDown className="ml-auto size-4 group-data-[collapsible=icon]:hidden" />
                  </SidebarMenuButton>

                  {isUserMenuOpen ? (
                    <div className="absolute right-0 bottom-[calc(100%+8px)] z-20 min-w-40 rounded-input border border-border bg-card p-1 shadow-sm group-data-[collapsible=icon]:right-[calc(-100%-8px)]">
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
              </SidebarMenuItem>
            </SidebarMenu>
          </SidebarFooter>
          <SidebarRail />
        </Sidebar>

        <SidebarInset
          className={`h-screen bg-page ${isFullCanvasOnboardingRoute ? "overflow-hidden" : "overflow-y-auto [scrollbar-gutter:stable]"}`}
        >
          {isFullCanvasOnboardingRoute ? children : <div className="p-4 md:p-20">{children}</div>}
        </SidebarInset>
      </SidebarProvider>
    </TooltipProvider>
  );
}
