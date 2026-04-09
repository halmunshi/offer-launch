import { SignIn } from "@clerk/nextjs";
import Link from "next/link";

export default function SignInPage() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-page p-6">
      <div className="flex w-full max-w-md flex-col items-center gap-5">
        <Link href="/" className="text-[18px] font-extrabold tracking-[-0.02em]">
          <span className="text-primary">Offer</span>
          <span className="text-[#f26522]">Launch</span>
        </Link>
        <SignIn
          forceRedirectUrl="/home"
          fallbackRedirectUrl="/home"
          signUpUrl="/sign-up"
          appearance={{
            variables: {
              colorBackground: "#faf9f7",
              colorPrimary: "#f53c00",
              colorForeground: "#1a1a1a",
              colorMutedForeground: "#57534e",
              colorInput: "#ffffff",
              colorInputForeground: "#1a1a1a",
              colorNeutral: "#e8e5e0",
              colorBorder: "#e8e5e0",
              fontFamily: "var(--font-dm-sans)",
              borderRadius: "12px",
            },
            elements: {
              card: "border border-border shadow-none",
              footerActionLink: "text-orange hover:text-[#d63500]",
              formButtonPrimary: "bg-orange hover:bg-[#d63500] text-white",
              socialButtonsBlockButton: "border-border bg-card text-primary hover:bg-surface",
              socialButtonsBlockButtonText: {
                color: "#1a1a1a",
              },
            },
          }}
        />
      </div>
    </main>
  );
}
