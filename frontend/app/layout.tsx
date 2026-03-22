import { ClerkProvider } from "@clerk/nextjs";
import { ui } from "@clerk/ui";
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "OfferLaunch",
  description: "OfferLaunch",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider ui={ui}>
      <html lang="en" className={`${inter.variable} h-full antialiased`}>
        <body className="min-h-full bg-[#0a0a0a] text-slate-50">{children}</body>
      </html>
    </ClerkProvider>
  );
}
