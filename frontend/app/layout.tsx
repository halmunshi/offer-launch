import { ClerkProvider } from "@clerk/nextjs";
import type { Metadata } from "next";
import { DM_Sans, Inter } from "next/font/google";
import "./globals.css";
import { cn } from "@/lib/utils";

const inter = Inter({subsets:['latin'],variable:'--font-sans'});

const dmSans = DM_Sans({
  variable: "--font-dm-sans",
  subsets: ["latin"],
  weight: ["400", "500", "600", "700", "800"],
});

export const metadata: Metadata = {
  title: "OfferLaunch - AI-Powered Funnel Builder",
  description:
    "OfferLaunch helps you generate and refine high-converting funnels with AI-powered copy and live builder workflows.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en" className={cn("h-full", "antialiased", dmSans.variable, "font-sans", inter.variable)}>
        <body className="min-h-full bg-page font-sans text-primary">{children}</body>
      </html>
    </ClerkProvider>
  );
}
