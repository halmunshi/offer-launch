"use client";

import { SignOutButton, useUser } from "@clerk/nextjs";
import { useEffect, useState } from "react";

import { api } from "@/lib/api";

export default function DashboardPage() {
  const { user } = useUser();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<unknown>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchHealth = async () => {
      try {
        const response = await api.get<Record<string, unknown>>("/health/detailed", null);
        if (isMounted) {
          setData(response);
        }
      } catch (fetchError) {
        if (isMounted) {
          setError(
            fetchError instanceof Error ? fetchError.message : "Failed to fetch health status",
          );
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    void fetchHealth();

    return () => {
      isMounted = false;
    };
  }, []);

  return (
    <section className="mx-auto flex min-h-screen w-full max-w-3xl flex-col gap-4 p-6">
      <h1 className="text-2xl font-semibold">Welcome to OfferLaunch</h1>
      <p className="text-slate-300">
        Signed in as: {user?.primaryEmailAddress?.emailAddress ?? "No email found"}
      </p>

      <SignOutButton redirectUrl="/sign-in">
        <button
          type="button"
          className="w-fit rounded-md border border-slate-700 px-4 py-2 text-sm hover:border-slate-500"
        >
          Sign out
        </button>
      </SignOutButton>

      <div className="mt-4 rounded-md border border-slate-800 bg-slate-950/50 p-4">
        <h2 className="mb-2 text-sm font-medium text-slate-200">Backend health diagnostic</h2>
        {loading ? <p>Loading health check...</p> : null}
        {error ? <p>Error: {error}</p> : null}
        {!loading && !error ? <pre>{JSON.stringify(data, null, 2)}</pre> : null}
      </div>
    </section>
  );
}
