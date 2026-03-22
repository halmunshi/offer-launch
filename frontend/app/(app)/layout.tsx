export default function AppLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return <main className="min-h-screen bg-[#0a0a0a] text-slate-50">{children}</main>;
}
