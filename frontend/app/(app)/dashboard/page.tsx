"use client";

import { SignOutButton, useUser } from "@clerk/nextjs";

export default function DashboardPage() {
  const { user } = useUser();

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
    </section>
  );
}
